import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Subito CRM Lorenzo", layout="wide")

DB_URL = "https://docs.google.com/spreadsheets/d/1xXydotEJiQUD0GB_2mdtj30_BsyM9WLGfNjYGhUu_pQ/export?format=csv&gid=1944182975"
TARGET_URL = "https://docs.google.com/spreadsheets/d/1xXydotEJiQUD0GB_2mdtj30_BsyM9WLGfNjYGhUu_pQ/export?format=csv&gid=1398752677"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines='skip')
        data.columns = data.columns.str.strip() # Rimuove spazi dai nomi colonne
        return data
    except:
        return pd.DataFrame()

df = load_data(DB_URL)
target_df = load_data(TARGET_URL)

st.title("🚀 Subito CRM - Dashboard Lorenzo")

if not df.empty:
    # --- PULIZIA IMPORTI (Rimuove €, spazi e punti delle migliaia) ---
    def clean_currency(x):
        if isinstance(x, str):
            return x.replace('€', '').replace('.', '').replace(',', '.').strip()
        return x

    df['importo'] = df['importo'].apply(clean_currency)
    df['importo'] = pd.to_numeric(df['importo'], errors='coerce').fillna(0)
    
    total_fatturato = df['importo'].sum()
    
    # --- LOGICA TARGET FLESSIBILE ---
    target_semestrale = 100000.0 # Default
    if not target_df.empty:
        target_df.columns = target_df.columns.str.strip()
        # Cerca una colonna che contenga la parola 'Target' indipendentemente dal nome esatto
        target_cols = [c for c in target_df.columns if 'Target' in c]
        if target_cols:
            val = target_df[target_cols[0]].iloc[0]
            target_semestrale = pd.to_numeric(clean_currency(val), errors='coerce') or 100000.0

    percentuale = total_fatturato / target_semestrale if target_semestrale > 0 else 0

    # --- KPI ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Fatturato Reale", f"€ {total_fatturato:,.2f}")
    col2.metric("Target Semestrale", f"€ {target_semestrale:,.2f}")
    col3.metric("Raggiungimento", f"{percentuale:.1%}")
    st.progress(min(percentuale, 1.0))

    # --- GRAFICI ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        # Usiamo 'tipologia prodotto' (strip per sicurezza)
        df.columns = df.columns.str.strip()
        if 'tipologia prodotto' in df.columns:
            fig_prod = px.pie(df, values='importo', names='tipologia prodotto', title="Mix Prodotti")
            st.plotly_chart(fig_prod, use_container_width=True)
    with c2:
        if 'mese inserimento' in df.columns:
            fig_mese = px.bar(df, x='mese inserimento', y='importo', color='tipologia prodotto', title="Trend Mensile")
            st.plotly_chart(fig_mese, use_container_width=True)

    st.divider()
    st.subheader("📋 Ultime Vendite")
    st.dataframe(df.tail(10))
else:
    st.error("Dati non caricati. Controlla la pubblicazione del foglio Google.")
