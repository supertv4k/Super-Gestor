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

# --- 2. ESTILIZAÇÃO CSS (CORREÇÃO DO BOTÃO E LOGO) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    
    /* ESTILO DO BOTÃO - AGORA A LOGO É PARTE DELE */
    div.stButton > button {
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        width: 100% !important;
        height: 80px !important;
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
        color: white !important;
        padding-left: 20px !important;
        transition: 0.3s !important;
        text-align: left !important;
    }

    div.stButton > button:hover {
        border-color: #00d4ff !important;
        background-color: #1c2128 !important;
    }

    /* Ajuste para a logo dentro do botão */
    .img-servidor {
        width: 50px;
        height: 50px;
        border-radius: 8px;
        object-fit: cover;
        margin-right: 20px;
        border: 1px solid #444;
    }

    .edit-panel { background-color: #1c2128; padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; margin-bottom: 25px; }
    .metric-container { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .val-azul { color: #00d4ff; font-size: 24px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXÃO E CARGA DE DADOS ---
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
        cabecalho = [str(c).strip().lower() for c in valores[0]]
        df = pd.DataFrame(valores[1:], columns=cabecalho)
        if 'id' in df.columns: df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        df['custo'] = pd.to_numeric(df['custo'], errors='coerce').fillna(0)
        df['mensalidade'] = pd.to_numeric(df['mensalidade'], errors='coerce').fillna(0)
        return df[df['nome'].astype(str).str.strip() != ""]
    return pd.DataFrame()

def format_data_br(data_str):
    try: return pd.to_datetime(data_str).strftime('%d/%m/%Y')
    except: return data_str

# --- INÍCIO DO APP ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)

if not df.empty:
    hoje = datetime.now().date()
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    # --- TAB 1: CLIENTES ---
    with tab1:
        if st.session_state.get('cliente_selecionado') is not None:
            c = st.session_state.cliente_selecionado
            st.markdown(f'<div class="edit-panel"><h3>📝 EDITAR: {str(c.get("nome")).upper()}</h3></div>', unsafe_allow_html=True)
            with st.form("edit_form"):
                e_nome = st.text_input("NOME", value=str(c.get('nome')).upper())
                e_user = st.text_input("USUÁRIO", value=c.get('usuario'))
                e_senha = st.text_input("SENHA", value=c.get('senha'))
                e_venc = st.date_input("VENCIMENTO", value=pd.to_datetime(c.get('vencimento')).date())
                e_whats = st.text_input("WHATSAPP", value=c.get('whatsapp'))
                if st.form_submit_button("💾 SALVAR"):
                    # Lógica de update
                    ids = sheet.col_values(1)
                    idx = ids.index(str(c['id'])) + 1
                    sheet.update_cell(idx, 2, e_nome.upper())
                    sheet.update_cell(idx, 3, e_user)
                    sheet.update_cell(idx, 4, e_senha)
                    sheet.update_cell(idx, 7, e_venc.strftime('%Y-%m-%d'))
                    sheet.update_cell(idx, 10, e_whats)
                    st.session_state.cliente_selecionado = None
                    st.rerun()
                if st.form_submit_button("✖️ FECHAR"):
                    st.session_state.cliente_selecionado = None
                    st.rerun()

        busca = st.text_input("🔎 PESQUISAR...")
        df_f = df[df['nome'].str.contains(busca, case=False, na=False)] if busca else df
        
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img_src = f"data:image/png;base64,{r['logo_blob']}" if r.get('logo_blob') else "https://i.imgur.com/vH9XvI0.png"
            venc_br = format_data_br(r.get('vencimento'))
            
            # Aqui usamos colunas para colocar a logo de um lado e o botão do outro de forma limpa
            col_img, col_btn = st.columns([1, 6])
            with col_img:
                st.markdown(f'<img src="{img_src}" class="img-servidor">', unsafe_allow_html=True)
            with col_btn:
                label = f"{str(r.get('nome')).upper()} | 🔑 {r.get('usuario')} | 📅 {venc_br}"
                if st.button(label, key=f"btn_{r['id']}"):
                    st.session_state.cliente_selecionado = r.to_dict()
                    st.rerun()

    # --- TAB 2: ADICIONAR ---
    with tab2:
        st.subheader("🚀 NOVO CLIENTE")
        with st.form("add_new"):
            n_nome = st.text_input("NOME COMPLETO")
            n_user = st.text_input("USUÁRIO")
            n_senha = st.text_input("SENHA")
            n_venc = st.date_input("VENCIMENTO", value=hoje + timedelta(days=30))
            n_whats = st.text_input("WHATSAPP (Ex: 629...)")
            n_img = st.file_uploader("LOGO SERVIDOR", type=['png', 'jpg'])
            if st.form_submit_button("🚀 CADASTRAR"):
                l_b = base64.b64encode(n_img.read()).decode() if n_img else ""
                novo_id = int(df['id'].max() + 1) if not df.empty else 1
                sheet.append_row([novo_id, n_nome.upper(), n_user, n_senha, "SERV", "IPTV", n_venc.strftime('%Y-%m-%d'), 10, 35, n_whats, "", l_b])
                st.rerun()

    # --- TAB 3: COBRANÇA ---
    with tab3:
        st.subheader("🚨 CENTRAL DE COBRANÇA")
        # Filtros simplificados
        df_vencidos = df[df['dias_res'] < 0]
        st.write(f"Clientes Vencidos: {len(df_vencidos)}")
        for _, cli in df_vencidos.iterrows():
            msg = urllib.parse.quote(f"Olá {cli['nome']}, sua assinatura venceu. Segue PIX: 62.326.879/0001-13")
            st.link_button(f"Cobrar {cli['nome']}", f"https://wa.me/55{cli['whatsapp']}?text={msg}")

    # --- TAB 4: AJUSTES ---
    with tab4:
        st.subheader("⚙️ AJUSTES")
        if st.button("🔄 ATUALIZAR DADOS"): st.rerun()
        st.download_button("📥 BACKUP CSV", df.to_csv(index=False).encode('utf-8-sig'), "gestao.csv")
