import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Subito CRM Lorenzo", layout="wide")

# --- CONFIGURAZIONE URL CORRETTO ---
CSV_URL = "https://docs.google.com/spreadsheets/d/1xXydotEJiQUD0GB_2mdtj30_BsyM9WLGfNjYGhUu_pQ/export?format=csv&gid=1944182975"
# URL per il foglio Target (se il GID è diverso, cambialo qui sotto)
TARGET_URL = "https://docs.google.com/spreadsheets/d/1xXydotEJiQUD0GB_2mdtj30_BsyM9WLGfNjYGhUu_pQ/export?format=csv&gid=1086208035" 

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines='skip')
        data.columns = data.columns.str.strip()
        return data
    except:
        return pd.DataFrame()

st.title("🚀 Subito CRM - Dashboard Lorenzo")

df = load_data(CSV_URL)

if not df.empty:
    # Pulizia importi
    df['importo'] = pd.to_numeric(df['importo'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    # Calcolo Fatturato
    total_fatturato = df['importo'].sum()
    
    # Caricamento Target (se fallisce mette 100k)
    target_df = load_data(TARGET_URL)
    try:
        target_semestrale = float(target_df['Target_Semestrale'].iloc[0])
    except:
        target_semestrale = 100000.0

    percentuale = total_fatturato / target_semestrale if target_semestrale > 0 else 0

    # --- UI DASHBOARD ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Fatturato Reale", f"€ {total_fatturato:,.2f}")
    col2.metric("Target Semestrale", f"€ {target_semestrale:,.2f}")
    col3.metric("Raggiungimento", f"{percentuale:.1%}")
    st.progress(min(percentuale, 1.0))

    # --- GRAFICI ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if 'tipologia prodotto' in df.columns:
            fig_prod = px.pie(df, values='importo', names='tipologia prodotto', title="Fatturato per Prodotto")
            st.plotly_chart(fig_prod, use_container_width=True)
    with c2:
        if 'mese inserimento' in df.columns:
            fig_mese = px.bar(df, x='mese inserimento', y='importo', color='tipologia prodotto', title="Trend Mensile", barmode='group')
            st.plotly_chart(fig_mese, use_container_width=True)

    st.divider()
    st.subheader("📋 Ultime 10 Vendite")
    st.dataframe(df.tail(10))

else:
    st.error("Impossibile leggere i dati. Verifica che il foglio sia 'Pubblicato sul Web' in formato CSV.")
