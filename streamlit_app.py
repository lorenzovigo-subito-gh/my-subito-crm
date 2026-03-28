import streamlit as st
import pandas as pd
import plotly.express as px

# Configurazione Pagina
st.set_page_config(page_title="Subito CRM Lorenzo", layout="wide")

# --- INDIRIZZI DEI FOGLI (Formato CSV Export) ---
DB_URL = "https://docs.google.com/spreadsheets/d/1xXydotEJiQUD0GB_2mdtj30_BsyM9WLGfNjYGhUu_pQ/export?format=csv&gid=1944182975"
TARGET_URL = "https://docs.google.com/spreadsheets/d/1xXydotEJiQUD0GB_2mdtj30_BsyM9WLGfNjYGhUu_pQ/export?format=csv&gid=1398752677"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        # Legge il CSV, gestisce eventuali spazi nei nomi colonne
        data = pd.read_csv(url)
        data.columns = data.columns.str.strip()
        return data
    except Exception as e:
        st.error(f"Errore caricamento dati: {e}")
        return pd.DataFrame()

# Caricamento
df = load_data(DB_URL)
target_df = load_data(TARGET_URL)

st.title("🚀 Subito CRM - Dashboard Lorenzo")

if not df.empty:
    # 1. Pulizia e Conversione Dati
    df['importo'] = pd.to_numeric(df['importo'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    # 2. Calcolo Logica Target Semestrale
    total_fatturato = df['importo'].sum()
    
    try:
        # Prende il valore dalla colonna Target_Semestrale nel foglio Target
        target_semestrale = float(target_df['Target_Semestrale'].iloc[0])
    except:
        target_semestrale = 100000.0 # Valore di backup se il foglio Target è vuoto

    percentuale = total_fatturato / target_semestrale if target_semestrale > 0 else 0

    # --- SEZIONE KPI ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Fatturato Reale", f"€ {total_fatturato:,.2f}")
    with col2:
        st.metric("Obiettivo Semestrale", f"€ {target_semestrale:,.2f}")
    with col3:
        st.metric("Raggiungimento Premio", f"{percentuale:.1%}")
    
    # Barra di avanzamento colorata
    st.progress(min(percentuale, 1.0))

    # --- SEZIONE GRAFICI ---
    st.divider()
    c1, c2 = st.columns(2)
    
    with c1:
        # Grafico Fatturato per Tipologia Prodotto
        if 'tipologia prodotto' in df.columns:
            fig_prod = px.pie(df, values='importo', names='tipologia prodotto', 
                             title="Mix Prodotti (Fatturato)",
                             hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_prod, use_container_width=True)
        else:
            st.warning("Colonna 'tipologia prodotto' non trovata.")

    with c2:
        # Andamento per Mese
        if 'mese inserimento' in df.columns:
            # Ordiniamo i mesi per sicurezza (opzionale se già ordinati nel DB)
            fig_mese = px.bar(df, x='mese inserimento', y='importo', color='tipologia prodotto',
                             title="Performance Mensile",
                             barmode='group',
                             labels={'importo': 'Fatturato (€)', 'mese inserimento': 'Mese'})
            st.plotly_chart(fig_mese, use_container_width=True)

    # --- SEZIONE TABELLA ---
    st.divider()
    st.subheader("📋 Ultime Vendite Inserite")
    # Mostriamo solo le colonne più importanti per chiarezza
    cols_to_show = ['Ragione Sociale', 'Categoria', 'tipologia prodotto', 'importo', 'data fine prodotto/servizio']
    available_cols = [c for c in cols_to_show if c in df.columns]
    st.dataframe(df[available_cols].tail(10), use_container_width=True)

    # --- ALERT SCADENZE ---
    st.sidebar.header("🔔 Alert Scadenze")
    if 'data fine prodotto/servizio' in df.columns:
        # Semplice visualizzazione dei prossimi in scadenza
        df['data fine prodotto/servizio'] = pd.to_datetime(df['data fine prodotto/servizio'], errors='coerce')
        scadenze = df.sort_values(by='data fine prodotto/servizio').dropna(subset=['data fine prodotto/servizio'])
        st.sidebar.dataframe(scadenze[['Ragione Sociale', 'data fine prodotto/servizio']].head(5))

else:
    st.error("Non è stato possibile caricare i dati. Controlla che il file Google Sheets sia 'Pubblicato sul Web' come CSV.")
