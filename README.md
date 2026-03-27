# Flua Nutrição — Dashboard de Disponibilidade e Ocupação

Plataforma de Business Intelligence (BI) para gestão e análise de produtividade de equipes de nutricionistas. Acompanha oferta de horários, ocupação de agendas e desempenho financeiro, com backend persistente no **Google Firebase Firestore**.

---

## 🚀 Funcionalidades

### Dashboard Semanal (`app.py`)
- **Upload de Dados:** Processamento de planilhas de disponibilidade (Optum) e agenda ocupada.
- **KPIs Principais:** Oferta Total, Ocupação Total, Taxa de Ocupação e Faturamento.
- **Metas Financeiras:** Cálculo de ponto de equilíbrio baseado em custos, impostos e valor por consulta.
- **Gráficos Interativos:** Comparativo semanal de Oferta vs. Ocupação.

### Dashboard Mensal (`app_mensal.py`)
- **Seção 1 — Carga de Dados:** Permite carregar arquivos (Inputs A/D/E) para uma competência (Mês/Ano).
  - 🔄 **Independência de Arquivos:** O usuário pode enviar apenas os arquivos que tiver disponíveis em mãos em um dado momento (não é mais obrigatório enviar Input A e D juntos).
  - 📥 **Atualização Incremental:** Se o período já existe no banco, o sistema faz o merge dos dados novos com os já existentes, sobrescrevendo apenas o que foi enviado (ex: carregar só o Controle E sem perder o A e D originais).
- **Seção 2 — Dashboard:** Visualização direta do Firestore com suporte a **Range de Datas** (ex: ver Jan a Mar de uma vez).
- **KPIs Customizados:** Cards HTML modernos com indicadores de ocupação, realização e faturamento.
- **Exportação Excel:** Downloads de tabelas agora em formato **.xlsx** (Excel) com botões estilizados.
- **Gráficos Otimizados:** Evolução mensal com eixos inteligentes que evitam sobreposição visual de barras e linhas.

---

## 🛠️ Tecnologias Utilizadas

| Categoria | Tecnologia |
|---|---|
| Linguagem | Python 3.x |
| Framework Web | [Streamlit](https://streamlit.io/) |
| Banco de Dados | [Google Firebase Firestore](https://firebase.google.com/) (NoSQL) |
| Análise de Dados | Pandas, NumPy |
| Visualização | Plotly (Express & Graph Objects) |
| Interface | CSS customizado |

---

## 📋 Pré-requisitos

1. **Python 3.10+** instalado.
2. **Conta no Firebase** com projeto criado e Firestore habilitado.
3. **Service Account Key** (`serviceAccountKey.json`) na raiz do projeto.  
   → Obtida em: *Firebase Console → Configurações do Projeto → Contas de serviço → Gerar nova chave privada*

> ⚠️ O arquivo `serviceAccountKey.json` está no `.gitignore` e **nunca deve ser comitado**.

---

## 🔧 Instalação

```bash
# 1. Criar e ativar ambiente virtual (recomendado)
python -m venv venv
.\venv\Scripts\activate        # Windows
source venv/bin/activate       # Linux/macOS

# 2. Instalar dependências
pip install -r requirements.txt
```

---

## 💻 Como Executar

```bash
# Dashboard Semanal
streamlit run app.py

# Dashboard Mensal (com backend Firebase)
streamlit run app_mensal.py
```

---

## 📥 Carga Histórica

Para popular o banco com dados históricos pela primeira vez, use o script `bulk_loader.py`:

```bash
python bulk_loader.py
```

**Arquivos fonte esperados em `data/mensal/`:**

| Input | Arquivo | Aba |
|---|---|---|
| A — Oferta | `06 Histórico Extração Optum Tratada.xlsx` | `Oferta` |
| D — Sessões | `06 Histórico Extração Optum Tratada.xlsx` | `Banco Optum tratado` |
| E — Controles | `02 Controle de atendimentos_*.xlsx` | `Controle atendimentos` |

O script:
- Detecta todos os períodos disponíveis nos arquivos
- Verifica duplicatas no Firestore (pergunta antes de sobrescrever)
- Processa e salva os outputs (C, F, G) mês a mês
- Gera um **log de auditoria JSON** automático em `logs/carga/`

---

## 📂 Estrutura do Projeto

```text
├── app.py                    # Dashboard de visão semanal
├── app_mensal.py             # Dashboard mensal com backend Firebase
├── firebase_config.py        # Inicialização singleton do Firebase Admin SDK
├── data_loader.py            # Camada de acesso ao Firestore (CRUD + chunking)
├── bulk_loader.py            # Script de carga histórica em lote
├── requirements.txt          # Dependências do projeto
├── serviceAccountKey.json    # ⚠️ NÃO COMMITAR — credencial Firebase (no .gitignore)
├── data/
│   └── mensal/               # Arquivos Excel fonte para carga histórica
├── logs/
│   └── carga/                # Logs de auditoria de execuções do bulk_loader (JSON)
├── images/                   # Ativos visuais (logos, ícones)
├── scripts/                  # Scripts auxiliares
└── sandbox/                  # Ambiente de testes
```

---

### 📤 Carga Histórica e Bulk Loader
O script `bulk_loader.py` foi projetado para automação inicial e suporte a múltiplas profissionais:
- **Busca Dinâmica:** Detecta automaticamente todos os arquivos que seguem o padrão `02 Controle de atendimentos_*.xlsx` na pasta `data/mensal/`.
- **Escalabilidade:** Suporta a inclusão de novas nutricionistas apenas adicionando seus arquivos à pasta, sem necessidade de alteração no código.
- **Log de Auditoria:** Cada execução gera um relatório detalhado em `logs/carga/` com o status de cada período e contagem de registros.

---

## 🗄️ Estrutura do Firestore e Robustez

```text
periodos_mensal/              ← Collection principal
  └── "2025_03"               ← Document ID: YYYY_MM
        ├── ano, mes, data_upload
        ├── custo_nutri_mes, impostos, valor_consulta
        └── dados/            ← Sub-collection
              ├── input_a     ← Oferta (disponibilidade)
              ├── input_d     ← Sessões Optum
              ├── input_e     ← Controles manuais (Todas as Nutris)
              ├── output_c    ← Tabela semanal Oferta × Ocupação
              ├── output_f    ← Resumo Consolidado por Profissional
              └── output_g    ← Faturamento por status de sessão
```

Os dados são armazenados de forma otimizada:
- **Chunking Automático:** Para evitar o limite de 1MB do Firestore em meses com muitos dados, o sistema divide automaticamente os documentos em partes (`_part2`, `_part3`, etc) e as recompõe na leitura de forma transparente.
- **Cache de Performance:** O dashboard utiliza `st.cache_data` para minimizar leituras no banco e acelerar a troca de períodos.

---

## 🎨 Identidade Visual

| Cor | Hex | Uso |
|---|---|---|
| Marinho/Petróleo | `#044851` | Cabeçalhos, KPIs e Botões Primários |
| Turquesa | `#66cbdd` | Oferta e destaques |
| Verde Excel | `#1d6f42` | Bordas e Hover dos botões de exportação |
| Verde Limão | `#c3d76b` | Sucesso e Realização |
| Laranja/Vermelho | `#eb4524` | Alertas e Horários Vagos |

---

Desenvolvido para **Flua Nutrição**.
