import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
from PIL import Image

# Configuração da página
try:
    logo_icon = Image.open("images/flua-logo.png")
    st.set_page_config(
        page_title="Dashboard - Disponibilidade Nutricionistas",
        page_icon=logo_icon,
        layout="wide"
    )
except:
    st.set_page_config(
        page_title="Dashboard - Disponibilidade Nutricionistas",
        page_icon="📊",
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

    .metric-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 4px solid #66cbdd;
    }

    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 1rem;
        border: none;
    }
    .stButton>button[kind="primary"] {
        background-color: #044851 !important;
        color: white !important;
    }
    .stButton>button[kind="secondary"] {
        background-color: #66cbdd20 !important;
        color: #044851 !important;
        border: 1px solid #66cbdd55 !important;
    }
    .stButton>button:hover {
        opacity: 0.85;
    }

    /* Estilo para tabelas com linhas alternadas */
    .dataframe tbody tr:nth-child(odd) {
        background-color: #ffffff !important;
    }
    .dataframe tbody tr:nth-child(even) {
        background-color: #e8f7fa !important;
    }
    .dataframe tbody tr:hover {
        background-color: #d0ecf1 !important;
    }
    
    /* Aumentar tamanho da fonte em tabelas */
    .dataframe {
        font-size: 1.3rem !important;
    }
    
    /* Negrito para dados de tabela */
    .dataframe tbody td {
        font-weight: 600 !important;
    }
    
    /* Headers de tabela */
    .dataframe thead th {
        font-size: 1.4rem !important;
        font-weight: bold !important;
        background-color: #044851 !important;
        color: white !important;
    }
    
    /* Labels maiores nos KPIs */
    .stMetric label {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: bold !important;
    }

</style>
""", unsafe_allow_html=True)

# Funções auxiliares do ETL
def label_semana(df):
    """Adiciona rótulos de semana ao DataFrame"""
    s = df["Data"]
    mask = s.notna()

    m_ini = s.dt.to_period("M").dt.start_time
    m_fim = (m_ini + pd.offsets.MonthEnd(0))

    week_mon = s - pd.to_timedelta(s.dt.weekday, unit="D")
    week_sun = week_mon + pd.Timedelta(days=6)

    week_start = week_mon.where(week_mon >= m_ini, m_ini)
    week_end = week_sun.where(week_sun <= m_fim, m_fim)

    mes_abrev = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
                7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}

    w0 = m_ini.dt.weekday
    week_in_month = ((s.dt.day + w0 - 1) // 7 + 1).astype("Int64")

    label = pd.Series(pd.NA, index=s.index, dtype="string")
    label[mask] = (
        s[mask].dt.month.astype(str)
        + " " +
        s[mask].dt.month.map(mes_abrev)
        + " - Sem " + week_in_month[mask].astype(str)
        + " - " + week_start[mask].dt.day.astype(str).str.zfill(2)
        + " a " + week_end[mask].dt.day.astype(str).str.zfill(2)
    )

    df["Semana_mes"] = week_in_month
    df["Semana_label"] = label
    df["Mes_num"] = s.dt.month
    df["Mes_nome"] = s.dt.month.map(mes_abrev)
    return df

def processar_disponibilidade(df):
    """Processa dados de disponibilidade"""
    dict_mes = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho',
                7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}
    
    df_trd = pd.DataFrame(columns=['Data completa', 'Ano', 'Mês', 'Mês_Ano', 'DDS', 'Início', 'Fim', 'Total horas', 'Janelas','Nutri'])
    df_trd['Data completa'] = df['HORA INICIAL'].copy()
    df_trd["Data"] = df_trd["Data completa"].str.split(" -").str[0]
    df_trd["Data"] = pd.to_datetime(df_trd["Data"], format="%d/%m/%Y", errors="coerce")
    df_trd['Ano'] = df_trd["Data"].dt.year
    df_trd['Mês_num'] = df_trd["Data"].dt.month
    df_trd['Mês'] = df_trd['Mês_num'].map(dict_mes)
    df_trd['Mês_Ano'] = df_trd['Mês'] + df_trd['Ano'].astype(str)
    df_trd['DDS'] = df_trd['Data completa'].str[-3:]
    df_trd['Início'] = df['HORA FINAL'].copy()
    df_trd["Início"] = pd.to_datetime(df_trd["Início"], format="%H:%M:%S", errors="coerce")
    df_trd['Fim'] = df['HORAS TOTAIS'].copy()
    df_trd["Fim"] = pd.to_datetime(df_trd["Fim"], format="%H:%M:%S", errors="coerce")
    df_trd["Total horas"] = (df_trd["Fim"] - df_trd["Início"])
    df_trd["Total horas"] = df_trd["Total horas"].apply(lambda x: str(x).split(" days ")[-1] if pd.notnull(x) else None)
    df_trd["Janelas"] = (df_trd["Fim"] - df_trd["Início"]).dt.total_seconds() / 3600
    df_trd["Janelas"] = df_trd["Janelas"].astype(int)
    df_trd["Início"] = df_trd["Início"].dt.time
    df_trd["Fim"] = df_trd["Fim"].dt.time
    df_trd['Nutri'] = df['Unnamed: 6'].copy()
    df_trd.drop(columns=['Mês_num'], inplace=True)
    
    return label_semana(df_trd)

def processar_ocupacao(df):
    """Processa dados de ocupação"""
    df_trd = df.copy()
    df_trd.rename(columns={'DATA':'Data completa', 'RESPONSÁVEL':'Nutri'}, inplace=True)
    df_trd["Data"] = df_trd["Data completa"].str.split(" -").str[0]
    df_trd["Data"] = pd.to_datetime(df_trd["Data"], format="%d/%m/%Y", errors="coerce")
    
    return label_semana(df_trd)

def formatar_numero(num):
    """Formata números com separador de milhar"""
    return f"{int(num):,}".replace(",", ".")

def formatar_valor(valor):
    """Formata valores monetários"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_percentual(valor):
    """Formata percentuais com vírgula como separador decimal"""
    return f"{valor:.1f}%".replace(".", ",")

