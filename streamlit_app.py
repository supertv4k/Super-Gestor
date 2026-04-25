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

# --- 2. ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    
    /* Card Retangular */
    .cliente-card {
        display: flex;
        align-items: center;
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 10px 15px;
        margin-bottom: -72px; 
        position: relative;
        z-index: 1;
    }

    .img-servidor-card {
        width: 55px;
        height: 55px;
        border-radius: 8px;
        object-fit: cover;
        margin-right: 20px;
        border: 1px solid #444;
    }

    .info-text { display: flex; flex-direction: column; }
    .nome-c { font-weight: bold; font-size: 16px; color: white; text-transform: uppercase; }
    .detalhe-c { font-size: 13px; color: #8b949e; }

    /* Botão Invisível que Cobre o Card */
    div.stButton > button {
        width: 100% !important;
        height: 75px !important;
        background-color: transparent !important;
        border: 1px solid transparent !important;
        color: transparent !important;
        position: relative;
        z-index: 10;
        cursor: pointer;
    }
    
    div.stButton > button:hover {
        border: 1px solid #00d4ff !important;
        background-color: rgba(0, 212, 255, 0.05) !important;
    }

    /* Painel de Edição Azul */
    .edit-panel { background-color: #1c2128; padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; margin-bottom: 25px; }
    label { color: white !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE DADOS ---
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
        df = pd.DataFrame(valores[1:], columns=[str(c).strip().lower() for c in valores[0]])
        if 'id' in df.columns: df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        return df[df['nome'].astype(str).str.strip() != ""]
    return pd.DataFrame()

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
        # --- BLOCO DE EDIÇÃO (RESTURADO COM TODOS OS BOTÕES) ---
        if st.session_state.get('cliente_selecionado') is not None:
            c = st.session_state.cliente_selecionado
            st.markdown(f'<div class="edit-panel"><h3>📝 EDITAR: {str(c.get("nome")).upper()}</h3></div>', unsafe_allow_html=True)
            
            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                en_nome = col1.text_input("NOME", value=str(c.get('nome')).upper())
                en_user = col2.text_input("USUÁRIO", value=c.get('usuario'))
                en_senha = col1.text_input("SENHA", value=c.get('senha'))
                en_venc = col2.date_input("VENCIMENTO", value=pd.to_datetime(c.get('vencimento')).date())
                en_whats = col1.text_input("WHATSAPP", value=c.get('whatsapp'))
                en_img = col2.file_uploader("TROCAR LOGO DO SERVIDOR", type=['png', 'jpg', 'jpeg'])
                
                # LINHA DE BOTÕES: SALVAR, EXCLUIR, FECHAR
                b_salvar, b_excluir, b_fechar = st.columns(3)
                
                if b_salvar.form_submit_button("💾 SALVAR"):
                    ids = sheet.col_values(1)
                    row_idx = ids.index(str(c['id'])) + 1
                    
                    # Se subiu imagem nova, converte; se não, mantém a velha
                    if en_img:
                        img_blob = base64.b64encode(en_img.read()).decode()
                    else:
                        img_blob = c.get('logo_blob', '')
                    
                    # Atualiza os dados na planilha (Colunas: ID, Nome, User, Senha, Serv, Sist, Venc, Custo, Mensal, Whats, Obs, Logo)
                    dados_atualizados = [str(c['id']), en_nome.upper(), en_user, en_senha, c.get('servidor'), c.get('sistema'), en_venc.strftime('%Y-%m-%d'), c.get('custo'), c.get('mensalidade'), en_whats, c.get('observacao'), img_blob]
                    sheet.update(range_name=f'A{row_idx}:L{row_idx}', values=[dados_atualizados])
                    
                    st.session_state.cliente_selecionado = None
                    st.success("✅ Alterações salvas!"); time.sleep(1); st.rerun()
                
                if b_excluir.form_submit_button("🗑️ EXCLUIR"):
                    ids = sheet.col_values(1)
                    row_idx = ids.index(str(c['id'])) + 1
                    sheet.delete_rows(row_idx)
                    st.session_state.cliente_selecionado = None
                    st.warning("❌ Cliente excluído."); time.sleep(1); st.rerun()

                if b_fechar.form_submit_button("✖️ FECHAR"):
                    st.session_state.cliente_selecionado = None
                    st.rerun()

        # --- LISTAGEM DE CLIENTES ---
        busca = st.text_input("🔎 PESQUISAR...")
        df_f = df[df['nome'].str.contains(busca, case=False, na=False)] if busca else df
        
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img_src = f"data:image/png;base64,{r['logo_blob']}" if r.get('logo_blob') else "https://i.imgur.com/vH9XvI0.png"
            venc_br = format_data_br(r.get('vencimento'))
            
            st.markdown(f'''
                <div class="cliente-card">
                    <img src="{img_src}" class="img-servidor-card">
                    <div class="info-text">
                        <span class="nome-c">{str(r.get('nome')).upper()}</span>
                        <span class="detalhe-c">🔑 {r.get('usuario')} | {r.get('sistema')} | 📅 {venc_br}</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            
            if st.button(f"edit_{r['id']}", key=f"btn_{r['id']}"):
                st.session_state.cliente_selecionado = r.to_dict()
                st.rerun()

    # --- TABS ADICIONAIS (COBRANÇA E AJUSTES) ---
    with tab2:
        st.subheader("🚀 NOVO CLIENTE")
        with st.form("novo_form", clear_on_submit=True):
            n_nome = st.text_input("NOME")
            n_user = st.text_input("USUÁRIO")
            n_senha = st.text_input("SENHA")
            n_venc = st.date_input("VENCIMENTO", value=hoje + timedelta(days=30))
            n_whats = st.text_input("WHATSAPP")
            n_img = st.file_uploader("LOGO", type=['png', 'jpg'])
            if st.form_submit_button("🚀 CADASTRAR"):
                blob = base64.b64encode(n_img.read()).decode() if n_img else ""
                prox_id = int(df['id'].max() + 1) if not df.empty else 1
                sheet.append_row([prox_id, n_nome.upper(), n_user, n_senha, "SERV", "IPTV", n_venc.strftime('%Y-%m-%d'), 10, 35, n_whats, "", blob])
                st.success("Cadastrado!"); st.rerun()

    with tab3:
        st.subheader("🚨 COBRANÇA")
        for _, cli in df[df['dias_res'] <= 0].iterrows():
            st.write(f"Vencido: {cli['nome']}")
            st.link_button(f"Enviar WhatsApp para {cli['nome']}", f"https://wa.me/55{cli['whatsapp']}?text=Venceu!")

    with tab4:
        st.subheader("⚙️ AJUSTES")
        if st.button("🔄 SINCRONIZAR"): st.rerun()
