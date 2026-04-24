import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse
import base64
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS REFORÇADA (PARA MANTER LADO A LADO) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    
    /* Força as colunas a ficarem lado a lado mesmo no celular */
    [data-testid="column"] {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        width: auto !important;
        min-width: 0px !important;
    }

    /* Container do botão para ocupar o espaço restante */
    div.stButton { width: 100% !important; }

    /* Ajuste da logo do servidor */
    .img-servidor {
        width: 50px !important;
        height: 50px !important;
        border-radius: 8px;
        margin-right: 8px;
        border: 1px solid #444;
        object-fit: cover;
    }

    /* Botão de Cliente Compacto */
    div.stButton > button { 
        text-align: left !important; 
        background-color: #161b22 !important; 
        border: 1px solid #30363d !important; 
        color: white !important; 
        border-radius: 10px !important; 
        padding: 12px 10px !important; 
        width: 100% !important;
        font-size: 13px !important; /* Fonte levemente menor para caber tudo */
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    
    /* Remove espaços vazios entre as linhas */
    .element-container { margin-bottom: 5px !important; }
    
    /* Métricas */
    .metric-container { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; width: 100%; }
    .val-azul { color: #00d4ff; font-size: 24px; font-weight: bold; }
    .val-verde { color: #28a745; font-size: 24px; font-weight: bold; }
    .val-laranja { color: #ffa500; font-size: 24px; font-weight: bold; }
    .val-vermelho { color: #ff4b4b; font-size: 24px; font-weight: bold; }
    .val-lucro { color: #00ff88; font-size: 24px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXÃO E FUNÇÕES (MESMA LÓGICA ANTERIOR) ---
def conectar_gs():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1ntE8RpofySu5IFupuvOZxZnrnmHKzaYbyqAQ-Mzc8so").sheet1
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

def carregar_dados(sheet):
    if sheet:
        valores_brutos = sheet.get_all_values()
        if not valores_brutos: return pd.DataFrame()
        cabecalho = [str(c).strip().lower() for c in valores_brutos[0]]
        df = pd.DataFrame(valores_brutos[1:], columns=cabecalho)
        if 'id' in df.columns:
            df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        if 'sistema' in df.columns:
            df['sistema'] = df['sistema'].astype(str).str.strip().str.upper().apply(lambda x: "IPTV" if "IPTV" in x else "P2P")
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        df['custo'] = pd.to_numeric(df['custo'], errors='coerce').fillna(0)
        df['mensalidade'] = pd.to_numeric(df['mensalidade'], errors='coerce').fillna(0)
        df = df[df['nome'].astype(str).str.strip() != ""]
        return df
    return pd.DataFrame()

if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = ["UNIPLAY", "MUNDO GF", "P2BRAZ", "UNITV", "PLAYTV", "P2CINE", "P2SPEED", "BLADE", "MEGATV", "BOB PLAYER", "IBO PLAYER", "IBO PRO PLAYER", "OUTROS"]

def format_data_br(data_str):
    try: return pd.to_datetime(data_str).strftime('%d/%m/%Y')
    except: return data_str

# --- 4. INTERFACE ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)

if not df.empty:
    hoje = datetime.now().date()
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    df_ativos = df[df['dias_res'] >= 0]
    lucro_total = df_ativos['mensalidade'].sum() - df_ativos['custo'].sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.markdown(f'<div class="metric-container"><div class="val-azul">{len(df)}</div><small>TOTAL</small></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-container"><div class="val-verde">{len(df_ativos)}</div><small>ATIVOS</small></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-container"><div class="val-laranja">{len(df[df["dias_res"] == 0])}</div><small>HOJE</small></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-container"><div class="val-vermelho">{len(df[df["dias_res"] < 0])}</div><small>VENCIDOS</small></div>', unsafe_allow_html=True)
    m5.markdown(f'<div class="metric-container"><div class="val-lucro">R$ {lucro_total:,.0f}</div><small>LUCRO</small></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ NOVO", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    if st.session_state.get('cliente_selecionado') is not None:
        # (O bloco de edição permanece igual, omitido aqui para brevidade do chat)
        pass 

    busca = st.text_input("🔎 PESQUISAR CLIENTE...")
    df_f = df[df['nome'].str.contains(busca, case=False, na=False) | df['usuario'].str.contains(busca, case=False, na=False)] if busca else df
    
    # --- LISTAGEM LADO A LADO REFORÇADA ---
    for _, r in df_f.sort_values(by='dias_res').iterrows():
        img_tag = f"data:image/png;base64,{r['logo_blob']}" if r.get('logo_blob') else "https://i.imgur.com/vH9XvI0.png"
        
        # Coluna pequena para logo e grande para botão
        c_logo, c_btn = st.columns([1, 8])
        
        with c_logo:
            st.markdown(f'<img src="{img_tag}" class="img-servidor">', unsafe_allow_html=True)
        
        with c_btn:
            txt = f"{str(r.get('nome'))[:12].upper()} | 🔑 {r.get('usuario')} | 📅 {format_data_br(r.get('vencimento'))}"
            if st.button(txt, key=f"btn_{r['id']}"):
                st.session_state.cliente_selecionado = r.to_dict()
                st.rerun()

# (As outras abas seguem a mesma lógica do seu código original)
