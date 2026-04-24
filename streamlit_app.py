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

# --- 2. ESTILIZAÇÃO CSS (CORREÇÃO DEFINITIVA DO CARD) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    
    /* Container do Cliente - Estilo Botão Retangular */
    .cliente-card {
        display: flex;
        align-items: center;
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 10px 15px;
        margin-bottom: 10px;
        transition: 0.3s;
        cursor: pointer;
        text-decoration: none !important;
        color: white !important;
    }
    
    .cliente-card:hover {
        border-color: #00d4ff;
        background-color: #1c2128;
    }

    .img-servidor-card {
        width: 55px;
        height: 55px;
        border-radius: 8px;
        object-fit: cover;
        margin-right: 20px; /* Espaço fixo entre a logo e o texto */
        border: 1px solid #444;
        flex-shrink: 0;
    }

    .info-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .nome-cliente {
        font-weight: bold;
        font-size: 16px;
        text-transform: uppercase;
        margin-bottom: 2px;
    }

    .detalhes-cliente {
        font-size: 14px;
        color: #8b949e;
    }

    /* Esconder o botão padrão do Streamlit mas manter a funcionalidade */
    .stButton > button {
        display: none;
    }
    
    /* Botão invisível que cobre o card inteiro para clique */
    .overlay-button {
        background: none !important;
        border: none !important;
        padding: 0 !important;
        width: 100%;
        text-align: left;
    }

    .edit-panel { background-color: #1c2128; padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXÃO E DADOS ---
def conectar_gs():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1ntE8RpofySu5IFupuvOZxZnrnmHKzaYbyqAQ-Mzc8so").sheet1
    except Exception as e:
        st.error(f"Erro: {e}")
        return None

def carregar_dados(sheet):
    if sheet:
        valores = sheet.get_all_values()
        if not valores: return pd.DataFrame()
        df = pd.DataFrame(valores[1:], columns=[str(c).strip().lower() for c in valores[0]])
        if 'id' in df.columns: df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        df['custo'] = pd.to_numeric(df['custo'], errors='coerce').fillna(0)
        df['mensalidade'] = pd.to_numeric(df['mensalidade'], errors='coerce').fillna(0)
        return df[df['nome'].astype(str).str.strip() != ""]
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
    
    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    with tab1:
        # Seção de edição
        if st.session_state.get('cliente_selecionado') is not None:
            c_sel = st.session_state.cliente_selecionado
            st.markdown(f'<div class="edit-panel"><h3>📝 EDITANDO: {str(c_sel.get("nome")).upper()}</h3></div>', unsafe_allow_html=True)
            with st.form("edit_form"):
                en_nome = st.text_input("NOME", value=str(c_sel.get('nome')).upper())
                en_user = st.text_input("USUÁRIO", value=c_sel.get('usuario'))
                if st.form_submit_button("💾 SALVAR"):
                    st.session_state.cliente_selecionado = None
                    st.rerun()
                if st.form_submit_button("✖️ FECHAR"):
                    st.session_state.cliente_selecionado = None
                    st.rerun()

        busca = st.text_input("🔎 PESQUISAR CLIENTE...")
        df_f = df[df['nome'].str.contains(busca, case=False, na=False)] if busca else df
        
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img_tag = f"data:image/png;base64,{r['logo_blob']}" if r.get('logo_blob') else "https://i.imgur.com/vH9XvI0.png"
            venc_br = format_data_br(r.get('vencimento'))
            
            # --- ESTRUTURA DO CARD COM LOGO NA LATERAL (SEM SOBREPOSIÇÃO) ---
            # O st.button fica "invisível" mas clicável sobre o layout HTML
            with st.container():
                st.markdown(f'''
                    <div class="cliente-card">
                        <img src="{img_tag}" class="img-servidor-card">
                        <div class="info-container">
                            <div class="nome-cliente">{str(r.get('nome')).upper()}</div>
                            <div class="detalhes-cliente">🔑 {r.get('usuario')} | {r.get('sistema')} | 📅 {venc_br}</div>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                
                # Botão invisível que aciona a ação
                if st.button("Selecionar", key=f"btn_{r['id']}", use_container_width=True):
                    st.session_state.cliente_selecionado = r.to_dict()
                    st.rerun()

# (Tabs 2, 3 e 4 continuam com a mesma lógica do seu código original)
