"""
bulk_loader.py
Script para carga histórica de dados mensais no Firebase Firestore.

Lê os arquivos Excel históricos, processa mês a mês usando a mesma lógica
ETL do app_mensal.py, e salva no Firestore.

Uso:
    python bulk_loader.py
"""
import os
import sys
import json
import glob
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import firebase_config
import data_loader

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "mensal")

FILE_OPTUM = os.path.join(DATA_DIR, "06 Histórico Extração Optum Tratada.xlsx")
# Busca dinâmica por todos os arquivos de controle de atendimentos
FILES_E = glob.glob(os.path.join(DATA_DIR, "*Controle de atendimentos*.xlsx"))

# Importar as funções auxiliares do app_mensal
dict_dia_semana = {0:"Seg", 1:"Ter", 2:"Qua", 3:"Qui", 4:"Sex", 5:"Sáb", 6:"Dom"}
dict_mes_abrev  = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
                   7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
dict_mes_full   = {1:'Janeiro',2:'Fevereiro',3:'Março',4:'Abril',5:'Maio',6:'Junho',
                   7:'Julho',8:'Agosto',9:'Setembro',10:'Outubro',11:'Novembro',12:'Dezembro'}

MAPA_NOMES = {
    'ANA LU SA R  SZAJUBOK':   'ANA LUÍSA R. SZAJUBOK',
    'C NTIA DOS SANTOS IRINEU':'CÍNTIA DOS SANTOS IRINEU',
    'CINTIA DOS SANTOS IRINEU':'CÍNTIA DOS SANTOS IRINEU',
}


def tratar_nomes_nutri(df, coluna='Nutri'):
    df = df.copy()
    df[coluna] = df[coluna].str.strip().str.upper().replace(MAPA_NOMES)
    return df


