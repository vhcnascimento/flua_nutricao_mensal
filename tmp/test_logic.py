import pandas as pd
import numpy as np

dict_dia_semana = {0:"Seg", 1:"Ter", 2:"Qua", 3:"Qui", 4:"Sex", 5:"Sáb", 6:"Dom"}

def build_graph_dia_semana(df_a, df_d, df_e):
    """Gráfico barras+linha por dia da semana consolidado"""
    a = df_a.copy()
    d = df_d.copy()
    e = df_e.copy() if not df_e.empty else pd.DataFrame()

    for df_ in [a, d, e]:
        if not df_.empty:
            # CORREÇÃO A SER APLICADA:
            df_['Data'] = pd.to_datetime(df_['Data'], errors='coerce')
            
            df_['Dia_semana_cod']  = df_['Data'].dt.weekday
            df_['Dia_semana_desc'] = df_['Dia_semana_cod'].map(dict_dia_semana)

    # ... restante da lógica omitida para o teste de tipo ...
    return a # apenas para ver se passou o .dt

# Simulando erro: Data como STRING (idêntico ao carregamento do Firestore)
df_a_error = pd.DataFrame({
    'Data': ["2025-05-05", "2025-05-06"],
    'Janelas': [10, 20]
})

print("Testando lógica com Datas as Strings (Erro reprodutor)...")
try:
    res = build_graph_dia_semana(df_a_error, pd.DataFrame(), pd.DataFrame())
    print("Sucesso! Conversão automatizada funcionou.")
    print(res[['Data', 'Dia_semana_desc']])
except Exception as e:
    print(f"Falhou! Erro: {e}")
