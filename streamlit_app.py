import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="CRM Subito - Lorenzo", layout="wide", page_icon="📈")

# Stile CSS per un look professionale (Rosso Subito)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #ff5a5f; }
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNESSIONE NATIVA ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def load_crm_data():
    # Legge il foglio principale
    df = conn.read(worksheet="DB fatturato clienti Lorenzo")
    df.columns = df.columns.str.strip()
    
    # Pulizia importi
    def clean_val(x):
        try:
            return float(str(x).replace('€', '').replace('.', '').replace(',', '.').strip())
        except:
            return 0.0
            
    df['importo_n'] = df['importo'].apply(clean_val)
    # Conversione date per alert
    df['dt_scadenza'] = pd.to_datetime(df['data fine prodotto/servizio'], dayfirst=True, errors='coerce')
    return df

@st.cache_data(ttl=60)
def load_target():
    try:
        t_df = conn.read(worksheet="Target_Semestrale")
        t_df.columns = t_df.columns.str.strip()
        return t_df
    except:
        return pd.DataFrame()

# Caricamento
df = load_crm_data()
target_df = load_target()

# --- SIDEBAR NAVIGAZIONE ---
st.sidebar.image("https://www.subito.it/assets/img/logo-subito.svg", width=120)
st.sidebar.title("CRM Lorenzo V.")
menu = st.sidebar.radio("Scegli la sezione:", ["📊 Dashboard Performance", "📋 Report Vendite", "👤 Scheda Cliente"])

# --- TAB 1: DASHBOARD ---
if menu == "📊 Dashboard Performance":
    st.title("📊 Performance Commerciale")
    
    # Calcoli Target
    totale_fatturato = df['importo_n'].sum()
    try:
        # Puliamo il valore del target
        val_raw = target_df.iloc[0,0]
        val_target = float(str(val_raw).replace('€', '').replace('.', '').replace(',', '.').strip())
    except:
        val_target = 100000.0
    
    perc_raggiungimento = totale_fatturato / val_target if val_target > 0 else 0
    
    # KPI Top
    c1, c2, c3 = st.columns(3)
    c1.metric("Fatturato Reale YTD", f"€ {totale_fatturato:,.2f}")
    c2.metric("Target Semestrale", f"€ {val_target:,.2f}")
    c3.metric("Avanzamento Premio", f"{perc_raggiungimento:.1%}")
    st.progress(min(perc_raggiungimento, 1.0))
    
    st.divider()
    
    # Grafici
    g1, g2 = st.columns(2)
    with g1:
        fig_pie = px.pie(df, values='importo_n', names='tipologia prodotto', hole=0.5, 
                         title="Mix Prodotti (Volume d'Affari)",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)
    with g2:
        df_m = df.groupby('mese inserimento')['importo_n'].sum().reset_index()
        fig_bar = px.bar(df_m, x='mese inserimento', y='importo_n', title="Trend Fatturato Mensile",
                         color_discrete_sequence=['#ff5a5f'], text_auto='.2s')
        st.plotly_chart(fig_bar, use_container_width=True)

# --- TAB 2: REPORT VENDITE ---
elif menu == "📋 Report Vendite":
    st.title("📋 Report Completo Vendite")
    
    # Filtri veloci
    col_f1, col_f2 = st.columns(2)
    search_query = col_f1.text_input("🔍 Cerca Ragione Sociale...")
    prod_filter = col_f2.multiselect("Filtra per Prodotto", df['tipologia prodotto'].unique())
    
    df_filtered = df.copy()
    if search_query:
        df_filtered = df_filtered[df_filtered['Ragione Sociale'].str.contains(search_query, case=False, na=False)]
    if prod_filter:
        df_filtered = df_filtered[df_filtered['tipologia prodotto'].isin(prod_filter)]
    
    st.write(f"Visualizzando {len(df_filtered)} record su {len(df)}")
    
    # Tabella Modificabile
    st.data_editor(df_filtered[['Ragione Sociale', 'Categoria', 'tipologia prodotto', 'importo', 'mese inserimento', 'data fine prodotto/servizio']], 
                   use_container_width=True, hide_index=True)

# --- TAB 3: SCHEDA CLIENTE ---
elif menu == "👤 Scheda Cliente":
    st.title("👤 Profilo Cliente Dettagliato")
    
    clienti_unici = sorted(df['Ragione Sociale'].dropna().unique().tolist())
    cliente_sel = st.selectbox("Seleziona il cliente per l'analisi:", [""] + clienti_unici)
    
    if cliente_sel:
        dati_c = df[df['Ragione Sociale'] == cliente_sel]
        
        # Header Scheda
        st.subheader(f"Dati per: {cliente_sel}")
        
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.info(f"**Categoria**\n\n{dati_c['Categoria'].iloc[0]}")
        with sc2:
            st.success(f"**Totale Speso**\n\n€ {dati_c['importo_n'].sum():,.2f}")
        with sc3:
            attivi = len(dati_c[dati_c['dt_scadenza'] >= pd.Timestamp.now()])
            st.warning(f"**Contratti Attivi**\n\n{attivi}")
        
        st.divider()
        
        # Elenco Prodotti
        st.markdown("### 📦 Storico Prodotti Acquistati")
        st.dataframe(dati_c[['tipologia prodotto', 'importo', 'mese inserimento', 'data fine prodotto/servizio']], 
                     use_container_width=True, hide_index=True)
        
        # Grafico Trend Cliente
        fig_c = px.line(dati_c.sort_values('dt_scadenza'), x='mese inserimento', y='importo_n', 
                        title="Andamento Investimento Cliente", markers=True)
        st.plotly_chart(fig_c, use_container_width=True)
