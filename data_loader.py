"""
data_loader.py
Funções para ler e gravar dados do Firestore para o dashboard mensal.

Estrutura Firestore:
  Collection: periodos_mensal
    Document: "2025_03" (YYYY_MM)
      Fields: { ano, mes, data_upload, custo_nutri_mes, impostos, valor_consulta }
      Sub-collection: dados
        Documents: input_a, input_d, input_e, output_c, output_f, output_g
          → { records: [...], total_parts: N }
          (se > 800 KB, dividido em input_a_part2, input_a_part3, etc.)
"""
import math
import json
from datetime import datetime
from typing import Optional

import pandas as pd
import numpy as np
from google.cloud.firestore_v1 import DocumentReference

# Limite seguro por documento (~800 KB para margem)
MAX_DOC_BYTES = 800_000

COLLECTION = "periodos_mensal"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _periodo_id(ano: int, mes: int) -> str:
    return f"{int(ano)}_{int(mes):02d}"


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Converte DataFrame em lista de dicts serializável para Firestore."""
    import datetime as dt
    if df is None or df.empty:
        return []
    df_clean = df.copy()

    # Reset index se tiver MultiIndex ou Index com nome (ex: Output C)
    if df_clean.index.name or isinstance(df_clean.index, pd.MultiIndex):
        df_clean = df_clean.reset_index()

    for col in df_clean.columns:
        if pd.api.types.is_datetime64_any_dtype(df_clean[col]):
            df_clean[col] = df_clean[col].dt.strftime("%Y-%m-%d %H:%M:%S")
        elif df_clean[col].dtype == "timedelta64[ns]":
            df_clean[col] = df_clean[col].astype(str)
        else:
            # Converter valores individuais problemáticos
            df_clean[col] = df_clean[col].apply(lambda x: (
                x.isoformat() if isinstance(x, (dt.time, dt.date, dt.datetime)) else
                str(x)        if isinstance(x, pd.Period) else
                None          if isinstance(x, float) and np.isnan(x) else
                None          if x is pd.NA or x is pd.NaT else
                x
            ))

    # Substituir NaN/NaT por None
    df_clean = df_clean.where(df_clean.notna(), None)

    # Converter tipos numpy para nativos Python
    records = df_clean.to_dict(orient="records")
    for rec in records:
        for k, v in rec.items():
            if isinstance(v, (np.integer,)):
                rec[k] = int(v)
            elif isinstance(v, (np.floating,)):
                rec[k] = None if np.isnan(v) else float(v)
            elif isinstance(v, np.bool_):
                rec[k] = bool(v)
            elif isinstance(v, (dt.time, dt.date, dt.datetime)):
                rec[k] = v.isoformat()
            elif isinstance(v, pd.Period):
                rec[k] = str(v)
    return records


def _records_to_df(records: list[dict]) -> pd.DataFrame:
    """Reconstrói DataFrame a partir de records do Firestore."""
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


def _estimar_tamanho_json(records: list[dict]) -> int:
    """Estima tamanho em bytes do JSON dos records."""
    return len(json.dumps(records, default=str).encode("utf-8"))


# ─── Listagem e verificação ──────────────────────────────────────────────────

def listar_periodos(db) -> list[dict]:
    """
    Retorna lista de periodos disponíveis no Firestore.
    Cada item: { 'ano': int, 'mes': int, 'data_upload': str, 'id': str }
    """
    docs = db.collection(COLLECTION).stream()
    periodos = []
    for doc in docs:
        data = doc.to_dict()
        periodos.append({
            "id": doc.id,
            "ano": data.get("ano"),
            "mes": data.get("mes"),
            "data_upload": data.get("data_upload"),
        })
    periodos.sort(key=lambda x: (x["ano"] or 0, x["mes"] or 0))
    return periodos


def verificar_periodo_existe(db, ano: int, mes: int) -> bool:
    """Verifica se já existe dados para o período informado."""
    doc_id = _periodo_id(ano, mes)
    doc = db.collection(COLLECTION).document(doc_id).get()
    return doc.exists


# ─── Salvamento ──────────────────────────────────────────────────────────────

def _salvar_dataframe(db, periodo_ref: DocumentReference, nome: str, df: pd.DataFrame):
    """Salva um DataFrame no Firestore, dividindo em parts se necessário."""
    records = _df_to_records(df)
    if not records:
        periodo_ref.collection("dados").document(nome).set({
            "records": [],
            "total_parts": 1,
        })
        return

    tamanho = _estimar_tamanho_json(records)
    if tamanho <= MAX_DOC_BYTES:
        periodo_ref.collection("dados").document(nome).set({
            "records": records,
            "total_parts": 1,
        })
    else:
        # Dividir em chunks
        n_parts = math.ceil(tamanho / MAX_DOC_BYTES)
        chunk_size = math.ceil(len(records) / n_parts)
        for i in range(n_parts):
            chunk = records[i * chunk_size : (i + 1) * chunk_size]
            part_name = nome if i == 0 else f"{nome}_part{i + 1}"
            periodo_ref.collection("dados").document(part_name).set({
                "records": chunk,
                "total_parts": n_parts,
                "part": i + 1,
            })


def salvar_dados_mensal(
    db,
    ano: int,
    mes: int,
    dados: dict[str, pd.DataFrame],
    custo_nutri_mes: float = 0.0,
    impostos: float = 0.0,
    valor_consulta: float = 0.0,
):
    """
    Salva todos os DataFrames de um período no Firestore.

    Args:
        db: Firestore client
        ano, mes: competência
        dados: dict com chaves 'input_a', 'input_d', 'input_e',
               'output_c', 'output_f', 'output_g' → DataFrames
        custo_nutri_mes, impostos, valor_consulta: parâmetros financeiros
    """
    doc_id = _periodo_id(ano, mes)
    periodo_ref = db.collection(COLLECTION).document(doc_id)

    # Metadados do período
    periodo_ref.set({
        "ano": int(ano),
        "mes": int(mes),
        "data_upload": datetime.now().isoformat(),
        "custo_nutri_mes": float(custo_nutri_mes),
        "impostos": float(impostos),
        "valor_consulta": float(valor_consulta),
    })

    # Salvar cada DataFrame
    for nome, df in dados.items():
        _salvar_dataframe(db, periodo_ref, nome, df)


# ─── Carregamento ────────────────────────────────────────────────────────────

def _carregar_dataframe(db, periodo_ref: DocumentReference, nome: str) -> pd.DataFrame:
    """Carrega um DataFrame do Firestore, reunindo parts se necessário."""
    doc = periodo_ref.collection("dados").document(nome).get()
    if not doc.exists:
        return pd.DataFrame()

    data = doc.to_dict()
    total_parts = data.get("total_parts", 1)
    records = data.get("records", [])

    if total_parts > 1:
        for i in range(2, total_parts + 1):
            part_doc = periodo_ref.collection("dados").document(f"{nome}_part{i}").get()
            if part_doc.exists:
                records.extend(part_doc.to_dict().get("records", []))

    return _records_to_df(records)


def carregar_dados_mensal(db, ano: int, mes: int) -> Optional[dict]:
    """
    Carrega todos os dados de um período do Firestore.

    Retorna dict com:
        - 'meta': { ano, mes, data_upload, custo_nutri_mes, impostos, valor_consulta }
        - 'input_a', 'input_d', 'input_e': DataFrames dos inputs processados
        - 'output_c', 'output_f', 'output_g': DataFrames dos outputs
    Ou None se o período não existir.
    """
    doc_id = _periodo_id(ano, mes)
    periodo_ref = db.collection(COLLECTION).document(doc_id)
    meta_doc = periodo_ref.get()

    if not meta_doc.exists:
        return None

    resultado = {"meta": meta_doc.to_dict()}

    nomes = ["input_a", "input_d", "input_e", "output_c", "output_f", "output_g"]
    for nome in nomes:
        resultado[nome] = _carregar_dataframe(db, periodo_ref, nome)

    return resultado


# ─── Exclusão ─────────────────────────────────────────────────────────────────

def excluir_periodo(db, ano: int, mes: int):
    """Remove um período inteiro do Firestore (documento + sub-collections)."""
    doc_id = _periodo_id(ano, mes)
    periodo_ref = db.collection(COLLECTION).document(doc_id)

    # Remover sub-collection 'dados'
    dados_docs = periodo_ref.collection("dados").stream()
    for doc in dados_docs:
        doc.reference.delete()

    # Remover documento principal
    periodo_ref.delete()