# Inicializar session state
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
if 'disponibilidade_data' not in st.session_state:
    st.session_state.disponibilidade_data = None
if 'ocupacao_data' not in st.session_state:
    st.session_state.ocupacao_data = None
if 'processed_disponibilidade' not in st.session_state:
    st.session_state.processed_disponibilidade = None
if 'processed_ocupacao' not in st.session_state:
    st.session_state.processed_ocupacao = None
if 'custo_nutri_mes' not in st.session_state:
    st.session_state.custo_nutri_mes = 0
if 'impostos' not in st.session_state:
    st.session_state.impostos = 0
if 'valor_consulta' not in st.session_state:
    st.session_state.valor_consulta = 0
if 'mes_selecionado' not in st.session_state:
    st.session_state.mes_selecionado = None

# Título principal com logo
try:
    col_logo, col_title = st.columns([1, 9])
    with col_logo:
        logo = Image.open("images/flua-logo.png")
        st.image(logo, width=80)
    with col_title:
        st.markdown('<div class="main-header">Dashboard de Disponibilidade - Nutricionistas</div>', unsafe_allow_html=True)
except:
    st.markdown('<div class="main-header">📊 Dashboard de Disponibilidade - Nutricionistas</div>', unsafe_allow_html=True)

st.markdown("### 📅 Análise Semanal de Disponibilidade e Ocupação")

# Navegação
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🗂️ Seção 1: Upload de Arquivos", use_container_width=True, type="primary" if st.session_state.current_step == 1 else "secondary"):
        st.session_state.current_step = 1

with col2:
    if st.button("📈 Seção 2: Processar Dados", use_container_width=True, type="primary" if st.session_state.current_step == 2 else "secondary"):
        st.session_state.current_step = 2

with col3:
    if st.button("📊 Seção 3: Visualizar Resultados", use_container_width=True, type="primary" if st.session_state.current_step == 3 else "secondary"):
        st.session_state.current_step = 3

st.markdown("---")

