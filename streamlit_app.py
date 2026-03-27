import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Subito CRM Lorenzo", layout="wide")

# Connessione
conn = st.connection("gsheets", type=GSheetsConnection)

# Lettura dati (Prende l'URL direttamente dai Secrets che abbiamo impostato)
try:
    df = conn.read(worksheet="DB fatturato clienti Lorenzo")
    target_df = conn.read(worksheet="Target")
except Exception as e:
    st.error("Errore di connessione al foglio Google. Verifica i Secrets su Streamlit Cloud.")
    st.stop()

# Pulizia dati
df['importo'] = pd.to_numeric(df['importo'], errors='coerce').fillna(0)

st.title("🚀 Subito CRM - Dashboard Lorenzo")

# --- CALCOLO TARGET E PREMI ---
total_fatturato = df['importo'].sum()

if not target_df.empty and 'Target_Semestrale' in target_df.columns:
    target_semestrale = pd.to_numeric(target_df['Target_Semestrale'].iloc[0], errors='coerce')
else:
    target_semestrale = 100000

percentuale = total_fatturato / target_semestrale if target_semestrale > 0 else 0

# --- KPI PRINCIPALI ---
col1, col2, col3 = st.columns(3)
col1.metric("Fatturato Reale", f"€ {total_fatturato:,.2f}")
col2.metric("Target Semestrale", f"€ {target_semestrale:,.2f}")
col3.metric("Avanzamento Premio", f"{percentuale:.1%}")

st.progress(min(percentuale, 1.0) if percentuale > 0 else 0.0)

# --- GRAFICI ---
st.divider()
c1, c2 = st.columns(2)

with c1:
    fig_prod = px.pie(df, values='importo', names='tipologia prodotto', 
                 title="Fatturato per Tipologia Prodotto")
    st.plotly_chart(fig_prod, use_container_width=True)

with c2:
    fig_mese = px.bar(df, x='mese inserimento', y='importo', color='tipologia prodotto', 
                 title="Andamento Mensile Fatturato")
    st.plotly_chart(fig_mese, use_container_width=True)

st.divider()
st.subheader("📅 Ultime Vendite e Scadenze")
st.dataframe(df.tail(10))
