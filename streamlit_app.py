import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Subito CRM Lorenzo", layout="wide")

# Collegamento al foglio Google (usando l'URL che hai girato)
url = "https://docs.google.com/spreadsheets/d/1xXydotEJiQUD0GB_2mdtj30_BsyM9WLGfNjYGhUu_pQ/edit?usp=sharing"

# Connessione
conn = st.connection("gsheets", type=GSheetsConnection)

# Lettura dati (Specificando i fogli)
df = conn.read(spreadsheet=url, worksheet="DB fatturato clienti Lorenzo")
target_df = conn.read(spreadsheet=url, worksheet="Target")

# Pulizia dati minima
df['importo'] = pd.to_numeric(df['importo'], errors='coerce').fillna(0)

st.title("🚀 Subito CRM - Dashboard Lorenzo")

# --- CALCOLO TARGET E PREMI ---
total_fatturato = df['importo'].sum()

# Cerchiamo il target semestrale nel foglio Target (se vuoto mettiamo 100.000 di default)
if not target_df.empty and 'Target_Semestrale' in target_df.columns:
    target_semestrale = target_df['Target_Semestrale'].iloc[0]
else:
    target_semestrale = 100000

percentuale = total_fatturato / target_semestrale

# --- KPI PRINCIPALI ---
col1, col2, col3 = st.columns(3)
col1.metric("Fatturato Reale", f"€ {total_fatturato:,.2f}")
col2.metric("Target Semestrale", f"€ {target_semestrale:,.2f}")
col3.metric("Avanzamento Premio", f"{percentuale:.1%}")

st.progress(min(percentuale, 1.0))

# --- GRAFICI ---
st.divider()
c1, c2 = st.columns(2)

with c1:
    # Grafico a torta per tipologia prodotto
    fig_prod = px.pie(df, values='importo', names='tipologia prodotto', 
                 title="Fatturato per Tipologia Prodotto",
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_prod, use_container_width=True)

with c2:
    # Andamento mensile (usando la colonna 'mese inserimento')
    fig_mese = px.bar(df, x='mese inserimento', y='importo', color='tipologia prodotto', 
                 title="Andamento Mensile Fatturato",
                 barmode='group')
    st.plotly_chart(fig_mese, use_container_width=True)

# --- TABELLA E SCADENZE ---
st.divider()
st.subheader("📅 Ultime Vendite e Scadenze Imminenti")
st.dataframe(df[['Ragione Sociale', 'Categoria', 'tipologia prodotto', 'data fine prodotto/servizio', 'importo']].tail(15))

# Funzione per inserimento (Anteprima)
with st.expander("➕ Inserisci Nuova Vendita (Logica CRM)"):
    st.write("Modulo di inserimento rapido in fase di attivazione...")
