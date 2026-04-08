---
description: Arquivo de regras, domínio e debug do projeto Flua Nutrição Mensal
trigger: always_on
---

# 🧠 GEMINI.md - Escopo Flua Nutrição Mensal

Este documento centraliza as regras de negócio cruciais, armadilhas comuns (gotchas), estrutura do banco de dados e fluxos de dados do aplicativo **Flua Nutrição - Dashboard Mensal**.
> 🔴 **MANDATORY**: Ao atuar na manutenção deste projeto (adicionar features, debugar falhas ou alterar o ETL), leia as regras abaixo ANTES de mexer nos cálculos de cruzamento de dados.

---

## 🏗️ 1. Arquitetura do Projeto

O projeto é dividido em processos de Carga (ETL) e Visualização Frontend via Streamlit conectando-se no Firebase (Firestore).

- **`app_mensal.py`**: O painel interativo. Contém a interface em Streamlit, mas também lida com o parse *em memória* dos formulários enviados na "Seção 1". Ele persiste os DFs resultantes direto no Firebase.
- **`bulk_loader.py`**: O script utilitário rodado via terminal localmente para massificar uma carga histórica limpa lendo os binários das pastas `/data/mensal/`. Deve sempre espelhar as lógicas de ETL exatas descritas nas funções de parsing do `app_mensal.py`.
- **`data_loader.py`**: Interage com o Firebase para listar períodos, salvar os lotes mensais e requisitar os documentos pro frontend da "Seção 2".

---

## 📊 2. Regras de Negócio e Dados (O ETL)

O sistema lida com o cruzamento de relatórios da operação da coordenação vs. planilhas manuais das Nutricionistas. 

### Matriz de Fontes da Verdade (Source of Truth)

1. **Input A (Oferta)**
   - **Origem**: Arquivo Optum Tratada (Aba "Oferta").
   - **Função**: Determinar o total de *Janelas* e horas disponibilizadas pelos profissionais.
2. **Input D (Banco Optum Tratado)**
   - **Origem**: Arquivo Optum Tratada (Aba "Banco Optum tratado").
   - **Função**: Contém o tracking dos agendamentos oficiais do benefício.
   - > 🎯 **Source of Truth**: É de onde calculamos as métricas de **Ocupação** e **Realizado** (onde Status sessão == "Compareceu ao atendimento").
   - > ⚠️ **CRÍTICO - Faturamento**: A coluna `Valor atendimento` ou `Valor Unitário` do Input D é a **ÚNICA** fonte da verdade para o Faturamento. O Input E (da Nutri) NUNCA ditará valor em Reais a ser pago nos outputs F e G.
3. **Input E (Controle das Nutris)**
   - **Origem**: Multiplos relatórios preenchidos pelas nutricionistas (`Controle atendimentos...xlsx`).
   - **Função**: **Auditoria e Batimento**. Serve para conferir se o que a nutricionista registrou em sua planilha individual condiz com os agendamentos registrados no Banco Optum (Input D).
   - > 📊 **Check**: Gera a coluna "Check" e "Planilhas" no Output G, mas não é a base para o KPI primário de Realizados.

---

## 🪤 3. Armadilhas e Manutenção (Gotchas)

### 3.1 Cabeçalhos "Sujos" no Excel
Muitas falhas "misteriosas" de conversão para 0 nos resultados de faturamento e ocupação vêm da exportação ruidosa do Excel da coordenação:

> Os relatórios do Optum costumam vir com **espaços em branco nas extremidades ou quebras de linha**.
Exemplo do mundo real: `"Valor atendimento "` ou `"Status atendimento \n (Realizado...)"`

**🛠️ A Regra Obrigatória da Limpeza:**
Todo script de Parse (tanto do `bulk_loader.py` quanto de uploads em `app_mensal.py`) deve aplicar um regex profundo nos cabeçalhos recém importados:
```python
# OBRIGATÓRIO: Remover \n, tabulações, duplo espaço e limpar bordas.
df.columns = df.columns.astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
```
Nunca utilize apenas `df.columns.str.strip()` caso a string contenha newlines `\n` internos.

### 3.2 KeyErrors de Planilhas Inexistentes (DataFrame Vazio)
Ao rodar agrupamentos do Pandas em dicionários de dados mesclados, sempre preveja que pode haver meses em que as Nutris "esqueceram" de subir o Input E ou que não rodamos dados operacionais para aquela pessoa.
- Antes de um `.groupby` sobre um DF, sempre valide `if not df_e_mes.empty:` ou retorne dataframes simulados vazios `pd.DataFrame(columns=[...])`.

### 3.3 Lógica da Coluna Check (Auditoria D vs E)
A coluna `Check` no Output G é a principal ferramenta de integridade de dados.
- **Cálculo**: `Total Agendamentos (Input D) == Contagem de IDs (Input E)`.
- Se os valores divergirem, o sistema exibirá `⚠️ Not OK`. Isso geralmente indica que a Nutri esqueceu de registrar um atendimento em sua planilha pessoal ou que há um erro na extração do Optum.
- **Paridade**: Esta lógica deve ser idêntica tanto no `app_mensal.py` quanto no `bulk_loader.py`.

---

## 🔥 4. Estrutura do Firebase Firestore

Os dados são ingeridos na nuvem de modo a simplificar o consumo do web-app.

- **Coleção Raiz:** Organizada ano a ano. Ex: `mensal_2024`, `mensal_2025`, `mensal_2026`.
- **Nomes de Documento:** Padrão mês e ano. Ex: `02-2026`, `09-2024`.
- **Formato Interno (JSON / dicts):**
  - Raiz: `arquivos`, `custo_nutri_mes`, `impostos`, `valor_consulta`
  - Tabelas de Dados (Convertidas com orient='records' pelo Pandas):
    - `input_a`, `input_d`, `input_e` (Bases em modo raw table com a semana computada)
    - `output_c` (Comparecimento Nutris vs Geral)
    - `output_f` (Taxas convertidas Oferta vs Ocupação vs Realizado e seus percentuais)
    - `output_g` (Resumo Tabela de Faturamento R$, cruzando contagem de status do Input E vs Agendamento Optum e exibindo checagem emoji de auditoria das planilhas das Nutris)

---

## 🎨 5. Design e Interface (UI)

O aplicativo preza por uma estética **Premium** e **Moderna**, distanciando-se do layout padrão do Streamlit através de CSS customizado.

### 5.1 KPI Cards Customizados
Em vez do `st.metric`, o dashboard utiliza uma função helper `kpi_card` que gera HTML/CSS para exibir indicadores.
- **Flexbox**: Os cards são organizados em um container `.kpi-wrapper` com `display: flex`. Isso permite um grid responsivo e alinhamento superior ao sistema de colunas nativo.
- **Tematização**: O uso de **CSS Custom Properties** (ex: `--card-color`) permite que cada card tenha uma cor de acento associada ao seu significado (ex: Verde para "Realizado", Amarelo para "Atenção/Ocupação").
- **Visual Excellence**: Qualquer nova métrica de destaque deve seguir este padrão para manter a "Wow Experience" do usuário.
