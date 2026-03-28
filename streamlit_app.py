import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Subito CRM Lorenzo", layout="wide")

# --- CONFIGURAZIONE URL ---
# Incolla tra le virgolette il link CSV che hai ottenuto da "Pubblica sul Web"
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSFddFLCTd9HUT0UrjsAiHSnHiv4m4yaJX3GXgSMTQclXJ-GL3dw02-gphchK5TUS0aP4KKSbgi8DzW/pub?output=csv" 

@st.cache_data(ttl=60) # Aggiorna i dati ogni minuto
def load_data(url):
    # Leggiamo direttamente il CSV saltando i blocchi aziendali
    data = pd.read_csv(url)
    # Pulizia nomi colonne per sicurezza
    data.columns = data.columns.str.strip()
    return data

st.title("🚀 Subito CRM - Dashboard Lorenzo")

try:
    df = load_data(CSV_URL)
    
    # --- CALCOLO TARGET ---
    # Convertiamo l'importo in numero (gestendo virgole o simboli)
    df['importo'] = pd.to_numeric(df['importo'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    total_fatturato = df['importo'].sum()
    target_semestrale = 100000 # Puoi cambiarlo qui o caricarlo da un altro foglio
    percentuale = total_fatturato / target_semestrale

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
        fig_prod = px.pie(df, values='importo', names='tipologia prodotto', title="Fatturato per Prodotto")
        st.plotly_chart(fig_prod, use_container_width=True)
    with c2:
        fig_mese = px.bar(df, x='mese inserimento', y='importo', color='tipologia prodotto', title="Trend Mensile")
        st.plotly_chart(fig_mese, use_container_width=True)

    st.divider()
    st.subheader("📋 Anteprima Dati")
    st.dataframe(df.tail(10))

except Exception as e:
    st.error(f"⚠️ Errore nel caricamento: {e}")
    st.info("Assicurati di aver incollato il link 'Pubblica sul Web' in formato CSV nel codice.")
