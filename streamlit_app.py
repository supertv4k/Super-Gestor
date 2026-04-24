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

# --- 2. ESTILIZAÇÃO CSS (AQUI ESTÁ A MÁGICA DO BOTÃO RETANGULAR COM LOGO) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    
    /* Container para posicionar a logo sobre o botão */
    .btn-container {
        position: relative;
        width: 100%;
        margin-bottom: 10px;
    }

    /* A logo que ficará na esquerda, por cima do botão */
    .img-overlay {
        position: absolute;
        left: 10px;
        top: 50%;
        transform: translateY(-50%);
        width: 50px;
        height: 50px;
        border-radius: 8px;
        object-fit: cover;
        z-index: 10;
        pointer-events: none; /* Deixa o clique passar para o botão abaixo */
        border: 1px solid #444;
    }

    /* O BOTÃO RETANGULAR QUE OCUPA TUDO */
    div.stButton > button {
        width: 100% !important;
        height: 70px !important;
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important; /* Retangular com cantos levemente arredondados */
        color: white !important;
        text-align: left !important;
        padding-left: 75px !important; /* Espaço para não bater na logo */
        font-size: 16px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        transition: 0.3s;
    }
    
    div.stButton > button:hover {
        border-color: #00d4ff !important;
        background-color: #1c2128 !important;
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
        # Lógica de edição
        if st.session_state.get('cliente_selecionado') is not None:
            c_sel = st.session_state.cliente_selecionado
            st.markdown(f'<div class="edit-panel"><h3>📝 EDITANDO: {str(c_sel.get("nome")).upper()}</h3></div>', unsafe_allow_html=True)
            with st.form("edit_form"):
                en_nome = st.text_input("NOME", value=str(c_sel.get('nome')).upper())
                en_user = st.text_input("USUÁRIO", value=c_sel.get('usuario'))
                en_venc = st.date_input("VENCIMENTO", value=pd.to_datetime(c_sel.get('vencimento')).date())
                if st.form_submit_button("💾 SALVAR"):
                    # (Lógica de salvamento omitida por espaço, mas você mantém a sua original)
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
            
            # CRIANDO O BOTÃO COM LOGO SOBREPOSTA NA ESQUERDA
            st.markdown(f'''
                <div class="btn-container">
                    <img src="{img_tag}" class="img-overlay">
                ''', unsafe_allow_html=True)
            
            label_btn = f"{str(r.get('nome')).upper()} | 🔑 {r.get('usuario')} | 📅 {venc_br}"
            if st.button(label_btn, key=f"btn_{r['id']}"):
                st.session_state.cliente_selecionado = r.to_dict()
                st.rerun()
                
            st.markdown('</div>', unsafe_allow_html=True)

# (O restante das tabs 2, 3 e 4 continuam com sua lógica original)
