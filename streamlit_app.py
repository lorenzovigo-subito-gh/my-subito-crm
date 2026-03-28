import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="CRM Subito - Lorenzo", layout="wide", page_icon="📈")

# Stile CSS per il look "Subito"
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #ff5a5f; }
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNESSIONE NATIVA ---
# Questa riga cerca automaticamente l'URL nei "Secrets" che hai salvato prima
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def load_crm_data():
    # Legge il foglio principale (assicurati che il nome sia esatto)
    df = conn.read(worksheet="DB fatturato clienti Lorenzo")
    df.columns = df.columns.str.strip()
    
    # Pulizia importi
    def clean_val(x):
        try:
            return float(str(x).replace('€', '').replace('.', '').replace(',', '.').strip())
        except:
            return 0.0
            
    df['importo_n'] = df['importo'].apply(clean_val)
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

# Caricamento effettivo dei dati
df = load_crm_data()
target_df = load_target()

# --- 3. NAVIGAZIONE (SIDEBAR) ---
st.sidebar.image("https://www.subito.it/assets/img/logo-subito.svg", width=120)
st.sidebar.title("CRM Lorenzo V.")
menu = st.sidebar.radio("Vai a:", ["📊 Dashboard", "📋 Report Vendite", "👤 Scheda Cliente"])

# --- 4. LOGICA DELLE TAB ---

if menu == "📊 Dashboard":
    st.title("📊 Performance Commerciale")
    
    # Calcolo Target
    totale_fatturato = df['importo_n'].sum()
    try:
        val_target = float(str(target_df.iloc[0,0]).replace('€', '').replace('.', '').replace(',', '.').strip())
    except:
        val_target = 100000.0
    
    perc = totale_fatturato / val_target if val_target > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Fatturato Reale YTD", f"€ {totale_fatturato:,.2f}")
    c2.metric("Target Semestrale", f"€ {val_target:,.2f}")
    c3.metric("Raggiungimento", f"{perc:.1%}")
    st.progress(min(perc, 1.0))
    
    st.divider()
    
    g1, g2 = st.columns(2)
    with g1:
        fig_pie = px.pie(df, values='importo_n', names='tipologia prodotto', hole=0.5, title="Mix Prodotti")
        st.plotly_chart(fig_pie, use_container_width=True)
    with g2:
        df_m = df.groupby('mese inserimento')['importo_n'].sum().reset_index()
        fig_bar = px.bar(df_m, x='mese inserimento', y='importo_n', title="Trend Mensile", color_discrete_sequence=['#ff5a5f'])
        st.plotly_chart(fig_bar, use_container_width=True)

elif menu == "📋 Report Vendite":
    st.title("📋 Report Completo Vendite")
    
    search = st.text_input("🔍 Cerca Ragione Sociale...")
    df_filtered = df.copy()
    if search:
        df_filtered = df_filtered[df_filtered['Ragione Sociale'].str.contains(search, case=False, na=False)]
    
    st.data_editor(df_filtered[['Ragione Sociale', 'Categoria', 'tipologia prodotto', 'importo', 'mese inserimento', 'data fine prodotto/servizio']], 
                   use_container_width=True, hide_index=True)

elif menu == "👤 Scheda Cliente":
    st.title("👤 Profilo Cliente")
    cliente_sel = st.selectbox("Seleziona cliente:", sorted(df['Ragione Sociale'].unique()))
    
    if cliente_sel:
        dati_c = df[df['Ragione Sociale'] == cliente_sel]
        col1, col2 = st.columns(2)
        col1.metric("Totale Speso", f"€ {dati_c['importo_n'].sum():,.2f}")
        col2.metric("N. Contratti", len(dati_c))
        
        st.markdown("### Storico Acquisti")
        st.table(dati_c[['tipologia prodotto', 'importo', 'data fine prodotto/servizio']])
