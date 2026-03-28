import streamlit as st
import pandas as pd
import plotly.express as px

# Configurazione Pagina
st.set_page_config(page_title="Subito CRM Lorenzo", layout="wide", page_icon="🚀")

# --- LINK PUBBLICATI (CSV) ---
DB_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSFddFLCTd9HUT0UrjsAiHSnHiv4m4yaJX3GXgSMTQclXJ-GL3dw02-gphchK5TUS0aP4KKSbgi8DzW/pub?gid=1944182975&single=true&output=csv"
TARGET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSFddFLCTd9HUT0UrjsAiHSnHiv4m4yaJX3GXgSMTQclXJ-GL3dw02-gphchK5TUS0aP4KKSbgi8DzW/pub?gid=1398752677&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = data.columns.str.strip()
        return data
    except Exception as e:
        return pd.DataFrame()

# Funzione per pulire i prezzi (toglie €, punti migliaia, trasforma virgola in punto)
def clean_price(value):
    if pd.isna(value): return 0.0
    s = str(value).replace('€', '').replace(' ', '')
    # Se c'è sia il punto che la virgola (es. 1.200,50)
    if '.' in s and ',' in s:
        s = s.replace('.', '').replace(',', '.')
    # Se c'è solo la virgola (es. 1200,50)
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except:
        return 0.0

# Caricamento dati
df = load_data(DB_URL)
target_df = load_data(TARGET_URL)

if not df.empty:
    # Pulizia colonna importo
    df['importo_clean'] = df['importo'].apply(clean_price)
    
    # --- SIDEBAR FILTRI ---
    st.sidebar.header("🎯 Filtri Dashboard")
    mesi = ["Tutti"] + sorted(df['mese inserimento'].dropna().unique().tolist())
    mese_sel = st.sidebar.selectbox("Seleziona Mese", mesi)
    
    prodotti = ["Tutti"] + sorted(df['tipologia prodotto'].dropna().unique().tolist())
    prod_sel = st.sidebar.selectbox("Tipologia Prodotto", prodotti)
    
    # Applicazione filtri
    df_filtered = df.copy()
    if mese_sel != "Tutti":
        df_filtered = df_filtered[df_filtered['mese inserimento'] == mese_sel]
    if prod_sel != "Tutti":
        df_filtered = df_filtered[df_filtered['tipologia prodotto'] == prod_sel]

    # --- CALCOLO TARGET ---
    totale_fatturato = df['importo_clean'].sum() # Fatturato totale sempre basato su tutto l'anno
    
    try:
        # Cerchiamo la colonna target (indipendentemente dal nome esatto)
        col_target = [c for c in target_df.columns if 'Target' in c][0]
        val_target = target_df[col_target].iloc[0]
        target_val = clean_price(val_target)
    except:
        target_val = 100000.0
    
    perc_raggiungimento = totale_fatturato / target_val if target_val > 0 else 0

    # --- VISUALIZZAZIONE KPI ---
    st.title("🚀 Subito CRM - Dashboard Lorenzo")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Fatturato Reale (YTD)", f"€ {totale_fatturato:,.2f}")
    c2.metric("Target Semestrale", f"€ {target_val:,.2f}")
    c3.metric("Avanzamento Premio", f"{perc_raggiungimento:.1%}")
    
    st.progress(min(perc_raggiungimento, 1.0))

    # --- GRAFICI ---
    st.divider()
    g1, g2 = st.columns(2)
    
    with g1:
        fig_pie = px.pie(df_filtered, values='importo_clean', names='tipologia prodotto', 
                         title=f"Mix Prodotti - {mese_sel}", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with g2:
        # Andamento mensile globale
        df_monthly = df.groupby('mese inserimento')['importo_clean'].sum().reset_index()
        fig_bar = px.bar(df_monthly, x='mese inserimento', y='importo_clean', 
                         title="Andamento Fatturato Mensile", text_auto='.2s')
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- TABELLA DATI E SCADENZE ---
    st.divider()
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        st.subheader("📋 Dettaglio Vendite (Filtrate)")
        st.dataframe(df_filtered[['Ragione Sociale', 'Categoria', 'tipologia prodotto', 'importo', 'data fine prodotto/servizio']], use_container_width=True)
        
    with col_b:
        st.subheader("🔔 Prossime Scadenze")
        if 'data fine prodotto/servizio' in df.columns:
            df['scadenza_dt'] = pd.to_datetime(df['data fine prodotto/servizio'], errors='coerce')
            scadenze = df[df['scadenza_dt'] >= pd.Timestamp.now()].sort_values('scadenza_dt')
            st.dataframe(scadenze[['Ragione Sociale', 'data fine prodotto/servizio']].head(10), use_container_width=True)

else:
    st.error("❌ Errore: Non riesco a leggere i dati. Verifica che entrambi i fogli siano 'Pubblicati sul Web' come CSV.")
