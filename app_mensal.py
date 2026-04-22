import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import io
import re
from PIL import Image
import data_loader

# Configuração da página
logo_icon = Image.open("images/flua-logo.png")
st.set_page_config(
    page_title="Dashboard Mensal - Flua Nutrição",
    page_icon=logo_icon,
    layout="wide"
)

st.markdown("""
<style>
    body, .stApp {
        background-color: #f8f9fa;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #044851;
        padding: 1rem 0;
        display: flex;
        align-items: center;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #463e8c;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #E7F7FA;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 6px solid #66cbdd;
        margin: 1rem 0;
        color: #044851;
    }
    .success-box {
        background-color: #e8f7ef;
        padding: 1rem;
        border-radius: 8px;
        border-left: 6px solid #c3d76b;
        color: #044851;
    }
    .warning-box {
        background-color: #fff8e0;
        padding: 1rem;
        border-radius: 8px;
        border-left: 6px solid #fcc105;
        color: #8a6d00;
    }
    .error-box {
        background-color: #fde8e8;
        padding: 1rem;
        border-radius: 8px;
        border-left: 6px solid #eb4524;
        color: #7a1515;
    }
    .kpi-wrapper {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        justify-content: center;
        margin: 1.5rem 0;
    }
    .kpi-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 1.5rem 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        text-align: center;
        min-width: 160px;
        flex: 1 1 180px;
        max-width: 220px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(0,0,0,0.03);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 5px;
        background: var(--card-color, #aab7b8);
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.1);
        border-color: var(--card-color, #aab7b8);
    }
    .kpi-icon {
        font-size: 1.8rem;
        margin-bottom: 0.5rem;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
    }
    .kpi-label {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #7f8c8d;
        margin-bottom: 0.8rem;
        height: 2.2em;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .kpi-value {
        font-size: clamp(1.4rem, 2.5vw, 1.8rem);
        font-weight: 800;
        color: #044851;
        line-height: 1.1;
        margin-bottom: 0.5rem;
        white-space: nowrap;
    }
    .kpi-value .currency {
        font-size: 0.6em;
        font-weight: 600;
        margin-right: 0.1rem;
        color: #7f8c8d;
    }
    .kpi-delta-pos { font-size: 0.85rem; font-weight: 700; color: #27ae60; background: #e8f7ef; padding: 2px 8px; border-radius: 12px; }
    .kpi-delta-neg { font-size: 0.85rem; font-weight: 700; color: #eb4524; background: #fde8e8; padding: 2px 8px; border-radius: 12px; }
    .kpi-delta-neu { font-size: 0.85rem; font-weight: 700; color: #7f8c8d; }

    /* Estilização dos botões de download (Excel) */
    .stDownloadButton button {
        background-color: #ffffff !important;
        color: #1d6f42 !important;
        border: 2px solid #1d6f42 !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        width: 100% !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .stDownloadButton button:hover {
        background-color: #1d6f42 !important;
        color: #ffffff !important;
        box-shadow: 0 8px 15px rgba(29, 111, 66, 0.2) !important;
        transform: translateY(-2px) !important;
    }

    /* Estilização dos Botões */
    .stButton button {
        background-color: #f8f9fa !important;
        color: #7f8c8d !important;
        border: 1px solid #dcdde1 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    .stButton button:hover {
        border-color: #044851 !important;
        color: #044851 !important;
        background-color: #ffffff !important;
    }

    /* Stepper Styling */
    .stepper-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        border: 1px solid #edf2f7;
    }
    .step {
        display: flex;
        align-items: center;
        font-weight: 600;
        color: #aab7b8;
    }
    .step.active {
        color: #044851;
    }
    .step-number {
        display: inline-flex;
        justify-content: center;
        align-items: center;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #edf2f7;
        margin-right: 8px;
        font-size: 1rem;
    }
    .step.active .step-number {
        background: #044851;
        color: #ffffff;
    }
    .step-divider {
        height: 2px;
        width: 60px;
        background: #edf2f7;
        margin: 0 15px;
    }
    .step-divider.active {
        background: #044851;
    }
    
    /* Upload Cards */
    .upload-card {
        background: #ffffff;
        border: 1px solid #edf2f7;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        border-left: 5px solid #044851;
    }
    .upload-card:hover {
        border-color: #66cbdd;
        box-shadow: 0 4px 10px rgba(102, 203, 221, 0.1);
        transform: translateY(-2px);
    }
    .upload-card h4 {
        margin-top: 0;
        color: #044851;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÕES ETL
# ─────────────────────────────────────────────────────────────────────────────

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


def tratar_nomes_nutri(df, coluna='Nutri'):
    df = df.copy()
    df[coluna] = df[coluna].str.strip().str.upper().replace(MAPA_NOMES)
    return df


def extract_sort_key(label):
    m = re.search(r'^(\d+)\s+-\s+(\d+)\s+\w+\s+-\s+Sem\s+(\d+)', str(label))
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return (0, 0, 0)


# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÕES DE HIGIENIZAÇÃO / HELPER
# ─────────────────────────────────────────────────────────────────────────────

def safe_to_numeric(val):
    """Converte valores monetários (R$ 84,00) ou numéricos (84.0) para float de forma segura."""
    if pd.isna(val) or val == "":
        return 0.0
    if isinstance(val, (int, float, np.number)):
        return float(val)
    
    s = str(val).replace("R$", "").strip()
    if not s:
        return 0.0
    
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    
    try:
        return float(s)
    except ValueError:
        return 0.0


# ─── Input A: Disponibilidade Optum ──────────────────────────────────────────
def processar_input_a(file_obj):
    df = pd.read_excel(file_obj)
    # Higienizar colunas conforme regra do GEMINI.md
    df.columns = df.columns.astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()

    out = pd.DataFrame(columns=['Data completa','Ano','Mês','Mês_Ano','DDS','Início','Fim','Total horas','Janelas','Nutri'])
    
    # Identificação flexível de colunas (Suporta formato Tratado e Raw)
    col_data  = next((c for c in df.columns if c in ['Data completa', 'HORA INICIAL']), None)
    col_inicio = next((c for c in df.columns if c in ['Início', 'HORA FINAL']), None)
    col_fim    = next((c for c in df.columns if c in ['Fim', 'HORAS TOTAIS']), None)
    col_total  = next((c for c in df.columns if c in ['Total horas', 'Duração']), None)
    col_nutri  = next((c for c in df.columns if c in ['Nutri', 'Responsável']), None)
    if not col_nutri and 'Unnamed: 6' in df.columns: col_nutri = 'Unnamed: 6'

    if col_data:
        out['Data completa'] = df[col_data].astype(str).copy()
        out["Data"] = out["Data completa"].str.split(" -").str[0]
        out["Data"] = pd.to_datetime(out["Data"], format="%d/%m/%Y", errors="coerce")
        out['Ano']     = out["Data"].dt.year
        out['Mês_num'] = out["Data"].dt.month
        out['Mês']     = out['Mês_num'].map(dict_mes_full)
        out['Mês_Ano'] = out['Mês'].astype(str) + " " + out['Ano'].astype(str)
        if 'DDS' in df.columns: out['DDS'] = df['DDS']
        else: out['DDS'] = out['Data completa'].str[-3:]

    # Cálculo de Janelas priorizando coluna de Total horas (ground truth)
    if col_total:
        total_td = pd.to_timedelta(df[col_total].astype(str), errors='coerce')
        out["Janelas"] = total_td.dt.total_seconds() / 3600
        out["Total horas"] = df[col_total].astype(str)
    elif col_inicio and col_fim:
        ini = pd.to_datetime(df[col_inicio], format="%H:%M:%S", errors="coerce")
        fim = pd.to_datetime(df[col_fim], format="%H:%M:%S", errors="coerce")
        out["Janelas"] = (fim - ini).dt.total_seconds() / 3600
        out["Total horas"] = (fim - ini).apply(lambda x: str(x).split(" days ")[-1] if pd.notnull(x) else None)

    if col_inicio:
        out['Início'] = pd.to_datetime(df[col_inicio], format="%H:%M:%S", errors="coerce").dt.time
    if col_fim:
        out['Fim'] = pd.to_datetime(df[col_fim], format="%H:%M:%S", errors="coerce").dt.time
    
    if col_nutri:
        out['Nutri'] = df[col_nutri].astype(str).str.strip().str.upper()

    if 'Mês_num' in out.columns: out.drop(columns=['Mês_num'], inplace=True)
    out = label_semana(out)
    out['Mês'] = out['Data'].dt.month
    return out


# ─── Input D: Relatório de sessões Optum (vários arquivos) ───────────────────
COLS_D = ['Número do caso','Beneficiário','Empresa','Data inicial do caso',
          'Status do caso','Tipo medida tomada','Responsável','Data sessão',
          'Tempo atendimento','Status sessão','Valor Unitário']

def processar_input_d(file_objs):
    frames, logs = [], []
    for f in file_objs:
        nome = f.name
        try:
            # Lemos a primeira linha para identificar as colunas presentes
            df_cols = pd.read_excel(f, nrows=0)
            
            # Criamos um mapa para os nomes originais (que serão lidos no usecols) 
            # retirando eventuais espaços extras do cabeçalho
            orig_columns = list(df_cols.columns)
            stripped_columns = [str(c).strip() for c in orig_columns]
            
            cols_found = stripped_columns

            # Mapeamento do "Banco Optum tratado" para o formato esperado pelo app_mensal
            rename_map = {
                'ID caso':           'Número do caso',
                'Nome cliente':      'Beneficiário',
                'Empresa':           'Empresa',
                'Data inicial do caso': 'Data inicial do caso',
                'Status do caso':    'Status do caso',
                'Tipo medida tomada':'Tipo medida tomada',
                'Nutri':             'Responsável',
                'Data sessão':       'Data sessão', # mantemos este por enquanto (depois vira Data)
                'Tempo atendimento': 'Tempo atendimento',
                'Status atendimento':'Status sessão',
                'Valor atendimento': 'Valor Unitário',
            }

            usecols_orig = []
            final_renames = {}
            for target_col in COLS_D:
                if target_col in cols_found:
                    idx = cols_found.index(target_col)
                    usecols_orig.append(orig_columns[idx])
                    final_renames[orig_columns[idx]] = target_col
                else:
                    possible_sources = [k for k, v in rename_map.items() if v == target_col]
                    for src in possible_sources:
                        if src in cols_found:
                            idx = cols_found.index(src)
                            usecols_orig.append(orig_columns[idx])
                            final_renames[orig_columns[idx]] = target_col
                            break
            
            # Pandas aceita a lista exata dos nomes sem strip
            df = pd.read_excel(f, usecols=usecols_orig)
            df = df.rename(columns=final_renames)
            
            # Garantir que todas as colunas de COLS_D pelo menos existam (como NaN se faltar) 
            # para evitar KeyError na frente
            for c in COLS_D:
                if c not in df.columns:
                    df[c] = None
            
            frames.append(df)
            logs.append(("OK", nome, ""))
        except Exception as e:
            logs.append(("ERRO", nome, str(e)))

    if not frames:
        return pd.DataFrame(), logs

    df_all = pd.concat(frames, ignore_index=True)
    df_all.rename(columns={'Data sessão':'Data','Responsável':'Nutri'}, inplace=True)
    df_all["Data"] = pd.to_datetime(df_all["Data"], format="%d/%m/%Y", errors="coerce")
    df_all = label_semana(df_all)
    df_all['Ano'] = df_all['Data'].dt.year
    df_all['Mês'] = df_all['Data'].dt.month
    df_all['Nutri'] = df_all['Nutri'].astype(str).str.strip().str.upper()
    df_all = tratar_nomes_nutri(df_all, 'Nutri')
    return df_all, logs


# ─── Input E: Controles individuais de atendimento (vários arquivos) ─────────
COLUNAS_E = ['Data ', 'Nutri ', 'ID caso', 'Status atendimento \n(Realizado, Falta, Reagendou)']

def processar_input_e(file_objs):
    frames, logs = [], []
    for f in file_objs:
        nome = f.name
        try:
            df_head = pd.read_excel(f, skiprows=2, nrows=0, sheet_name='Controle atendimentos')
            cols_encontradas = df_head.columns.tolist()
            if all(c in cols_encontradas for c in COLUNAS_E):
                
                # Se o usuário também inserir o Valor atendimento nessa aba, vamos pegar
                cols_to_use = COLUNAS_E.copy()
                if 'Valor atendimento' in cols_encontradas:
                    cols_to_use.append('Valor atendimento')
                elif 'Valor Unitário' in cols_encontradas:
                    cols_to_use.append('Valor Unitário')
                    
                df = pd.read_excel(f, skiprows=2, usecols=cols_to_use, sheet_name='Controle atendimentos')
                df["Arquivo"] = nome
                
                # Para unificar se for necessário no build_output_g
                if 'Valor Unitário' in df.columns and 'Valor atendimento' not in df.columns:
                    df = df.rename(columns={'Valor Unitário': 'Valor atendimento'})
                    
                frames.append(df)
                logs.append(("OK", nome, ""))
            else:
                faltando = [c for c in COLUNAS_E if c not in cols_encontradas]
                logs.append(("ERRO", nome, f"Colunas faltando: {faltando}"))
        except Exception as e:
            logs.append(("ERRO", nome, str(e)))

    if not frames:
        return pd.DataFrame(), logs

    df_all = pd.concat(frames, ignore_index=True)
    # Filtro: Desconsiderar linhas onde a Data ou o Status estejam nulos
    df_all = df_all[~df_all['Data '].isnull()].copy()
    
    col_status = 'Status atendimento \n(Realizado, Falta, Reagendou)'
    if col_status in df_all.columns:
        df_all = df_all[~df_all[col_status].isnull()].copy()
    df_all.rename(columns={'Data ':'Data','Nutri ':'Nutri'}, inplace=True)
    df_all["Data"] = pd.to_datetime(df_all["Data"], format="%d/%m/%Y", errors="coerce")
    df_all = label_semana(df_all)
    df_all['Ano'] = df_all['Data'].dt.year
    df_all['Mês'] = df_all['Data'].dt.month
    df_all['Nutri'] = df_all['Nutri'].str.strip().str.upper()
    df_all = tratar_nomes_nutri(df_all, 'Nutri')
    return df_all, logs


# ─── Outputs ──────────────────────────────────────────────────────────────────
def build_output_c(df_a, df_d):
    """Output C: tabela semanal Oferta × Ocupação"""
    if df_a.empty:
        df_oferta = pd.DataFrame()
    else:
        df_oferta = df_a.pivot_table(index='Semana_label', columns='Nutri', values='Janelas',
                                      aggfunc='sum', fill_value=0, dropna=False)
        df_oferta['TOTAL'] = df_oferta.sum(axis=1)
        df_oferta['CHECK'] = 'Oferta'

    if df_d.empty:
        df_ocup = pd.DataFrame()
    else:
        df_ocup = df_d.pivot_table(index='Semana_label', columns='Nutri', values='Número do caso',
                                    aggfunc='count', fill_value=0, dropna=False)
        df_ocup['TOTAL'] = df_ocup.sum(axis=1)
        df_ocup['CHECK'] = 'Ocupação'

    df_c = pd.concat([df_oferta, df_ocup]) if not df_oferta.empty or not df_ocup.empty else pd.DataFrame()
    if df_c.empty:
        return df_c
    cols = list(df_c.columns)
    mid  = sorted([c for c in cols if c not in ['CHECK','TOTAL']])
    
    if 'CHECK' not in df_c.columns: df_c['CHECK'] = ''
    if 'TOTAL' not in df_c.columns: df_c['TOTAL'] = 0

    df_c = df_c[['CHECK'] + mid + ['TOTAL']]
    df_c = df_c.fillna(0)
    df_c[mid + ['TOTAL']] = df_c[mid + ['TOTAL']].astype(int)
    return df_c


def build_output_f(df_a, df_d, df_e):
    """Output F: Oferta × Ocupação × Realizado por Nutri/Mês"""
    of = df_a.groupby(['Nutri','Ano','Mês'], as_index=False, dropna=False)['Janelas'].sum() if not df_a.empty else pd.DataFrame(columns=['Nutri','Ano','Mês','Oferta'])
    if not df_a.empty: of.rename(columns={'Janelas':'Oferta'}, inplace=True)

    oc = df_d.groupby(['Nutri','Ano','Mês'], as_index=False, dropna=False)['Número do caso'].count() if not df_d.empty else pd.DataFrame(columns=['Nutri','Ano','Mês','Ocupação'])
    if not df_d.empty: oc.rename(columns={'Número do caso':'Ocupação'}, inplace=True)

    df_d_realizado = df_d[df_d['Status sessão'] == 'Compareceu ao atendimento'] if not df_d.empty else pd.DataFrame()
    re_ = df_d_realizado.groupby(['Nutri','Ano','Mês'], as_index=False, dropna=False)['Número do caso'].count() if not df_d_realizado.empty else pd.DataFrame(columns=['Nutri','Ano','Mês','Realizado'])
    if not df_d_realizado.empty: re_.rename(columns={'Número do caso':'Realizado'}, inplace=True)

    if of.empty and oc.empty and re_.empty:
        return pd.DataFrame(columns=['Nutri','Ano','Mês','Oferta','Ocupação','Realizado','% Ocupação','% Realizado']), pd.DataFrame()

    df_f = of.merge(oc, on=['Nutri','Ano','Mês'], how='outer')
    df_f = df_f.merge(re_, on=['Nutri','Ano','Mês'], how='outer')
    df_f = df_f.fillna(0)
    df_f["% Ocupação"]  = (df_f["Ocupação"]  / df_f["Oferta"] ).replace([np.inf, np.nan], 0) * 100
    df_f["% Realizado"] = (df_f["Realizado"] / df_f["Ocupação"]).replace([np.inf, np.nan], 0) * 100

    # Remover linhas onde tudo é zero
    cols_num = ['Oferta','Ocupação','Realizado']
    df_f = df_f[~(df_f[cols_num] == 0).all(axis=1)]

    # Alertar datas inválidas
    check_bad = df_f[(df_f[['Ano','Mês']] == 0).all(axis=1) & (df_f[cols_num] > 0).any(axis=1)]
    df_f = df_f[~df_f.index.isin(check_bad.index)]
    df_f['Ano'] = df_f['Ano'].astype(int)
    df_f['Mês'] = df_f['Mês'].astype(int)
    df_f = df_f.sort_values(['Ano','Mês','Nutri'])
    return df_f, check_bad


def build_output_g(df_d, df_e):
    """Output G: faturamento por status de sessão + check com planilhas nutris"""
    df_g_raw = df_d.copy()
    
    # 1. Obter valor do faturamento estritamente do Input D ('Valor atendimento' ou 'Valor Unitário')
    val_col_d = None
    if 'Valor atendimento' in df_g_raw.columns and df_g_raw['Valor atendimento'].notnull().any():
        val_col_d = 'Valor atendimento'
    elif 'Valor Unitário' in df_g_raw.columns and df_g_raw['Valor Unitário'].notnull().any():
        val_col_d = 'Valor Unitário'
        
    if val_col_d:
        df_g_raw['Valor_Real'] = df_g_raw[val_col_d].apply(safe_to_numeric)
    else:
        df_g_raw['Valor_Real'] = 0.0

    # Adicionando Ano ao index para suportar ranges de datas
    df_g = df_g_raw.pivot_table(
        index=['Ano','Mês','Nutri'], columns='Status sessão',
        aggfunc={'Número do caso':'count','Valor_Real':'sum'},
        fill_value=0, dropna=False
    )
    
    # Renomear nível da coluna para bater com o padrão exigido nas telas e no backend
    df_g = df_g.rename(columns={'Valor_Real': 'Valor Unitário'}, level=0)
    
    df_g['Total Agendamentos'] = df_g['Número do caso'].sum(axis=1)
    df_g['Total Faturamento']  = df_g['Valor Unitário'].sum(axis=1)

    # Check com planilhas
    if not df_e.empty:
        tb = df_e.groupby(['Ano','Mês','Nutri'], dropna=False, as_index=False)[['ID caso']].count()
        tb.rename(columns={'ID caso':'Planilhas'}, inplace=True)
        
        # Mapear direto para o df_g usando o index triplo
        tb = tb.set_index(['Ano','Mês','Nutri'])
        df_g['Planilhas'] = df_g.index.map(tb['Planilhas'].to_dict()).fillna(0)
        
        # Calcular o check verificando a igualdade de agendamentos e planilhas
        col_agendamentos = 'Total Agendamentos'
        if col_agendamentos not in df_g.columns and ('Total Agendamentos', '') in df_g.columns:
            col_agendamentos = ('Total Agendamentos', '')
            
        df_g['Check'] = (df_g[col_agendamentos] == df_g['Planilhas']).map({False:'⚠️ Not OK', True:'✅ OK'})

    return df_g


def build_graph_mensal(df_f):
    """Gráfico barras+linha Oferta/Ocupação/Realizado por mês"""
    df_h = df_f.groupby(['Ano','Mês'], as_index=False, dropna=False)[['Oferta','Ocupação','Realizado']].sum()
    df_h["% Ocupação"]  = (df_h["Ocupação"]  / df_h["Oferta"] ).replace([np.inf, np.nan], 0) * 100
    df_h["% Realizado"] = (df_h["Realizado"] / df_h["Ocupação"]).replace([np.inf, np.nan], 0) * 100
    df_h['Competencia'] = pd.to_datetime({"year": df_h["Ano"], "month": df_h["Mês"], "day": 1})
    df_h = df_h.sort_values("Competencia")
    df_h["Label"] = df_h["Competencia"].dt.strftime("%b_%y")
    return df_h


def build_graph_dia_semana(df_a, df_d, df_e):
    """Gráfico barras+linha por dia da semana consolidado"""
    a = df_a.copy()
    d = df_d.copy()
    e = df_e.copy() if not df_e.empty else pd.DataFrame()

    for df_ in [a, d, e]:
        if not df_.empty:
            df_['Data'] = pd.to_datetime(df_['Data'], errors='coerce')
            df_['Dia_semana_cod']  = df_['Data'].dt.weekday
            df_['Dia_semana_desc'] = df_['Dia_semana_cod'].map(dict_dia_semana)

    if not a.empty:
        of = a.groupby(['Dia_semana_cod','Dia_semana_desc'], as_index=False, dropna=False)['Janelas'].sum()
        of.rename(columns={'Janelas':'Oferta'}, inplace=True)
    else:
        of = pd.DataFrame(columns=['Dia_semana_cod','Dia_semana_desc','Oferta'])

    if not d.empty:
        oc = d.groupby(['Dia_semana_cod','Dia_semana_desc'], as_index=False, dropna=False)['Número do caso'].count()
        oc.rename(columns={'Número do caso':'Ocupação'}, inplace=True)
    else:
        oc = pd.DataFrame(columns=['Dia_semana_cod','Dia_semana_desc','Ocupação'])

    df_i = of.merge(oc, on=['Dia_semana_cod','Dia_semana_desc'], how='outer')

    if not d.empty and 'Dia_semana_cod' in d.columns:
        d_realizado = d[d['Status sessão'] == 'Compareceu ao atendimento']
        re_ = d_realizado.groupby(['Dia_semana_cod','Dia_semana_desc'], as_index=False, dropna=False)['Número do caso'].count() if not d_realizado.empty else pd.DataFrame(columns=['Dia_semana_cod','Dia_semana_desc','Realizado'])
        if not d_realizado.empty: re_.rename(columns={'Número do caso':'Realizado'}, inplace=True)
        df_i = df_i.merge(re_, on=['Dia_semana_cod','Dia_semana_desc'], how='outer')
    else:
        df_i['Realizado'] = 0

    df_i = df_i.fillna(0)
    df_i["% Ocupação"]  = (df_i["Ocupação"]  / df_i["Oferta"] ).replace([np.inf, np.nan], 0) * 100
    df_i["% Realizado"] = (df_i["Realizado"] / df_i["Ocupação"]).replace([np.inf, np.nan], 0) * 100
    df_i = df_i.sort_values('Dia_semana_cod')
    return df_i


def preparar_tabela_dia_semana(df_i):
    """Transforma o DF de Dia da Semana para o formato da imagem (transposto)"""
    if df_i.empty:
        return pd.DataFrame()
    
    # Selecionar e renomear para exibição
    cols_order = ['Oferta', 'Ocupação', 'Realizado', '% Ocupação', '% Realizado']
    df_t = df_i.set_index('Dia_semana_desc')[cols_order].T
    
    # Formatação amigável
    for col in df_t.columns:
        # Valores absolutos
        for metric in ['Oferta', 'Ocupação', 'Realizado']:
            val = df_t.loc[metric, col]
            df_t.loc[metric, col] = f"{int(val):,}".replace(",", ".")
        # Percentuais
        for metric in ['% Ocupação', '% Realizado']:
            val = df_t.loc[metric, col]
            df_t.loc[metric, col] = f"{val:.0f}%"
            
    return df_t.reset_index().rename(columns={'index': 'Métrica'})


def grafico_barra_linha(df_plot, col_x, titulo):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    cores = {'Oferta':'#66cbdd','Ocupação':'#044851','Realizado':'#c3d76b'}
    for col, cor in cores.items():
        if col in df_plot.columns:
            fig.add_trace(go.Bar(x=df_plot[col_x], y=df_plot[col], name=col,
                                 marker_color=cor, text=df_plot[col], textposition="outside"),
                          secondary_y=False)
    for col, cor in [("% Ocupação","#fcc105"),("% Realizado","#463e8c")]:
        if col in df_plot.columns:
            fig.add_trace(go.Scatter(x=df_plot[col_x], y=df_plot[col], name=col,
                                     mode="lines+markers+text",
                                     text=df_plot[col].round(0).astype(int).astype(str)+"%",
                                     textposition="top center",
                                     line=dict(color=cor, width=2)),
                          secondary_y=True)
    fig.update_layout(title=titulo, barmode="group", hovermode="x unified",
                      legend_title="Indicadores", margin=dict(t=80,l=40,r=40,b=80),
                      height=450)
    
    # Cálculo dinâmico para evitar sobreposição:
    # 1. Escala Absoluta (Barras): ocupam a parte inferior (até ~60%)
    # 2. Escala Percentual (Linhas): ocupam a parte superior (acima das barras)
    max_abs = df_plot[['Oferta', 'Ocupação', 'Realizado']].max().max() if not df_plot.empty else 100
    
    fig.update_yaxes(title_text="Agendas", range=[0, max_abs * 1.8], secondary_y=False)
    fig.update_yaxes(title_text="Percentual (%)", range=[-120, 110], secondary_y=True)
    return fig


# ─── Formatação ───────────────────────────────────────────────────────────────
def fmt_num(v):
    try: return f"{int(v):,}".replace(",",".")
    except: return str(v)

def fmt_pct(x):
    if pd.isna(x): return "—"
    return f"{x:.1f}%".replace(".", ",")

def to_excel(df, index=False):
    """Converte DataFrame para bytes de um arquivo Excel (.xlsx)."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=index)
    return output.getvalue()

def fmt_val(v):
    if v is None: return "R$ 0,00"
    s = "-" if v < 0 else ""
    a = abs(v)
    return f"{s}R$ {a:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def apply_row_colors(row):
    c = '#ffffff' if row.name % 2 == 0 else '#e8f7fa'
    return [f'background-color: {c}'] * len(row)

def abrev_nutri(nome):
    """Retorna Primeiro + Último sobrenome. Ex: BEATRIZ BOTEQUIO DE MORAES MACHADO → Beatriz Machado"""
    if pd.isna(nome) or nome is None:
        return "N/A"
    nome_str = str(nome)
    partes = nome_str.strip().split()
    if len(partes) <= 2:
        return nome_str.title()
    return f"{partes[0].title()} {partes[-1].title()}"


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
defaults = {
    'current_step': 1,
    'carga_step': 1,
    'df_a': None, 'df_d': None, 'df_e': None,
    'logs_d': [], 'logs_e': [],
    'df_c': None, 'df_f': None, 'df_g': None,
    'bad_dates': None,
    'custo_nutri_mes': 0.0, 'impostos': 0.0, 'valor_consulta': 0.0,
    'firebase_ok': False,
    'confirmar_sobrescrita': False,
    'pre_save_data': None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Inicializar Firebase ──────────────────────────────────────────────────────
@st.cache_resource
def _init_firebase():
    try:
        from firebase_config import db
        return db
    except FileNotFoundError:
        return None
    except Exception:
        return None

_fb_db = _init_firebase()


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
try:
    if HAS_PIL:
        col_logo, col_title = st.columns([1, 9])
        with col_logo:
            logo = Image.open("images/flua-logo.png")
            st.image(logo, width=80)
        with col_title:
            st.markdown('<div class="main-header">Dashboard Mensal - Flua Nutrição</div>', unsafe_allow_html=True)
    else:
        raise Exception()
except:
    st.markdown('<div class="main-header">📊 Dashboard Mensal - Flua Nutrição</div>', unsafe_allow_html=True)

st.markdown("### 📅 Análise Mensal — Oferta · Ocupação · Realizado")

# Navegação
c1, c2 = st.columns(2)
with c1:
    if st.button("📤 Seção 1: Carga de Dados", use_container_width=True,
                 type="primary" if st.session_state.current_step == 1 else "secondary"):
        st.session_state.current_step = 1
with c2:
    if st.button("📊 Seção 2: Dashboard de Resultados", use_container_width=True,
                 type="primary" if st.session_state.current_step == 2 else "secondary"):
        st.session_state.current_step = 2

st.markdown("---")


# ═════════════════════════════════════════════════════════════════════════════
# SEÇÃO 1 — CARGA DE DADOS
# ═════════════════════════════════════════════════════════════════════════════
if st.session_state.current_step == 1:
    st.markdown('<div class="section-header">📤 Seção 1: Carga de Dados</div>', unsafe_allow_html=True)

    if _fb_db is None:
        st.markdown('''
        <div class="error-box">
            <h4>⚠️ Firebase não configurado</h4>
            <p>O arquivo <code>serviceAccountKey.json</code> não foi encontrado na raiz do projeto.</p>
            <ol>
                <li>Acesse <a href="https://console.firebase.google.com/" target="_blank">Firebase Console</a></li>
                <li>Crie um projeto (ex: <code>flua-nutricao</code>)</li>
                <li>Vá em <strong>Build → Firestore Database → Create database</strong></li>
                <li>Em <strong>Project Settings → Service accounts → Generate new private key</strong></li>
                <li>Salve o JSON como <code>serviceAccountKey.json</code> na raiz do projeto</li>
            </ol>
        </div>
        ''', unsafe_allow_html=True)
    else:
        # Render Stepper
        step = st.session_state.carga_step
        active_1 = "active" if step >= 1 else ""
        active_2 = "active" if step >= 2 else ""
        div_act_12 = "active" if step >= 2 else ""
        
        stepper_html = f'''
        <div class="stepper-container">
            <div class="step {active_1}">
                <div class="step-number">1</div>
                <div>Setup e Upload</div>
            </div>
            <div class="step-divider {div_act_12}"></div>
            <div class="step {active_2}">
                <div class="step-number">2</div>
                <div>Revisão e Envio</div>
            </div>
        </div>
        '''
        st.markdown(stepper_html, unsafe_allow_html=True)

        # Passo 1: Setup e Upload
        if step == 1:
            st.markdown('''
            <div class="info-box">
                <h4>📋 Passo 1: Configuração e Importação</h4>
                <p>Selecione a competência, defina os parâmetros e anexe os arquivos. Em seguida, os dados serão lidos para validação visual na aba de Revisão.</p>
            </div>
            ''', unsafe_allow_html=True)

            # ── Competência ──
            col_setup1, col_setup2 = st.columns([1, 1])
            with col_setup1:
                st.markdown('<div class="upload-card"><h4>📅 Competência</h4>', unsafe_allow_html=True)
                c_mes, c_ano = st.columns(2)
                with c_mes:
                    mes_carga = st.selectbox("Mês", list(range(1, 13)), format_func=lambda x: dict_mes_full[x], key="mes_carga")
                with c_ano:
                    ano_carga = st.number_input("Ano", min_value=2020, max_value=2030, value=datetime.now().year, step=1, key="ano_carga")
                
                periodo_existe = data_loader.verificar_periodo_existe(_fb_db, int(ano_carga), int(mes_carga))
                if periodo_existe:
                    st.markdown('''
                    <div style="margin-top: 10px; background-color: #fff8e0; border-left: 4px solid #fcc105; padding: 10px; font-size: 0.9em; border-radius: 4px; color: #8a6d00;">
                        ⚠️ Período já existe. O novo envio irá sobrescrever os dados para esta competência.
                    </div>
                    ''', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_setup2:
                st.markdown('<div class="upload-card"><h4>💰 Parâmetros Financeiros</h4>', unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1:
                    custo = st.number_input("Custo Nutris (R$)", min_value=0.0, value=float(st.session_state.custo_nutri_mes), step=1000.0, key="custo_carga")
                with c2:
                    imp = st.number_input("Impostos (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.impostos), step=0.5, key="imp_carga")
                with c3:
                    val = st.number_input("Valor Conf. (R$)", min_value=0.0, value=float(st.session_state.valor_consulta), step=1.0, key="val_carga")
                st.markdown('</div>', unsafe_allow_html=True)

            # ── Uploads ──
            st.markdown('<div class="upload-card"><h4>📥 1. Disponibilidade Optum</h4>', unsafe_allow_html=True)
            file_a = st.file_uploader("Arquivo A (Planilha de Oferta - 1 arquivo)", type=['xlsx','xls'], key="file_a_carga")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="upload-card"><h4>📥 2. Relatórios de Sessões Optum</h4>', unsafe_allow_html=True)
            files_d = st.file_uploader("Arquivos D (Agendamentos Ocupados - Múltiplos)", type=['xlsx','xls'], accept_multiple_files=True, key="files_d_carga")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="upload-card"><h4>📥 3. Controles das Nutricionistas</h4>', unsafe_allow_html=True)
            files_e = st.file_uploader("Arquivos E (Auditoria para Check - Múltiplos)", type=['xlsx','xls'], accept_multiple_files=True, key="files_e_carga")
            st.markdown('</div>', unsafe_allow_html=True)

            pode_enviar = file_a is not None or len(files_d) > 0 or len(files_e) > 0

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Processar Dados e Revisar (Avançar) ➡️", type="primary", use_container_width=True, disabled=not pode_enviar):
                with st.spinner("⏳ Analisando dados em memória..."):
                    try:
                        # Process in memory
                        dados_existentes = None
                        if periodo_existe:
                            dados_existentes = data_loader.carregar_dados_mensal(_fb_db, int(ano_carga), int(mes_carga))
                            
                        df_a_db = dados_existentes.get('input_a', pd.DataFrame()) if dados_existentes else pd.DataFrame()
                        df_d_db = dados_existentes.get('input_d', pd.DataFrame()) if dados_existentes else pd.DataFrame()
                        df_e_db = dados_existentes.get('input_e', pd.DataFrame()) if dados_existentes else pd.DataFrame()

                        if df_a_db.empty: df_a_db = pd.DataFrame(columns=['Data completa','Ano','Mês','Mês_Ano','DDS','Início','Fim','Total horas','Janelas','Nutri','Data','Semana_mes','Semana_label'])
                        if df_d_db.empty: df_d_db = pd.DataFrame(columns=['Número do caso','Beneficiário','Empresa','Data inicial do caso','Status do caso','Tipo medida tomada','Nutri','Data','Tempo atendimento','Status sessão','Valor Unitário','Semana_mes','Semana_label','Ano','Mês'])
                        if df_e_db.empty: df_e_db = pd.DataFrame(columns=['Data', 'Nutri', 'ID caso', 'Status atendimento \n(Realizado, Falta, Reagendou)', 'Arquivo', 'Semana_mes', 'Semana_label', 'Ano', 'Mês'])

                        file_a_obj = st.session_state.get("file_a_carga")
                        if file_a_obj: file_a_obj.seek(0)
                        df_a = processar_input_a(file_a_obj) if file_a_obj else df_a_db

                        files_d_obj = st.session_state.get("files_d_carga", [])
                        if files_d_obj:
                            for f in files_d_obj: f.seek(0)
                        df_d, logs_d = processar_input_d(files_d_obj) if files_d_obj else (df_d_db, [])

                        files_e_obj = st.session_state.get("files_e_carga", [])
                        if files_e_obj:
                            for f in files_e_obj: f.seek(0)
                        df_e, logs_e = processar_input_e(files_e_obj) if files_e_obj else (df_e_db, [])

                        # --- FILTRO DE COMPETÊNCIA ---
                        # Aplica máscara para garantir que apenas o mês/ano selecionado seja processado (vital para Input E que possui histórico)
                        _ano, _mes = int(ano_carga), int(mes_carga)
                        if not df_a.empty and 'Ano' in df_a.columns: df_a = df_a[(df_a['Ano'] == _ano) & (df_a['Mês'] == _mes)].copy()
                        if not df_d.empty and 'Ano' in df_d.columns: df_d = df_d[(df_d['Ano'] == _ano) & (df_d['Mês'] == _mes)].copy()
                        if not df_e.empty and 'Ano' in df_e.columns: df_e = df_e[(df_e['Ano'] == _ano) & (df_e['Mês'] == _mes)].copy()

                        df_c = build_output_c(df_a, df_d)
                        df_f, bad = build_output_f(df_a, df_d, df_e)
                        df_g = build_output_g(df_d, df_e) if not df_d.empty else None

                        st.session_state.pre_save_data = {
                            "ano": int(ano_carga),
                            "mes": int(mes_carga),
                            "custo": custo,
                            "imp": imp,
                            "val": val,
                            "df_a": df_a, "df_d": df_d, "df_e": df_e,
                            "df_c": df_c, "df_f": df_f, "df_g": df_g,
                            "logs_d": logs_d, "logs_e": logs_e, "bad": bad
                        }
                        st.session_state.carga_step = 2
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro no processamento: {e}")
                        import traceback
                        st.code(traceback.format_exc())

        # Passo 2: Verificacao e Envio
        elif step == 2:
            st.markdown('''
            <div class="success-box" style="margin-bottom: 20px;">
                <h4>✅ Leitura Concluída (Em Memória)</h4>
                <p>Verifique o resumo operacional abaixo. Se tudo estiver correto, clique em Confirmar para salvar os dados no dashboard oficial.</p>
            </div>
            ''', unsafe_allow_html=True)
            
            data = st.session_state.get('pre_save_data')
            if not data:
                st.session_state.carga_step = 1
                st.rerun()
                
            df_a = data['df_a']
            df_g = data['df_g']
            df_e = data['df_e']
            
            # KPI rápidos
            oferta_total = df_a['Janelas'].sum() if not df_a.empty else 0
            ocup_total = df_g['Total Agendamentos'].sum() if df_g is not None and 'Total Agendamentos' in df_g.columns else 0
            fat_total = df_g['Total Faturamento'].sum() if df_g is not None and 'Total Faturamento' in df_g.columns else 0

            if df_g is not None:
                nutris_encontradas = len(df_g.index.get_level_values('Nutri').unique())
            else:
                nutris_encontradas = 0

            st.markdown(f'''
            <div class="kpi-wrapper">
                <div class="kpi-card" style="--card-color: #66cbdd;">
                    <div class="kpi-icon">📦</div>
                    <div class="kpi-label">Janelas Lidas</div>
                    <div class="kpi-value">{int(oferta_total)}</div>
                </div>
                <div class="kpi-card" style="--card-color: #044851;">
                    <div class="kpi-icon">📅</div>
                    <div class="kpi-label">Sessões Lidas</div>
                    <div class="kpi-value">{int(ocup_total)}</div>
                </div>
                <div class="kpi-card" style="--card-color: #c3d76b;">
                    <div class="kpi-icon">👥</div>
                    <div class="kpi-label">Nutris Identificadas</div>
                    <div class="kpi-value">{nutris_encontradas}</div>
                </div>
                <div class="kpi-card" style="--card-color: #2ecc71;">
                    <div class="kpi-icon">💰</div>
                    <div class="kpi-label">Previsão Faturamento</div>
                    <div class="kpi-value"><span class="currency">R$</span> {fat_total:,.2f}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

            # Logs de Erro
            logs_d = data['logs_d']
            logs_e = data['logs_e']
            has_errors = any(s == "ERRO" for s, n, m in logs_d) or any(s == "ERRO" for s, n, m in logs_e)
            
            if has_errors:
                st.markdown('<div class="error-box" style="margin-bottom: 20px;">⚠️ Houve problemas na leitura de alguns arquivos. Confira abaixo.</div>', unsafe_allow_html=True)
                
            c_log1, c_log2 = st.columns(2)
            with c_log1:
                if logs_d:
                    with st.expander("📄 Logs do Optum (Input D)", expanded=has_errors):
                        for status, nome, msg in logs_d:
                            st.markdown(f"{'✅' if status == 'OK' else '❌'} **{nome}**" + (f" — {msg}" if msg else ""))
            with c_log2:
                if logs_e:
                    with st.expander("📄 Logs das Planilhas (Input E)", expanded=has_errors):
                        for status, nome, msg in logs_e:
                            st.markdown(f"{'✅' if status == 'OK' else '❌'} **{nome}**" + (f" — {msg}" if msg else ""))
            
            bad = data.get('bad')
            if bad is not None and not bad.empty:
                st.markdown('<div class="error-box" style="margin-top:20px;">⚠️ Linhas ignoradas por falta de Data/Valores em Branco ou Ano 0:</div>', unsafe_allow_html=True)
                st.dataframe(bad, use_container_width=True)

            st.markdown("---")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("⬅️ Retornar e Editar Parâmetros", use_container_width=True):
                    st.session_state.carga_step = 1
                    st.rerun()
            with col_b2:
                if st.button("🚀 Confirmar e Enviar ao Banco", type="primary", use_container_width=True):
                    with st.spinner("💾 Persistindo no Firebase..."):
                        try:
                            # Save
                            dt = st.session_state.pre_save_data
                            dados_para_salvar = {
                                "input_a": dt['df_a'],
                                "input_d": dt['df_d'],
                                "input_e": dt['df_e'],
                                "output_c": dt['df_c'],
                                "output_f": dt['df_f'],
                            }
                            df_g_save = dt['df_g']
                            if df_g_save is not None:
                                df_g_flat = df_g_save.reset_index()
                                df_g_flat.columns = [' - '.join([str(c) for c in col]).strip(' - ') if isinstance(col, tuple) else col for col in df_g_flat.columns]
                                dados_para_salvar["output_g"] = df_g_flat

                            oferta_t_meta = float(dt['df_a']['Janelas'].sum()) if not dt['df_a'].empty else 0.0
                            meta_fat_val = float(np.ceil(oferta_t_meta * 0.8) * 84)
                            
                            fat_val = float(df_g_save['Total Faturamento'].sum()) if df_g_save is not None and not df_g_save.empty and 'Total Faturamento' in df_g_save.columns else 0.0

                            data_loader.salvar_dados_mensal(
                                _fb_db,
                                dt['ano'], dt['mes'],
                                dados_para_salvar,
                                custo_nutri_mes=dt['custo'],
                                impostos=dt['imp'],
                                valor_consulta=dt['val'],
                                faturamento=fat_val,
                                meta_faturamento=meta_fat_val,
                            )

                            if '_cache_periodos' in st.session_state:
                                del st.session_state['_cache_periodos']

                            st.session_state.carga_step = 1
                            st.session_state.pre_save_data = None
                            st.success(f"✅ Dados de {dict_mes_full[dt['mes']]}/{dt['ano']} processados e salvos com sucesso!")
                        except Exception as e:
                            st.error(f"❌ Falha ao salvar no banco: {e}")

        # ── Períodos já carregados ───────────────────────────────────────────
        if step == 1:
            st.markdown("---")
            st.subheader("📋 Histórico do Banco de Dados")
            try:
                periodos = data_loader.listar_periodos(_fb_db)
                if periodos:
                    df_periodos = pd.DataFrame(periodos)
                    df_periodos['Período'] = df_periodos.apply(lambda r: f"{dict_mes_full.get(r['mes'], '?')}/{r['ano']}", axis=1)
                    df_periodos['Última atualização'] = df_periodos['data_upload']
                    st.dataframe(df_periodos[['Período', 'Última atualização']].reset_index(drop=True), use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhum período carregado ainda.")
            except Exception as e:
                st.warning(f"Erro ao listar períodos: {e}")


# ═════════════════════════════════════════════════════════════════════════════
# SEÇÃO 2 — DASHBOARD DE RESULTADOS
# ═════════════════════════════════════════════════════════════════════════════
elif st.session_state.current_step == 2:
    st.markdown('<div class="section-header">📊 Seção 2: Dashboard de Resultados</div>', unsafe_allow_html=True)

    if _fb_db is None:
        st.error("⚠️ Firebase não configurado. Vá à Seção 1 para instruções.")
    else:
        # Listar períodos disponíveis
        periodos = data_loader.listar_periodos(_fb_db)
        if not periodos:
            st.info("📭 Nenhum período disponível. Faça a carga de dados na Seção 1.")
        else:
            # Ordenar períodos cronologicamente
            periodos_sorted = sorted(periodos, key=lambda p: (p['ano'], p['mes']))
            opcoes_periodo = {
                f"{dict_mes_abrev.get(p['mes'], '?')}/{p['ano']}": (p['ano'], p['mes'])
                for p in periodos_sorted
            }
            opcoes_labels = list(opcoes_periodo.keys())

            # Filtro de range: De → Até
            col_de, col_ate = st.columns(2)
            with col_de:
                sel_inicio = st.selectbox("🗓️ De:", opcoes_labels, index=0, key="filtro_inicio")
            with col_ate:
                sel_fim = st.selectbox("Até:", opcoes_labels, index=len(opcoes_labels) - 1, key="filtro_fim")

            ano_ini, mes_ini = opcoes_periodo[sel_inicio]
            ano_fim, mes_fim = opcoes_periodo[sel_fim]

            periodos_no_range = [
                key for key, (ano, mes) in opcoes_periodo.items()
                if (ano_ini, mes_ini) <= (ano, mes) <= (ano_fim, mes_fim)
            ]

            if not periodos_no_range:
                st.warning("⚠️ O período inicial é maior que o período final. Ajuste o filtro.")
                st.stop()

            @st.cache_data(ttl=300)
            def _carregar_todos(periodos_keys):
                todos = {}
                for key in periodos_keys:
                    ano, mes = opcoes_periodo[key]
                    dados = data_loader.carregar_dados_mensal(_fb_db, ano, mes)
                    if dados:
                        todos[key] = dados
                return todos

            todos_dados = _carregar_todos(tuple(periodos_no_range))

            # Consolidar DataFrames do range
            dfs_f, dfs_a, dfs_d, dfs_e, dfs_g = [], [], [], [], []
            for key, d in todos_dados.items():
                ano_ref, mes_ref = opcoes_periodo[key]
                for df_key, target_list in [('output_f', dfs_f), ('input_a', dfs_a), 
                                            ('input_d', dfs_d), ('input_e', dfs_e), ('output_g', dfs_g)]:
                    if df_key in d and not d[df_key].empty:
                        df_tmp = d[df_key].copy()
                        if 'Ano' not in df_tmp.columns: df_tmp['Ano'] = ano_ref
                        if 'Mês' not in df_tmp.columns: df_tmp['Mês'] = mes_ref
                        target_list.append(df_tmp)

            df_f = pd.concat(dfs_f, ignore_index=True) if dfs_f else pd.DataFrame()
            df_a = pd.concat(dfs_a, ignore_index=True) if dfs_a else pd.DataFrame()
            df_d = pd.concat(dfs_d, ignore_index=True) if dfs_d else pd.DataFrame()
            df_e = pd.concat(dfs_e, ignore_index=True) if dfs_e else pd.DataFrame()
            df_g = pd.concat(dfs_g, ignore_index=True) if dfs_g else pd.DataFrame()

            # ── Filtro de data pós-carga ──────────────────────────────────────
            # Os documentos do Firestore podem conter linhas de outros meses;
            # aplicamos o range exato aqui para garantir consistência em todos
            # os gráficos e tabelas.
            def _filtrar_por_range(df, a_ini, m_ini, a_fim, m_fim):
                if df.empty or 'Ano' not in df.columns or 'Mês' not in df.columns:
                    return df
                df = df.copy()
                df['_ano'] = pd.to_numeric(df['Ano'], errors='coerce').fillna(0).astype(int)
                df['_mes'] = pd.to_numeric(df['Mês'], errors='coerce').fillna(0).astype(int)
                mask = df.apply(
                    lambda r: (a_ini, m_ini) <= (r['_ano'], r['_mes']) <= (a_fim, m_fim), axis=1
                )
                return df[mask].drop(columns=['_ano', '_mes']).reset_index(drop=True)

            df_f = _filtrar_por_range(df_f, ano_ini, mes_ini, ano_fim, mes_fim)
            df_a = _filtrar_por_range(df_a, ano_ini, mes_ini, ano_fim, mes_fim)
            df_d = _filtrar_por_range(df_d, ano_ini, mes_ini, ano_fim, mes_fim)
            df_e = _filtrar_por_range(df_e, ano_ini, mes_ini, ano_fim, mes_fim)
            df_g = _filtrar_por_range(df_g, ano_ini, mes_ini, ano_fim, mes_fim)

            # Reconstruir df_c a partir dos inputs já filtrados
            if not df_a.empty and not df_d.empty:
                df_c = build_output_c(df_a, df_d)
            else:
                df_c = pd.DataFrame()

            periodo_label = sel_inicio if sel_inicio == sel_fim else f"{sel_inicio} a {sel_fim}"

            # Params financeiros: usar último período do range
            ultimo = list(todos_dados.values())[-1]['meta'] if todos_dados else {}
            st.session_state.custo_nutri_mes = ultimo.get('custo_nutri_mes', 0)
            st.session_state.impostos = ultimo.get('impostos', 0)
            st.session_state.valor_consulta = ultimo.get('valor_consulta', 0)


            if df_f.empty:
                st.warning("Sem dados para exibir neste período.")
                st.stop()

            # Garantir tipos numéricos em df_f
            for col in ['Oferta', 'Ocupação', 'Realizado', '% Ocupação', '% Realizado']:
                if col in df_f.columns:
                    df_f[col] = pd.to_numeric(df_f[col], errors='coerce').fillna(0)
            for col in ['Ano', 'Mês']:
                if col in df_f.columns:
                    df_f[col] = pd.to_numeric(df_f[col], errors='coerce').fillna(0).astype(int)

            # Aliases para uso nos gráficos e tabelas
            df_f_fil = df_f
            df_a_fil = df_a
            df_d_fil = df_d
            df_e_fil = df_e

            # ── KPIs ─────────────────────────────────────────────────────────
            st.subheader("📈 KPIs Principais")
            oferta_t    = int(df_f_fil['Oferta'].sum())
            ocupacao_t  = int(df_f_fil['Ocupação'].sum())
            realizado_t = int(df_f_fil['Realizado'].sum()) if 'Realizado' in df_f_fil.columns else 0
            tx_ocup     = (ocupacao_t / oferta_t * 100) if oferta_t > 0 else 0
            tx_real     = (realizado_t / ocupacao_t * 100) if ocupacao_t > 0 else 0

            # Nova regra: Meta Faturamento = ceil(Oferta Total * 0.8) * 84
            meta_faturamento = int(np.ceil(oferta_t * 0.8) * 84)

            # Faturamento = Soma de todos os valores de consulta do Optum (Input D via Output G)
            if df_g is not None and not df_g.empty and 'Total Faturamento' in df_g.columns:
                faturamento = float(df_g['Total Faturamento'].sum())
            else:
                faturamento = 0.0

            def kpi_card(label, value, icon, color, delta_text=None, delta_positive=None):
                """Retorna HTML de um card KPI estilizado."""
                if delta_text:
                    css = "kpi-delta-pos" if delta_positive else "kpi-delta-neg"
                    arrow = "↑" if delta_positive else "↓"
                    delta_html = f'<div class="{css}">{arrow} {delta_text}</div>'
                else:
                    delta_html = '<div class="kpi-delta-neu">&nbsp;</div>'
                
                # Tratar R$ para ficar menor e evitar quebra
                if isinstance(value, str) and "R$" in value:
                    value = value.replace("R$", '<span class="currency">R$</span>')

                return f"""<div class="kpi-card" style="--card-color: {color};">
<div class="kpi-icon">{icon}</div>
<div class="kpi-label">{label}</div>
<div class="kpi-value">{value}</div>
{delta_html}
</div>"""

            delta_ocup = tx_ocup - 80
            
            # Montar o grid de KPIs em HTML para usar Flexbox (removendo indentação para evitar bloco de código no Streamlit)
            html_kpis = f"""<div class="kpi-wrapper">
{kpi_card("Oferta Total",     fmt_num(oferta_t),     "📦", "#66cbdd")}
{kpi_card("Ocupação Total",   fmt_num(ocupacao_t),   "📅", "#044851")}
{kpi_card("Realizado Total",  fmt_num(realizado_t),  "✅", "#c3d76b")}
{kpi_card("Taxa de Ocupação", fmt_pct(tx_ocup),      "📊", "#fcc105", 
          fmt_pct(abs(delta_ocup)), delta_ocup >= 0)}
{kpi_card("Taxa Realização",  fmt_pct(tx_real),      "🎯", "#463e8c")}
{kpi_card("Meta Faturamento", fmt_val(meta_faturamento), "🏁", "#aab7b8")}
{kpi_card(
    "Faturamento",
    fmt_val(faturamento),
    "💰", "#2ecc71",
    *(
        (f"{abs(((faturamento/meta_faturamento)-1)*100):.1f}% da meta".replace(".", ","),
         faturamento >= meta_faturamento)
        if meta_faturamento > 0 else (None, None)
    )
)}
</div>"""
            st.markdown(html_kpis, unsafe_allow_html=True)

            # ── Output G — Faturamento ────────────────────────────────────────
            if df_g is not None and not (isinstance(df_g, pd.DataFrame) and df_g.empty):
                st.markdown("---")
                st.subheader(f"💰 Faturamento por Nutricionista e Status de Sessão — {periodo_label}")
                try:
                        if isinstance(df_g, pd.DataFrame):
                            df_g_disp = df_g.reset_index(drop=True).copy()

                            # Abreviar nomes das nutricionistas
                            if 'Nutri' in df_g_disp.columns:
                                df_g_disp['Nutri'] = df_g_disp['Nutri'].apply(abrev_nutri)

                            # Mapear Mês para nome (se for numérico)
                            if 'Mês' in df_g_disp.columns:
                                df_g_disp['Mês'] = pd.to_numeric(df_g_disp['Mês'], errors='coerce').fillna(0).astype(int)
                                df_g_disp['Mês'] = df_g_disp['Mês'].map(dict_mes_full)

                            # Encurtar cabeçalhos de colunas longas
                            def _abrev_col(col):
                                subs = [
                                    ('Número do caso', 'Nº'),
                                    ('Valor Unitário', 'Valor (R$)'),
                                    ('Compareceu ao atendimento', 'Compareceu'),
                                    ('Faltou ao atendimento', 'Faltou'),
                                    ('Total Agendamentos', 'Total Agend.'),
                                    ('Total Faturamento', 'Fat. Total (R$)'),
                                ]
                                for old, new in subs:
                                    col = col.replace(old, new)
                                return col.strip(' -')
                            df_g_disp.columns = [_abrev_col(c) for c in df_g_disp.columns]

                            # Garantir inteiros nas colunas de contagem
                            for _col in ['Nº - Faltou', 'Nº - Compareceu', 'Total Agend.', 'Planilhas']:
                                if _col in df_g_disp.columns:
                                    df_g_disp[_col] = pd.to_numeric(df_g_disp[_col], errors='coerce').fillna(0).astype(int)

                            # Ordenar conforme solicitado: valores monetários agrupados, depois contagens
                            desired_order = [
                                'Ano', 'Mês', 'Nutri',
                                'Valor (R$) - Faltou', 'Valor (R$) - Compareceu', 'Fat. Total (R$)',
                                'Nº - Faltou', 'Nº - Compareceu', 'Total Agend.',
                                'Planilhas', 'Check',
                            ]
                            # Inclui colunas na ordem definida; appenda extras não mapeadas antes de Check
                            extras  = [c for c in df_g_disp.columns if c not in desired_order]
                            ordered = [c for c in desired_order[:-2] if c in df_g_disp.columns]
                            ordered += [c for c in extras if c not in ordered]
                            ordered += [c for c in desired_order[-2:] if c in df_g_disp.columns]
                            df_g_disp = df_g_disp[ordered]

                        st.dataframe(df_g_disp.style.apply(apply_row_colors, axis=1),
                                     use_container_width=True, height=400, hide_index=True)
                except Exception as e:
                    st.warning(f"Não foi possível exibir Output G: {e}")

            # ── Output F — Tabela Oferta × Ocupação × Realizado ──────────────
            st.markdown("---")
            st.subheader(f"📋 Oferta × Ocupação × Realizado — {periodo_label}")
            df_f_disp = df_f_fil.copy()
            df_f_disp['Ano'] = df_f_disp['Ano'].astype(int)
            df_f_disp['Mês'] = df_f_disp['Mês'].map(dict_mes_abrev)
            df_f_disp['Oferta']      = df_f_disp['Oferta'].apply(fmt_num)
            df_f_disp['Ocupação']    = df_f_disp['Ocupação'].apply(fmt_num)
            df_f_disp['Realizado']   = df_f_disp['Realizado'].apply(fmt_num)
            df_f_disp['% Ocupação']  = df_f_disp['% Ocupação'].apply(fmt_pct)
            df_f_disp['% Realizado'] = df_f_disp['% Realizado'].apply(fmt_pct)
            if 'Nutri' in df_f_disp.columns:
                df_f_disp['Nutri'] = df_f_disp['Nutri'].apply(abrev_nutri)
            # Reorder columns for readability
            cols_f_order = ['Ano', 'Mês', 'Nutri', 'Oferta', 'Ocupação', '% Ocupação', 'Realizado', '% Realizado']
            cols_f_order = [c for c in cols_f_order if c in df_f_disp.columns]
            df_f_disp = df_f_disp[cols_f_order].reset_index(drop=True)
            st.dataframe(df_f_disp.style.apply(apply_row_colors, axis=1),
                         use_container_width=True, height=400, hide_index=True)

            # ── Gráfico Mensal ────────────────────────────────────────────────
            st.markdown("---")
            st.subheader("📊 Evolução Mensal — Oferta, Ocupação e Realizado")
            df_h = build_graph_mensal(df_f_fil)
            if not df_h.empty:
                fig_h = grafico_barra_linha(df_h, "Label", f"Oferta, Ocupação e Realizado — {periodo_label}")
                st.plotly_chart(fig_h, use_container_width=True)

            # ── Gráfico por Dia da Semana ─────────────────────────────────────
            st.markdown("---")
            st.subheader("📅 Desempenho por Dia da Semana")
            df_ds = build_graph_dia_semana(df_a_fil, df_d_fil, df_e_fil)
            if not df_ds.empty:
                # Tabela Transposta (padrão da imagem)
                df_ds_tab = preparar_tabela_dia_semana(df_ds)
                st.dataframe(df_ds_tab.style.apply(apply_row_colors, axis=1),
                             use_container_width=True, hide_index=True)
                
                # Gráfico
                fig_ds = grafico_barra_linha(df_ds, "Dia_semana_desc", f"Performance por Dia da Semana — {periodo_label}")
                st.plotly_chart(fig_ds, use_container_width=True)

            # ── Output C — Semanas ───────────────────────────────────────────
            if not df_c.empty:
                st.markdown("---")
                st.subheader(f"📅 Disponibilidade × Ocupação por Semana — {periodo_label}")

                # Prepare display copy with renamed columns
                df_c_work = df_c.copy()
                if 'CHECK' in df_c_work.columns:
                    df_c_work = df_c_work.rename(columns={'CHECK': 'Tipo'})

                # Set index on Semana_label if it's a column, else keep as-is
                if 'Semana_label' in df_c_work.columns:
                    df_c_fil = df_c_work.set_index('Semana_label')
                elif 'Semana_label' in df_c_work.index.names:
                    df_c_fil = df_c_work
                else:
                    df_c_fil = df_c_work

                # Sort weeks chronologically
                if hasattr(df_c_fil.index, 'map'):
                    sort_keys = {idx: extract_sort_key(idx) for idx in df_c_fil.index}
                    df_c_fil['_sk'] = df_c_fil.index.map(sort_keys)
                    df_c_fil = df_c_fil.sort_values('_sk').drop(columns=['_sk'])

                # Bring Tipo column to front, then TOTAL last
                df_c_display = df_c_fil.copy().reset_index()
                df_c_display = df_c_display.rename(columns={'Semana_label': 'Semana', 'index': 'Semana'})
                nutri_cols = [c for c in df_c_display.columns if c not in ['Semana', 'Tipo', 'TOTAL']]
                # Abbreviate nutri names used as column headers
                nutri_rename = {c: abrev_nutri(c) for c in nutri_cols}
                df_c_display = df_c_display.rename(columns=nutri_rename)
                nutri_cols_abrev = [nutri_rename.get(c, c) for c in nutri_cols]
                col_order = ['Semana', 'Tipo'] + sorted(nutri_cols_abrev) + (['TOTAL'] if 'TOTAL' in df_c_display.columns else [])
                col_order = [c for c in col_order if c in df_c_display.columns]
                df_c_display = df_c_display[col_order]
                st.dataframe(df_c_display.style.apply(apply_row_colors, axis=1),
                             use_container_width=True, height=500, hide_index=True)

            # ── Resumo por Nutricionista ──────────────────────────────────────
            st.markdown("---")
            st.subheader(f"👥 Resumo por Nutricionista — {periodo_label}")
            df_nutri = df_f_fil.groupby('Nutri', as_index=False)[['Oferta','Ocupação','Realizado']].sum()
            df_nutri["% Ocupação"]  = (df_nutri["Ocupação"]  / df_nutri["Oferta"] ).replace([np.inf,np.nan],0)*100
            df_nutri["% Realizado"] = (df_nutri["Realizado"] / df_nutri["Ocupação"]).replace([np.inf,np.nan],0)*100
            df_nutri_d = df_nutri.copy()
            df_nutri_d['Oferta']      = df_nutri_d['Oferta'].apply(fmt_num)
            df_nutri_d['Ocupação']    = df_nutri_d['Ocupação'].apply(fmt_num)
            df_nutri_d['% Ocupação']  = df_nutri_d['% Ocupação'].apply(fmt_pct)
            df_nutri_d['Realizado']   = df_nutri_d['Realizado'].apply(fmt_num)
            df_nutri_d['% Realizado'] = df_nutri_d['% Realizado'].apply(fmt_pct)
            df_nutri_d['Nutri']       = df_nutri_d['Nutri'].apply(abrev_nutri)
            # Reorder: group absolute + percentage together
            cols_nutri_order = ['Nutri', 'Oferta', 'Ocupação', '% Ocupação', 'Realizado', '% Realizado']
            cols_nutri_order = [c for c in cols_nutri_order if c in df_nutri_d.columns]
            df_nutri_d = df_nutri_d[cols_nutri_order]
            st.dataframe(df_nutri_d.reset_index(drop=True).style.apply(apply_row_colors, axis=1),
                         use_container_width=True, height=400, hide_index=True)

            # ── Gráfico ocupação por nutri ────────────────────────────────────
            st.markdown("---")
            st.subheader("👥 Taxa de Ocupação por Nutricionista")
            df_np = df_nutri[df_nutri['Nutri'] != 'TOTAL'].copy()
            df_np["% Horários Vagos"] = 100 - df_np["% Ocupação"]
            df_np = df_np.sort_values("% Ocupação", ascending=True)
            df_np["Nutri"] = df_np["Nutri"].apply(abrev_nutri)
            fig_nutri = go.Figure()
            fig_nutri.add_trace(go.Bar(y=df_np["Nutri"], x=df_np["% Horários Vagos"],
                                        name="% Horários Vagos", orientation='h', marker_color='#eb4524'))
            fig_nutri.add_trace(go.Bar(y=df_np["Nutri"], x=df_np["% Ocupação"],
                                        name="% Ocupação", orientation='h', marker_color='#c3d76b'))
            fig_nutri.update_layout(barmode='stack', height=max(400, len(df_np)*45),
                                     xaxis=dict(range=[0,100]),
                                     legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_nutri, use_container_width=True)


            # ── Downloads ─────────────────────────────────────────────────────
            st.markdown("---")
            st.subheader("💾 Exportar Resultados")
            c1, c2, c3 = st.columns(3)
            with c1:
                xlsx_f = to_excel(df_f, index=False)
                st.download_button("📥 Oferta×Ocupação×Realizado (Excel)", xlsx_f,
                                    f"output_f_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", 
                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            with c2:
                if not df_c.empty:
                    xlsx_c = to_excel(df_c, index=True)
                    st.download_button("📥 Tabela Semanal (Excel)", xlsx_c,
                                        f"output_c_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            with c3:
                if df_g is not None and isinstance(df_g, pd.DataFrame) and not df_g.empty:
                    try:
                        xlsx_g = to_excel(df_g, index=False)
                        st.download_button("📥 Faturamento (Excel)", xlsx_g,
                                            f"output_g_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    except Exception as e:
                        st.caption(f"Export G indisponível: {e}")

            st.markdown("---")
            if st.button("⬅️ Voltar para Carga de Dados"):
                st.session_state.current_step = 1
                st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7f8c8d; padding: 1rem;">
    <strong>Dashboard Mensal — Flua Nutrição</strong><br>
    Análise Mensal: Oferta · Ocupação · Realizado | Versão 4.0 — Firebase
</div>
""", unsafe_allow_html=True)