# SEÇÃO 1: Upload de Arquivos
if st.session_state.current_step == 1:
    st.markdown('<div class="section-header">📁 Seção 1: Upload de Arquivos</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h4>📋 Instruções para Upload</h4>
        <p>Esta seção permite o upload de dois arquivos essenciais para a análise:</p>
        <ul>
            <li><strong>Arquivo 1 - Disponibilidade Optum:</strong> Planilha extraída do sistema com as janelas de disponibilidade das nutricionistas</li>
            <li><strong>Arquivo 2 - Agenda Ocupada:</strong> Planilha com os agendamentos realizados e ocupação das janelas</li>
        </ul>
        <p>⚠️ <strong>Importante:</strong> Os arquivos devem estar no formato Excel (.xlsx ou .xls) ou CSV (.csv)</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 Arquivo 1: Disponibilidade")
        st.markdown("*Cópia bruta do sistema Optum*")
        disponibilidade_file = st.file_uploader(
            "Carregue o arquivo de disponibilidade",
            type=['csv', 'xlsx', 'xls'],
            key="disp_file",
            help="Arquivo com as janelas de disponibilidade das nutricionistas"
        )
        
        if disponibilidade_file is not None:
            try:
                if disponibilidade_file.name.endswith('.csv'):
                    df_disp = pd.read_csv(disponibilidade_file)
                else:
                    df_disp = pd.read_excel(disponibilidade_file)
                
                st.session_state.disponibilidade_data = df_disp
                st.markdown('<div class="success-box">✅ Arquivo de disponibilidade carregado com sucesso!</div>', unsafe_allow_html=True)
                
                with st.expander("👁️ Ver preview dos dados"):
                    st.dataframe(df_disp.head(10), use_container_width=True)
                    st.metric("Total de Registros", len(df_disp))
                    
            except Exception as e:
                st.error(f"❌ Erro ao carregar arquivo: {str(e)}")
    
    with col2:
        st.subheader("📥 Arquivo 2: Agenda Ocupada")
        st.markdown("*Modelo de agenda ocupada - Visão semanal*")
        ocupacao_file = st.file_uploader(
            "Carregue o arquivo de agenda ocupada",
            type=['csv', 'xlsx', 'xls'],
            key="ocup_file",
            help="Arquivo com os agendamentos realizados"
        )
        
        if ocupacao_file is not None:
            try:
                if ocupacao_file.name.endswith('.csv'):
                    df_ocup = pd.read_csv(ocupacao_file)
                else:
                    df_ocup = pd.read_excel(ocupacao_file)
                
                st.session_state.ocupacao_data = df_ocup
                st.markdown('<div class="success-box">✅ Arquivo de ocupação carregado com sucesso!</div>', unsafe_allow_html=True)
                
                with st.expander("👁️ Ver preview dos dados"):
                    st.dataframe(df_ocup.head(10), use_container_width=True)
                    st.metric("Total de Registros", len(df_ocup))
                    
            except Exception as e:
                st.error(f"❌ Erro ao carregar arquivo: {str(e)}")
    
    st.markdown("---")
    
    # Parâmetros financeiros - ZERADOS por padrão
    st.subheader("💰 Parâmetros Financeiros")
    st.markdown("*Configure os valores para cálculo de metas e faturamento (deixe zerado se não desejar usar)*")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        custo_mes = st.number_input(
            "Custo com Nutricionistas (R$/mês)",
            min_value=0.0,
            value=float(st.session_state.custo_nutri_mes),
            step=1000.0,
            help="Valor total pago às nutricionistas no mês"
        )
        st.session_state.custo_nutri_mes = custo_mes
    
    with col2:
        impostos = st.number_input(
            "Percentual de Impostos (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.impostos),
            step=0.5,
            help="Percentual de impostos sobre o faturamento"
        )
        st.session_state.impostos = impostos
    
    with col3:
        valor_consulta = st.number_input(
            "Valor por Consulta (R$)",
            min_value=0.0,
            value=float(st.session_state.valor_consulta),
            step=1.0,
            help="Valor recebido por cada consulta realizada"
        )
        st.session_state.valor_consulta = valor_consulta
    
    # Botão para avançar
    st.markdown("---")
    if st.session_state.disponibilidade_data is not None and st.session_state.ocupacao_data is not None:
        if st.button("➡️ Avançar para Processamento", type="primary", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
    else:
        st.markdown('<div class="warning-box">⚠️ Por favor, carregue ambos os arquivos para continuar</div>', unsafe_allow_html=True)

# SEÇÃO 2: Processamento
elif st.session_state.current_step == 2:
    st.markdown('<div class="section-header">⚙️ Seção 2: Processamento de Dados</div>', unsafe_allow_html=True)
    
    if st.session_state.disponibilidade_data is None or st.session_state.ocupacao_data is None:
        st.warning("⚠️ Arquivos não carregados. Por favor, volte à Seção 1.")
        if st.button("⬅️ Voltar para Upload"):
            st.session_state.current_step = 1
            st.rerun()
    else:
        st.markdown("""
        <div class="info-box">
            <h4>🔄 Sobre o Processamento</h4>
            <p>O sistema irá processar os dados automaticamente realizando:</p>
            <ul>
                <li>✅ Formatação de datas e horários</li>
                <li>✅ Cálculo de janelas de atendimento</li>
                <li>✅ Organização por semanas do mês</li>
                <li>✅ Consolidação de disponibilidade e ocupação</li>
                <li>✅ Cálculo de métricas e KPIs</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Iniciar Processamento", type="primary", use_container_width=True):
            with st.spinner("⏳ Processando dados..."):
                try:
                    # Processar disponibilidade
                    df_disp_proc = processar_disponibilidade(st.session_state.disponibilidade_data)
                    st.session_state.processed_disponibilidade = df_disp_proc
                    
                    # Processar ocupação
                    df_ocup_proc = processar_ocupacao(st.session_state.ocupacao_data)
                    st.session_state.processed_ocupacao = df_ocup_proc
                    
                    st.success("✅ Dados processados com sucesso!")
                        
                except Exception as e:
                    st.error(f"❌ Erro no processamento: {str(e)}")
        
        # Mostrar preview se já processado
        if st.session_state.processed_disponibilidade is not None and st.session_state.processed_ocupacao is not None:
            st.markdown("---")
            st.success("✅ Dados já processados!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Disponibilidade Processada")
                st.dataframe(st.session_state.processed_disponibilidade.head(), use_container_width=True)
            
            with col2:
                st.subheader("📊 Ocupação Processada")
                st.dataframe(st.session_state.processed_ocupacao.head(), use_container_width=True)
            
            st.markdown("---")
            if st.button("➡️ Avançar para Resultados", type="primary", use_container_width=True):
                st.session_state.current_step = 3
                st.rerun()
        
        st.markdown("---")
        if st.button("⬅️ Voltar para Upload"):
            st.session_state.current_step = 1
            st.rerun()

# SEÇÃO 3: Resultados
elif st.session_state.current_step == 3:
    st.markdown('<div class="section-header">📊 Seção 3: Dashboard de Disponibilidade</div>', unsafe_allow_html=True)
    
    if st.session_state.processed_disponibilidade is None or st.session_state.processed_ocupacao is None:
        st.warning("⚠️ Dados não processados. Por favor, complete as etapas anteriores.")
        if st.button("⬅️ Voltar para Processamento"):
            st.session_state.current_step = 2
            st.rerun()
    else:
        df_disp = st.session_state.processed_disponibilidade
        df_ocup = st.session_state.processed_ocupacao
        
        # Filtro de mês (se houver mais de 1 mês nos dados)
        meses_disponiveis = sorted(df_disp['Mes_num'].dropna().unique())
        if len(meses_disponiveis) > 1:
            meses_nomes = df_disp.groupby('Mes_num')['Mes_nome'].first().to_dict()
            opcoes_meses = ["Todos os meses"] + [f"{meses_nomes[m]} ({m})" for m in meses_disponiveis]
            
            mes_selecionado = st.selectbox(
                "🗓️ Selecione o período:",
                opcoes_meses,
                key="filtro_mes",
                help="Filtre os dados por mês específico ou visualize todos os meses disponíveis"
            )
            
            if mes_selecionado != "Todos os meses":
                mes_num = int(mes_selecionado.split("(")[1].split(")")[0])
                df_disp = df_disp[df_disp['Mes_num'] == mes_num]
                df_ocup = df_ocup[df_ocup['Mes_num'] == mes_num]
                periodo_label = mes_selecionado.split(" (")[0]
            else:
                periodo_label = "Todos os meses"
        else:
            periodo_label = df_disp['Mes_nome'].iloc[0] if len(df_disp) > 0 else "Mês atual"
        
        # Criar tabela consolidada
        df_output = df_disp.pivot_table(
            index='Semana_label',
            columns='Nutri',
            values='Janelas',
            aggfunc='sum',
            fill_value=0,
            dropna=False
        )
        df_output['TOTAL'] = df_output.sum(axis=1)
        df_output['CHECK'] = 'Oferta'
        
        tb_temp = df_ocup.pivot_table(
            index='Semana_label',
            columns='Nutri',
            values='CASO',
            aggfunc='count',
            fill_value=0,
            dropna=False
        )
        tb_temp['TOTAL'] = tb_temp.sum(axis=1)
        tb_temp['CHECK'] = 'Ocupação'
        
        df_output = pd.concat([df_output, tb_temp])
        
        # Organizar colunas: CHECK, nutricionistas (alfabética), TOTAL
        cols = list(df_output.columns)
        col_check = ['CHECK']
        col_total = ['TOTAL']
        middle_cols = [c for c in cols if c not in ['CHECK', 'TOTAL']]
        middle_cols_sorted = sorted(middle_cols)
        new_order = col_check + middle_cols_sorted + col_total
        df_output = df_output[new_order]
        df_output = df_output.fillna(0)
        df_output[middle_cols_sorted + col_total] = df_output[middle_cols_sorted + col_total].astype(int)
        df_output = df_output.sort_index()
        
        # KPIs principais
        st.subheader("📈 KPIs Principais")
        
        df_semana = df_output.pivot_table(
            index="Semana_label",
            columns="CHECK",
            values="TOTAL",
            aggfunc="sum",
            fill_value=0
        )
        
        for col in ["Oferta", "Ocupação"]:
            if col not in df_semana.columns:
                df_semana[col] = 0
        
        oferta_total = df_semana['Oferta'].sum()
        ocupacao_total = df_semana['Ocupação'].sum()
        taxa_ocupacao = (ocupacao_total / oferta_total * 100) if oferta_total > 0 else 0
        
        # Calcular meta
        if st.session_state.custo_nutri_mes > 0 and st.session_state.valor_consulta > 0:
            meta_agendamento = np.ceil(
                st.session_state.custo_nutri_mes * 
                (1 + (st.session_state.impostos/100)) / 
                st.session_state.valor_consulta
            )
        else:
            meta_agendamento = 0
        
        faturamento = ocupacao_total * st.session_state.valor_consulta if st.session_state.valor_consulta > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Oferta Total",
                f"{formatar_numero(oferta_total)} janelas",
                help="Total de janelas disponíveis no período"
            )
        
        with col2:
            st.metric(
                "Ocupação Total",
                f"{formatar_numero(ocupacao_total)} agendas",
                help="Total de agendamentos realizados"
            )
        
        with col3:
            st.metric(
                "Taxa de Ocupação",
                formatar_percentual(taxa_ocupacao),
                delta=formatar_percentual(taxa_ocupacao - 80) if taxa_ocupacao >= 80 else formatar_percentual(taxa_ocupacao - 80),
                delta_color="normal" if taxa_ocupacao >= 80 else "inverse",
                help="Percentual de janelas ocupadas (meta: 80%)"
            )
        
        with col4:
            st.metric(
                "Faturamento",
                formatar_valor(faturamento),
                delta=formatar_valor(faturamento - (meta_agendamento * st.session_state.valor_consulta)) if meta_agendamento > 0 else None,
                help="Faturamento total do período"
            )
        
        # Meta mensal (só exibe se os parâmetros financeiros estiverem preenchidos)
        if meta_agendamento > 0:
            st.markdown("---")
            st.subheader("🎯 Meta de Agendamentos")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Meta Agendamentos", 
                    formatar_numero(meta_agendamento),
                    help=f"Meta calculada com base no custo mensal (R$ {formatar_numero(st.session_state.custo_nutri_mes)}), impostos ({st.session_state.impostos}%) e valor por consulta (R$ {st.session_state.valor_consulta:.2f})"
                )
            
            with col2:
                st.metric("Realizado", formatar_numero(ocupacao_total))
            
            with col3:
                diferenca = meta_agendamento - ocupacao_total
                st.metric(
                    "Faltam para a Meta",
                    formatar_numero(abs(diferenca)),
                    delta=f"{(ocupacao_total/meta_agendamento*100):.1f}% da meta",
                    delta_color="normal" if diferenca <= 0 else "inverse"
                )
        
        # TABELA DETALHADA - MOVIDA PARA CIMA (logo após KPIs)
        st.markdown("---")
        st.subheader(f"📋 Tabela Detalhada - {periodo_label}")
        
        # Simplificar tabela detalhada
        df_output_simplified = df_output.copy()
        df_output_simplified.index.name = "Semana"
        
        # Renomear coluna CHECK para Tipo
        df_output_simplified = df_output_simplified.rename(columns={'CHECK': 'Tipo'})
        
        # Formatar números
        for col in middle_cols_sorted + col_total:
            df_output_simplified[col] = df_output_simplified[col].apply(lambda x: formatar_numero(x))
        
        st.dataframe(df_output_simplified, use_container_width=True, height=500)
        
        # Tabela resumida por nutricionista
        st.markdown("---")
        st.subheader(f"👥 Resumo por Nutricionista - {periodo_label}")
        
        oferta_nutri = df_output[df_output["CHECK"] == "Oferta"].drop(columns=["CHECK"])
        ocupacao_nutri = df_output[df_output["CHECK"] == "Ocupação"].drop(columns=["CHECK"])
        
        oferta_total_nutri = oferta_nutri.sum()
        ocupacao_total_nutri = ocupacao_nutri.sum()
        
        percent_ocupacao = (ocupacao_total_nutri / oferta_total_nutri * 100).fillna(0).round(1)
        percent_vago = (100 - percent_ocupacao).round(1)
        
        # Criar DataFrame formatado
        df_percent_nutri = pd.DataFrame({
            "Oferta": oferta_total_nutri.apply(lambda x: formatar_numero(x)),
            "Ocupação": ocupacao_total_nutri.apply(lambda x: formatar_numero(x)),
            "% Ocupação": percent_ocupacao.apply(formatar_percentual),
            "% Horários Vagos": percent_vago.apply(formatar_percentual)
        })
        
        st.dataframe(df_percent_nutri, use_container_width=True, height=400)
        
        # Gráfico de ocupação por nutricionista - MOVIDO PARA LOGO ABAIXO
        st.markdown("---")
        st.subheader("👥 Taxa de Ocupação por Nutricionista")
        
        # Recalcular valores numéricos para o gráfico
        percent_ocupacao_numeric = (ocupacao_total_nutri / oferta_total_nutri * 100).fillna(0).round(1)
        percent_vago_numeric = (100 - percent_ocupacao_numeric).round(1)
        
        df_nutri_plot = pd.DataFrame({
            "Nutricionista": percent_ocupacao_numeric.index,
            "% Ocupação": percent_ocupacao_numeric.values,
            "% Horários Vagos": percent_vago_numeric.values
        })
        
        # Remover TOTAL do gráfico
        df_nutri_plot = df_nutri_plot[df_nutri_plot["Nutricionista"] != "TOTAL"]
        df_nutri_plot = df_nutri_plot.sort_values("% Ocupação", ascending=False)
        
        fig_nutri = go.Figure()
        
        fig_nutri.add_trace(go.Bar(
            y=df_nutri_plot["Nutricionista"],
            x=df_nutri_plot["% Horários Vagos"],
            name="% Horários Vagos",
            orientation='h',
            marker_color='#eb4524'
        ))
        
        fig_nutri.add_trace(go.Bar(
            y=df_nutri_plot["Nutricionista"],
            x=df_nutri_plot["% Ocupação"],
            name="% Ocupação",
            orientation='h',
            marker_color='#c3d76b'
        ))
        
        fig_nutri.update_layout(
            barmode='stack',
            title='Distribuição de Ocupação por Nutricionista',
            xaxis_title='Percentual (%)',
            yaxis_title='Nutricionista',
            height=max(400, len(df_nutri_plot) * 40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(range=[0, 100])
        )
        
        st.plotly_chart(fig_nutri, use_container_width=True)
        
        # Tabela resumida por semana
        st.markdown("---")
        st.subheader(f"📅 Resumo por Semana - {periodo_label}")
        
        df_semana_display = df_semana.copy()
        df_semana_display["% de Ocupação"] = (
            df_semana_display["Ocupação"] / df_semana_display["Oferta"]
        ).replace([np.inf, np.nan], 0) * 100
        
        df_semana_display["% Horários Vagos"] = 100 - df_semana_display["% de Ocupação"]
        
        # Formatar colunas
        df_semana_display["Oferta"] = df_semana_display["Oferta"].apply(formatar_numero)
        df_semana_display["Ocupação"] = df_semana_display["Ocupação"].apply(formatar_numero)
        df_semana_display["% de Ocupação"] = df_semana_display["% de Ocupação"].apply(formatar_percentual)
        df_semana_display["% Horários Vagos"] = df_semana_display["% Horários Vagos"].apply(formatar_percentual)
        
        # Reorganizar colunas
        df_semana_display = df_semana_display[["Oferta", "Ocupação", "% de Ocupação", "% Horários Vagos"]]
        
        st.dataframe(df_semana_display, use_container_width=True, height=400)
        
        # Gráfico de ocupação semanal
        st.markdown("---")
        st.subheader("📊 Ocupação Semanal")
        
        # Recalcular para valores numéricos
        df_semana_numeric = df_output.pivot_table(
            index="Semana_label",
            columns="CHECK",
            values="TOTAL",
            aggfunc="sum",
            fill_value=0
        )
        
        for col in ["Oferta", "Ocupação"]:
            if col not in df_semana_numeric.columns:
                df_semana_numeric[col] = 0
        
        fig_semana = go.Figure()
        
        fig_semana.add_trace(go.Bar(
            x=df_semana_numeric.index,
            y=df_semana_numeric['Ocupação'],
            name='Ocupação',
            marker_color='#044851'
        ))
        
        fig_semana.add_trace(go.Bar(
            x=df_semana_numeric.index,
            y=df_semana_numeric['Oferta'],
            name='Oferta',
            marker_color='#66cbdd'
        ))
        
        # Adicionar linha de 80% de ocupação
        ocupacao_80 = df_semana_numeric['Oferta'] * 0.8
        fig_semana.add_trace(go.Scatter(
            x=df_semana_numeric.index,
            y=ocupacao_80,
            name='Meta 80% Ocupação',
            mode='lines',
            line=dict(color='#fcc105', width=3, dash='dash')
        ))
        
        fig_semana.update_layout(
            barmode='group',
            title=f'Oferta vs Ocupação por Semana - {periodo_label}',
            xaxis_title='Semana',
            yaxis_title='Quantidade de Janelas',
            height=450,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        st.plotly_chart(fig_semana, use_container_width=True)
        
        # Download dos resultados
        st.markdown("---")
        st.subheader("💾 Exportar Resultados")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv = df_output.to_csv(index=True).encode('utf-8')
            st.download_button(
                label="📥 Download Tabela Completa (CSV)",
                data=csv,
                file_name=f"disponibilidade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            csv_semana = df_semana_display.to_csv(index=True).encode('utf-8')
            st.download_button(
                label="📥 Download Resumo Semanal (CSV)",
                data=csv_semana,
                file_name=f"resumo_semanal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col3:
            csv_nutri = df_percent_nutri.to_csv(index=True).encode('utf-8')
            st.download_button(
                label="📥 Download Análise Nutricionistas (CSV)",
                data=csv_nutri,
                file_name=f"analise_nutri_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Botão para voltar
        st.markdown("---")
        if st.button("⬅️ Voltar para Processamento"):
            st.session_state.current_step = 2
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7f8c8d; padding: 1rem;">
    <strong>Dashboard de Disponibilidade - Nutricionistas</strong><br>
    Análise Semanal | Versão 2.1
</div>
""", unsafe_allow_html=True)