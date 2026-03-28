import streamlit as st
import pandas as pd
import plotly.express as px

# Configurazione Pagina
st.set_page_config(page_title="Subito CRM Lorenzo", layout="wide", page_icon="🚀")

# --- NUOVI LINK PERSONALI (Funzionanti!) ---
DB_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRGTkBfT37GtwGgqoex61g71GITGQze2JHQAb9WaM4-nXclQ21sYF9w2oXnOcgrIw2rhjDjrRb8UNmk/pub?gid=0&single=true&output=csv"
TARGET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRGTkBfT37GtwGgqoex61g71GITGQze2JHQAb9WaM4-nXclQ21sYF9w2oXnOcgrIw2rhjDjrRb8UNmk/pub?gid=614814551&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        # Caricamento forzato in UTF-8 per evitare problemi con accenti
        data = pd.read_csv(url, encoding='utf-8')
        data.columns = data.columns.str.strip()
        return data
    except Exception as e:
        return pd.DataFrame()

def clean_price(value):
    if pd.isna(value) or value == "": return 0.0
    # Trasforma '1.200,50 €' o '1200' in float pulito
    s = str(value).replace('€', '').replace(' ', '').replace('\xa0', '')
    if '.' in s and ',' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except:
        return 0.0

# Caricamento
df = load_data(DB_URL)
target_df = load_data(TARGET_URL)

if not df.empty:
    # Pre-elaborazione dati
    df['importo_n'] = df['importo'].apply(clean_price)
    
    st.title("🚀 Subito CRM - Dashboard Lorenzo")
    st.markdown(f"**Ultimo aggiornamento:** {pd.Timestamp.now().strftime('%H:%M:%S')}")

    # --- CALCOLO TARGET ---
    totale_attuale = df['importo_n'].sum()
    try:
        # Cerca il target nel secondo foglio
        val_target = target_df.iloc[0, 0] # Prende il primo valore della prima colonna
        target_val = clean_price(val_target)
    except:
        target_val = 100000.0
    
    perc = totale_attuale / target_val if target_val > 0 else 0

    # --- KPI HEADER ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Fatturato Totale", f"€ {totale_attuale:,.2f}")
    c2.metric("Target Semestrale", f"€ {target_val:,.2f}")
    c3.metric("Raggiungimento", f"{perc:.1%}")
    
    st.progress(min(perc, 1.0))

    # --- GRAFICI ---
    st.divider()
    col_left, col_right = st.columns(2)
    
    with col_left:
        if 'tipologia prodotto' in df.columns:
            fig_pie = px.pie(df, values='importo_n', names='tipologia prodotto', 
                             title="Distribuzione Prodotti", hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        if 'mese inserimento' in df.columns:
            # Raggruppamento per mese
            df_m = df.groupby('mese inserimento')['importo_n'].sum().reset_index()
            fig_bar = px.bar(df_m, x='mese inserimento', y='importo_n', 
                             title="Andamento Mensile", text_auto='.2s',
                             color_discrete_sequence=['#ff5a5f']) # Rosso Subito
            st.plotly_chart(fig_bar, use_container_width=True)

    # --- TABELLA E SCADENZE ---
    st.divider()
    st.subheader("📋 Registro Vendite")
    st.dataframe(df[['Ragione Sociale', 'tipologia prodotto', 'importo', 'data fine prodotto/servizio']].tail(10), use_container_width=True)

    # Sidebar per scadenze
    st.sidebar.header("⏳ Scadenze Imminenti")
    if 'data fine prodotto/servizio' in df.columns:
        df['dt_scadenza'] = pd.to_datetime(df['data fine prodotto/servizio'], dayfirst=True, errors='coerce')
        prossime = df[df['dt_scadenza'] >= pd.Timestamp.now()].sort_values('dt_scadenza').head(5)
        for _, row in prossime.iterrows():
            st.sidebar.warning(f"**{row['Ragione Sociale']}**\nScade il: {row['data fine prodotto/servizio']}")

else:
    st.error("⚠️ Nessun dato trovato. Verifica che i fogli nel tuo Drive personale siano popolati.")
    st.info("Nota: Assicurati che le colonne si chiamino esattamente come nel file originale.")
