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

# --- 2. CSS PARA SOBREPOSIÇÃO REAL (BOTÃO SOBRE O CARD) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    
    /* Container que agrupa o botão e o visual do card */
    .card-container {
        position: relative;
        width: 100%;
        height: 90px; /* Altura fixa para garantir o alinhamento */
        margin-bottom: 15px;
    }

    /* O BOTÃO DO STREAMLIT - Agora ele flutua sobre o card */
    div.stButton > button {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 90px !important;
        background-color: transparent !important;
        color: transparent !important; /* Esconde o texto do botão */
        border: 1px solid #30363d !important;
        border-radius: 15px !important;
        z-index: 10 !important; /* Fica na frente de tudo */
        cursor: pointer !important;
    }
    
    div.stButton > button:hover {
        border-color: #00d4ff !important;
        background-color: rgba(0, 212, 255, 0.05) !important;
    }

    /* O CARD VISUAL - Fica atrás do botão */
    .client-card-visual {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 90px;
        background-color: #161b22;
        border-radius: 15px;
        display: flex;
        align-items: center;
        padding: 10px;
        z-index: 1; /* Fica atrás do botão clicável */
        pointer-events: none; /* Garante que o clique passe para o botão */
    }

    .card-logo {
        width: 65px;
        height: 65px;
        border-radius: 12px;
        object-fit: cover;
        margin-right: 15px;
        border: 1px solid #444;
    }

    .info-txt { display: flex; flex-direction: column; }
    .txt-linha1 { font-size: 14px; font-weight: bold; color: white; margin: 0; }
    .txt-linha2 { font-size: 11px; color: #8b949e; margin: 0; }

    /* Estilo das Métricas e Painéis */
    .metric-container { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .edit-panel { background-color: #1c2128; padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXÃO E DADOS (MANTIDO) ---
def conectar_gs():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1ntE8RpofySu5IFupuvOZxZnrnmHKzaYbyqAQ-Mzc8so").sheet1
    except: return None

def carregar_dados(sheet):
    if sheet:
        valores = sheet.get_all_values()
        if not valores: return pd.DataFrame()
        df = pd.DataFrame(valores[1:], columns=[c.strip().lower() for c in valores[0]])
        df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        df['custo'] = pd.to_numeric(df['custo'], errors='coerce').fillna(0)
        df['mensalidade'] = pd.to_numeric(df['mensalidade'], errors='coerce').fillna(0)
        return df[df['nome'] != ""]
    return pd.DataFrame()

def format_data_br(data_str):
    try: return pd.to_datetime(data_str).strftime('%d/%m/%Y')
    except: return data_str

# --- 4. INTERFACE ---
sheet = conectar_gs()
df = carregar_dados(sheet)

st.markdown('<h2 style="text-align:center; color:#00d4ff;">SUPERTv4k GESTÃO</h2>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    # Painel de Edição (se selecionado)
    if st.session_state.get('cliente_selecionado'):
        c = st.session_state.cliente_selecionado
        st.markdown(f'<div class="edit-panel"><h3>📝 EDITANDO: {c["nome"].upper()}</h3></div>', unsafe_allow_html=True)
        with st.form("edit"):
            # Campos de edição...
            if st.form_submit_button("FECHAR"):
                st.session_state.cliente_selecionado = None
                st.rerun()

    busca = st.text_input("🔎 PESQUISAR...")
    df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df

    # --- LISTAGEM CORRIGIDA ---
    for _, r in df_f.sort_values(by='dt_venc_calc').iterrows():
        img_b64 = f"data:image/png;base64,{r['logo_blob']}" if r.get('logo_blob') else "https://i.imgur.com/vH9XvI0.png"
        venc = format_data_br(r['vencimento'])
        sist = str(r.get('sistema')).upper()

        # Abrimos o container relativo
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        
        # 1. O Botão (Primeiro no código para o Streamlit processar o clique)
        # O CSS joga ele para "frente" com z-index: 10
        if st.button(" ", key=f"btn_{r['id']}"):
            st.session_state.cliente_selecionado = r.to_dict()
            st.rerun()
            
        # 2. O Visual do Card (Segundo no código)
        # O CSS joga ele para "trás" com z-index: 1
        st.markdown(f"""
            <div class="client-card-visual">
                <img src="{img_b64}" class="card-logo">
                <div class="info-txt">
                    <p class="txt-linha1">{sist} | {r['nome'].upper()}</p>
                    <p class="txt-linha2">🔑 {r['usuario']} | 📅 {venc}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.subheader("🚨 CENTRAL DE COBRANÇA")
    # Filtros de cobrança
    col1, col2, col3, col4, col5 = st.columns(5)
    if col1.button("❌ VENC"): st.session_state.filtro = "venc"
    if col2.button("⏰ HOJE"): st.session_state.filtro = "hoje"
    if col3.button("📅 1 DIA"): st.session_state.filtro = "1d"
    if col4.button("⏳ 2 DIAS"): st.session_state.filtro = "2d"
    if col5.button("⏳ 3 DIAS"): st.session_state.filtro = "3d"
    
    # Lógica de exibição e "Selecionar Todos" aqui...