def label_semana(df):
    s    = df["Data"]
    mask = s.notna()
    m_ini = s.dt.to_period("M").dt.start_time
    m_fim = m_ini + pd.offsets.MonthEnd(0)
    week_mon   = s - pd.to_timedelta(s.dt.weekday, unit="D")
    week_sun   = week_mon + pd.Timedelta(days=6)
    week_start = week_mon.where(week_mon >= m_ini, m_ini)
    week_end   = week_sun.where(week_sun <= m_fim, m_fim)
    w0             = m_ini.dt.weekday
    week_in_month  = ((s.dt.day + w0 - 1) // 7 + 1).astype("Int64")
    label = pd.Series(pd.NA, index=s.index, dtype="string")
    label[mask] = (
        s[mask].dt.year.astype(str)
        + " - " + s[mask].dt.month.astype(str)
        + " " + s[mask].dt.month.map(dict_mes_abrev)
        + " - Sem " + week_in_month[mask].astype(str)
        + " - " + week_start[mask].dt.day.astype(str).str.zfill(2)
        + " a " + week_end[mask].dt.day.astype(str).str.zfill(2)
    )
    df = df.copy()
    df["Semana_mes"]   = week_in_month
    df["Semana_label"] = label
    return df


# ─────────────────────────────────────────────────────────────────────────────
# LEITURA DOS DADOS HISTÓRICOS
# ─────────────────────────────────────────────────────────────────────────────

def carregar_input_a_historico():
    """Lê a aba 'Oferta' do arquivo histórico e converte para o formato esperado."""
    print("  📄 Lendo Input A (Oferta)...")
    df = pd.read_excel(FILE_OPTUM, sheet_name='Oferta')

    out = pd.DataFrame()
    out['Data completa'] = df['Data completa'].copy()
    out["Data"] = out["Data completa"].str.split(" -").str[0]
    out["Data"] = pd.to_datetime(out["Data"], format="%d/%m/%Y", errors="coerce")
    out['Ano']     = out["Data"].dt.year
    out['Mês_num'] = out["Data"].dt.month
    out['Mês']     = out['Mês_num']
    out['DDS']     = df['DDS'].copy()

    # Converter horários
    out['Início'] = pd.to_datetime(df['Início'], format="%H:%M:%S", errors="coerce")
    out['Fim']    = pd.to_datetime(df['Fim'], format="%H:%M:%S", errors="coerce")
    out["Total horas"] = (out["Fim"] - out["Início"]).apply(
        lambda x: str(x).split(" days ")[-1] if pd.notnull(x) else None)
    out["Janelas"] = (out["Fim"] - out["Início"]).dt.total_seconds() / 3600
    out["Janelas"] = out["Janelas"].astype(int, errors='ignore')
    out["Início"]  = out["Início"].dt.time
    out["Fim"]     = out["Fim"].dt.time
    out['Nutri']   = df['Nutri'].str.strip().str.upper()
    out.drop(columns=['Mês_num'], inplace=True)
    out = label_semana(out)
    out['Mês'] = out['Data'].dt.month

    print(f"    ✅ {len(out)} linhas carregadas")
    return out


def carregar_input_d_historico():
    """Lê a aba 'Banco Optum tratado' do arquivo histórico."""
    print("  📄 Lendo Input D (Banco Optum tratado)...")
    df = pd.read_excel(FILE_OPTUM, sheet_name='Banco Optum tratado')

    # Mapear colunas do histórico para o formato esperado pelo ETL
    rename_map = {
        'ID caso':           'Número do caso',
        'Nome cliente':      'Beneficiário',
        'Empresa':           'Empresa',
        'Data inicial do caso': 'Data inicial do caso',
        'Status do caso':    'Status do caso',
        'Tipo medida tomada':'Tipo medida tomada',
        'Nutri':             'Nutri',
        'Data sessão':       'Data',
        'Tempo atendimento': 'Tempo atendimento',
        'Status atendimento':'Status sessão',
        'Valor atendimento': 'Valor Unitário',
    }

    df = df.rename(columns=rename_map)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = label_semana(df)
    df['Ano']  = df['Data'].dt.year
    df['Mês']  = df['Data'].dt.month
    df['Nutri'] = df['Nutri'].str.strip().str.upper()
    df = tratar_nomes_nutri(df, 'Nutri')

    print(f"    ✅ {len(df)} linhas carregadas")
    return df


def carregar_input_e_historico():
    """Lê todos os arquivos de controle de atendimentos encontrados."""
    print(f"  📄 Lendo Input E ({len(FILES_E)} arquivos encontrados)...")
    frames = []

    for filepath in FILES_E:
        nome = os.path.basename(filepath)
        try:
            df_head = pd.read_excel(filepath, skiprows=2, nrows=0,
                                     sheet_name='Controle atendimentos')
            cols_encontradas = df_head.columns.tolist()

            # Colunas esperadas
            COLUNAS_E = ['Data ', 'Nutri ', 'ID caso',
                         'Status atendimento \n(Realizado, Falta, Reagendou)']

            if all(c in cols_encontradas for c in COLUNAS_E):
                df = pd.read_excel(filepath, skiprows=2, usecols=COLUNAS_E,
                                    sheet_name='Controle atendimentos')
                df["Arquivo"] = nome
                frames.append(df)
                print(f"    ✅ {nome}: {len(df)} linhas")
            else:
                faltando = [c for c in COLUNAS_E if c not in cols_encontradas]
                print(f"    ⚠️ {nome}: Colunas faltando: {faltando}")
        except Exception as e:
            print(f"    ❌ {nome}: Erro: {e}")

    if not frames:
        print("    ⚠️ Nenhum arquivo E processado")
        return pd.DataFrame()

    df_all = pd.concat(frames, ignore_index=True)
    df_all = df_all[~df_all['Data '].isnull()].copy()
    df_all.rename(columns={'Data ': 'Data', 'Nutri ': 'Nutri'}, inplace=True)
    df_all["Data"] = pd.to_datetime(df_all["Data"], errors="coerce")
    df_all = label_semana(df_all)
    df_all['Ano']  = df_all['Data'].dt.year
    df_all['Mês']  = df_all['Data'].dt.month
    df_all['Nutri'] = df_all['Nutri'].str.strip().str.upper()
    df_all = tratar_nomes_nutri(df_all, 'Nutri')

    print(f"    ✅ Total E: {len(df_all)} linhas")
    return df_all


# ─────────────────────────────────────────────────────────────────────────────
# OUTPUTS (mesma lógica do app_mensal.py)
# ─────────────────────────────────────────────────────────────────────────────

def build_output_c(df_a, df_d):
    df_oferta = df_a.pivot_table(index='Semana_label', columns='Nutri', values='Janelas',
                                  aggfunc='sum', fill_value=0, dropna=False)
    df_oferta['TOTAL'] = df_oferta.sum(axis=1)
    df_oferta['CHECK'] = 'Oferta'

    df_ocup = df_d.pivot_table(index='Semana_label', columns='Nutri', values='Número do caso',
                                aggfunc='count', fill_value=0, dropna=False)
    df_ocup['TOTAL'] = df_ocup.sum(axis=1)
    df_ocup['CHECK'] = 'Ocupação'

    df_c = pd.concat([df_oferta, df_ocup])
    cols = list(df_c.columns)
    mid  = sorted([c for c in cols if c not in ['CHECK','TOTAL']])
    df_c = df_c[['CHECK'] + mid + ['TOTAL']]
    df_c = df_c.fillna(0)
    df_c[mid + ['TOTAL']] = df_c[mid + ['TOTAL']].astype(int)
    return df_c


def build_output_f(df_a, df_d, df_e):
    of = df_a.groupby(['Nutri','Ano','Mês'], as_index=False, dropna=False)['Janelas'].sum()
    of.rename(columns={'Janelas':'Oferta'}, inplace=True)

    oc = df_d.groupby(['Nutri','Ano','Mês'], as_index=False, dropna=False)['Número do caso'].count()
    oc.rename(columns={'Número do caso':'Ocupação'}, inplace=True)

    re_ = df_e.groupby(['Nutri','Ano','Mês'], as_index=False, dropna=False)['ID caso'].count()
    re_.rename(columns={'ID caso':'Realizado'}, inplace=True)

    df_f = of.merge(oc, on=['Nutri','Ano','Mês'], how='outer', validate='1:1')
    df_f = df_f.merge(re_, on=['Nutri','Ano','Mês'], how='outer', validate='1:1')
    df_f = df_f.fillna(0)
    df_f["% Ocupação"]  = (df_f["Ocupação"]  / df_f["Oferta"] ).replace([np.inf, np.nan], 0) * 100
    df_f["% Realizado"] = (df_f["Realizado"] / df_f["Ocupação"]).replace([np.inf, np.nan], 0) * 100

    cols_num = ['Oferta','Ocupação','Realizado']
    df_f = df_f[~(df_f[cols_num] == 0).all(axis=1)]
    df_f = df_f[~((df_f[['Ano','Mês']] == 0).all(axis=1) & (df_f[cols_num] > 0).any(axis=1))]
    df_f['Ano'] = df_f['Ano'].astype(int)
    df_f['Mês'] = df_f['Mês'].astype(int)
    df_f = df_f.sort_values(['Ano','Mês','Nutri'])
    return df_f


def build_output_g(df_d, df_e):
    df_g_raw = df_d.copy()

    # Garantir que a coluna 'Valor Unitário' existe e é numérica
    if 'Valor Unitário' not in df_g_raw.columns:
        df_g_raw['Valor Unitário'] = 0.0
    df_g_raw['Valor Unitário'] = (
        df_g_raw['Valor Unitário']
            .astype(str)
            .str.replace("R$", "", regex=False)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .str.strip()
    )
    df_g_raw['Valor Unitário'] = pd.to_numeric(df_g_raw['Valor Unitário'], errors='coerce').fillna(0)

    # Garantir que 'Status sessão' existe
    if 'Status sessão' not in df_g_raw.columns:
        df_g_raw['Status sessão'] = 'N/D'

    # Garantir que 'Número do caso' existe
    if 'Número do caso' not in df_g_raw.columns:
        df_g_raw['Número do caso'] = range(len(df_g_raw))

    try:
        df_g = df_g_raw.pivot_table(
            index=['Mês','Nutri'], columns='Status sessão',
            aggfunc={'Número do caso':'count','Valor Unitário':'sum'},
            fill_value=0, dropna=False
        )
    except Exception:
        # Fallback: apenas contagem por Status
        df_g = df_g_raw.pivot_table(
            index=['Mês','Nutri'], columns='Status sessão',
            aggfunc={'Número do caso':'count'},
            fill_value=0, dropna=False
        )
        df_g['Valor Unitário'] = 0

    df_g['Total Agendamentos'] = df_g['Número do caso'].sum(axis=1)
    df_g['Total Faturamento']  = df_g['Valor Unitário'].sum(axis=1) if 'Valor Unitário' in df_g.columns else 0

    if not df_e.empty:
        try:
            tb = df_e.groupby(['Mês','Nutri'], dropna=False, as_index=False)[['ID caso']].count()
            tb.rename(columns={'ID caso':'Planilhas'}, inplace=True)
            df_left = df_g[['Total Agendamentos']].reset_index()
            df_left.columns = ['Mês','Nutri','Total Agendamentos']
            tb = df_left.merge(tb, on=['Mês','Nutri'], how='left')
            tb['Check'] = tb['Total Agendamentos'] == tb['Planilhas']
            tb['Check'] = tb['Check'].map({False:'⚠️ Not OK', True:'✅ OK'})
            tb = tb.set_index(['Mês','Nutri'])
            df_g['Planilhas'] = df_g.index.map(tb['Planilhas'].to_dict())
            df_g['Check']     = df_g.index.map(tb['Check'].to_dict())
        except Exception:
            pass

    # Flatten colunas multi-level (ex: ('Número do caso', 'Realizado') -> 'Número do caso - Realizado')
    df_g.columns = [
        ' - '.join([str(c) for c in col]).strip(' - ')
        if isinstance(col, tuple) else str(col)
        for col in df_g.columns
    ]
    # Reset index para que Mês/Nutri virem colunas normais
    df_g = df_g.reset_index()

    return df_g


# ─────────────────────────────────────────────────────────────────────────────
# CARGA HISTÓRICA
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("🔥 CARGA HISTÓRICA — Firebase Firestore")
    print("=" * 60)

    # 1. Verificar arquivos
    if not os.path.exists(FILE_OPTUM):
        print(f"❌ Arquivo Optum não encontrado: {FILE_OPTUM}")
        return
    if not FILES_E:
        print(f"⚠️ Nenhum arquivo de controle (Input E) encontrado em {DATA_DIR}")
    else:
        print(f"✅ Arquivo Optum encontrado")
        print(f"✅ {len(FILES_E)} arquivos de controle encontrados")

    # 2. Conexão Firebase
    print("🔌 Conectando ao Firebase...")
    db = firebase_config.db
    if not db:
        print("❌ Falha na conexão com Firebase")
        return
    print("✅ Conectado ao Firestore\n")

    # 3. Carregar todos os dados
    print("📊 Carregando dados históricos...")
    df_a = carregar_input_a_historico()
    df_d = carregar_input_d_historico()
    df_e = carregar_input_e_historico()

    # 4. Identificar períodos únicos (baseado em Input A como referência)
    periodos_a = df_a.dropna(subset=['Ano','Mês']).groupby(['Ano','Mês']).size().reset_index()
    periodos_a.columns = ['Ano','Mês','qtd']
    periodos_a = periodos_a.sort_values(['Ano','Mês'])

    print(f"\n📋 Períodos encontrados no Input A: {len(periodos_a)}")
    for _, r in periodos_a.iterrows():
        print(f"  {dict_mes_abrev[int(r['Mês'])]}/{int(r['Ano'])} ({int(r['qtd'])} registros oferta)")

    # 5. Verificar períodos já existentes
    periodos_existentes = data_loader.listar_periodos(db)
    periodos_existentes_set = {(p['ano'], p['mes']) for p in periodos_existentes}
    if periodos_existentes_set:
        print(f"\n⚠️ Períodos já no banco: {len(periodos_existentes_set)}")
        for ano, mes in sorted(periodos_existentes_set):
            print(f"  {dict_mes_abrev[mes]}/{ano}")

    # 6. Confirmar
    print(f"\n{'='*60}")
    resp = input("Deseja prosseguir com a carga? (s/n): ").strip().lower()
    if resp != 's':
        print("Carga cancelada.")
        return

    # Perguntar se deseja sobrescrever existentes
    sobrescrever = False
    if periodos_existentes_set:
        resp2 = input("Sobrescrever períodos que já existem? (s/n): ").strip().lower()
        sobrescrever = resp2 == 's'

    # 7. Processar e salvar mês a mês
    print(f"\n🚀 Iniciando carga...")
    total_ok = 0
    total_skip = 0
    total_erro = 0

    # Auditoria
    inicio_execucao = datetime.now()
    log_periodos = []

    for _, r in periodos_a.iterrows():
        ano = int(r['Ano'])
        mes = int(r['Mês'])
        label = f"{dict_mes_abrev[mes]}/{ano}"

        # Verificar se já existe
        if (ano, mes) in periodos_existentes_set and not sobrescrever:
            print(f"  ⏭️ {label} — já existe, pulando")
            total_skip += 1
            log_periodos.append({
                'periodo': label, 'ano': ano, 'mes': mes,
                'status': 'pulado', 'motivo': 'já existe no banco',
            })
            continue

        print(f"\n  🔄 Processando {label}...")

        try:
            # Filtrar dados do mês
            df_a_mes = df_a[(df_a['Data'].dt.year == ano) & (df_a['Data'].dt.month == mes)].copy()
            df_d_mes = df_d[(df_d['Data'].dt.year == ano) & (df_d['Data'].dt.month == mes)].copy()
            df_e_mes = df_e[(df_e['Data'].dt.year == ano) & (df_e['Data'].dt.month == mes)].copy() if not df_e.empty else pd.DataFrame()

            print(f"     A: {len(df_a_mes)} | D: {len(df_d_mes)} | E: {len(df_e_mes)}")

            # Build outputs
            df_c = build_output_c(df_a_mes, df_d_mes) if len(df_a_mes) > 0 and len(df_d_mes) > 0 else pd.DataFrame()
            df_f = build_output_f(df_a_mes, df_d_mes, df_e_mes) if len(df_a_mes) > 0 else pd.DataFrame()
            df_g = build_output_g(df_d_mes, df_e_mes) if len(df_d_mes) > 0 else None

            # Extrair valor consulta do input D (se disponível)
            valor_consulta = 0
            col_valor = next((c for c in df_d_mes.columns if c in ('Valor Unitário', 'Valor atendimento')), None)
            if col_valor:
                vals = (
                    df_d_mes[col_valor]
                    .astype(str)
                    .str.replace("R$", "", regex=False)
                    .str.replace(".", "", regex=False)
                    .str.replace(",", ".", regex=False)
                    .str.strip()
                )
                vals = pd.to_numeric(vals, errors='coerce').dropna()
                vals = vals[vals > 0]
                if not vals.empty:
                    valor_consulta = float(vals.mode().iloc[0]) if not vals.mode().empty else float(vals.median())

            # Preparar dados para salvar (apenas DataFrames, sem 'meta')
            dados = {
                'input_a': df_a_mes,
                'input_d': df_d_mes,
                'input_e': df_e_mes if not df_e_mes.empty else pd.DataFrame(),
                'output_c': df_c,
                'output_f': df_f,
                'output_g': df_g if df_g is not None else pd.DataFrame(),
            }

            # Salvar no Firestore (meta é passada como kwargs separados)
            data_loader.salvar_dados_mensal(
                db, ano, mes, dados,
                custo_nutri_mes=0.0,
                impostos=0.0,
                valor_consulta=valor_consulta,
            )
            print(f"     ✅ {label} salvo com sucesso!")
            total_ok += 1
            log_periodos.append({
                'periodo': label, 'ano': ano, 'mes': mes,
                'status': 'ok',
                'linhas_a': len(df_a_mes),
                'linhas_d': len(df_d_mes),
                'linhas_e': len(df_e_mes),
                'valor_consulta': valor_consulta,
                'sobrescreveu': (ano, mes) in periodos_existentes_set,
            })

        except Exception as e:
            print(f"     ❌ Erro em {label}: {e}")
            import traceback
            traceback.print_exc()
            total_erro += 1
            log_periodos.append({
                'periodo': label, 'ano': ano, 'mes': mes,
                'status': 'erro', 'motivo': str(e),
            })

    # 8. Resumo
    print(f"\n{'='*60}")
    print(f"📊 RESUMO DA CARGA HISTÓRICA")
    print(f"{'='*60}")
    print(f"  ✅ Salvos com sucesso: {total_ok}")
    print(f"  ⏭️ Pulados (já existentes): {total_skip}")
    print(f"  ❌ Erros: {total_erro}")
    print(f"{'='*60}")

    # 9. Salvar log de auditoria
    log_dir = os.path.join(os.path.dirname(__file__), 'logs', 'carga')
    os.makedirs(log_dir, exist_ok=True)
    ts = inicio_execucao.strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(log_dir, f'bulk_load_{ts}.json')
    log_data = {
        'execucao': inicio_execucao.isoformat(),
        'duracao_segundos': round((datetime.now() - inicio_execucao).total_seconds(), 1),
        'operador': os.getenv('USERNAME', os.getenv('USER', 'desconhecido')),
        'fontes': {
            'optum': FILE_OPTUM,
            'controles': [os.path.basename(f) for f in FILES_E],
        },
        'sobrescreveu': sobrescrever,
        'resumo': {
            'total_ok': total_ok,
            'total_pulados': total_skip,
            'total_erros': total_erro,
        },
        'periodos': log_periodos,
    }
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    print(f"\n📝 Log de auditoria salvo em: {log_path}")


if __name__ == "__main__":
    main()
