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

# --- 2. ESTILIZAÇÃO CSS (VISUAL DO BOTÃO CORRIGIDO) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    
    /* Container do Card Visual */
    .cliente-card {
        display: flex;
        align-items: center;
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 10px 15px;
        margin-bottom: -72px; /* Sobreposição para o botão invisível */
        position: relative;
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

    /* BOTÃO QUE RECEBE O CLIQUE */
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

    .edit-panel { background-color: #1c2128; padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; margin-bottom: 25px; }
    label { color: white !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXÃO COM GOOGLE SHEETS ---
def conectar_gs():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1ntE8RpofySu5IFupuvOZxZnrnmHKzaYbyqAQ-Mzc8so").sheet1
    except:
        return None

def carregar_dados(sheet):
    if sheet:
        valores = sheet.get_all_values()
        if not valores: return pd.DataFrame()
        # Cabeçalho: id, nome, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, whatsapp, observacao, logo_blob
        df = pd.DataFrame(valores[1:], columns=[str(c).strip().lower() for c in valores[0]])
        if 'id' in df.columns:
            df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        df['custo'] = pd.to_numeric(df['custo'], errors='coerce').fillna(0)
        df['mensalidade'] = pd.to_numeric(df['mensalidade'], errors='coerce').fillna(0)
        return df[df['nome'].astype(str).str.strip() != ""]
    return pd.DataFrame()

def format_data_br(data_str):
    try: return pd.to_datetime(data_str).strftime('%d/%m/%Y')
    except: return data_str

# --- 4. EXECUÇÃO PRINCIPAL ---
sheet = conectar_gs()
df = carregar_dados(sheet)

st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

if not df.empty:
    hoje = datetime.now().date()
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    with tab1:
        # PAINEL DE EDIÇÃO (RESTURADO)
        if st.session_state.get('cliente_selecionado') is not None:
            c = st.session_state.cliente_selecionado
            st.markdown(f'<div class="edit-panel"><h3>📝 EDITANDO: {str(c.get("nome")).upper()}</h3></div>', unsafe_allow_html=True)
            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                e_nome = col1.text_input("NOME", value=str(c.get('nome')).upper())
                e_user = col2.text_input("USUÁRIO", value=c.get('usuario'))
                e_senha = col1.text_input("SENHA", value=c.get('senha'))
                e_venc = col2.date_input("VENCIMENTO", value=pd.to_datetime(c.get('vencimento')).date())
                e_whats = col1.text_input("WHATSAPP", value=c.get('whatsapp'))
                e_mensal = col2.number_input("MENSALIDADE", value=float(c.get('mensalidade') or 0))
                
                b_salvar, b_cancelar = st.columns(2)
                if b_salvar.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                    ids = sheet.col_values(1)
                    row_idx = ids.index(str(c['id'])) + 1
                    # Atualiza a linha na planilha
                    sheet.update_cell(row_idx, 2, e_nome.upper())
                    sheet.update_cell(row_idx, 3, e_user)
                    sheet.update_cell(row_idx, 4, e_senha)
                    sheet.update_cell(row_idx, 7, e_venc.strftime('%Y-%m-%d'))
                    sheet.update_cell(row_idx, 9, e_mensal)
                    sheet.update_cell(row_idx, 10, e_whats)
                    st.session_state.cliente_selecionado = None
                    st.success("✅ Atualizado!"); time.sleep(1); st.rerun()
                if b_cancelar.form_submit_button("✖️ CANCELAR"):
                    st.session_state.cliente_selecionado = None
                    st.rerun()

        busca = st.text_input("🔎 PESQUISAR CLIENTE...")
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
            
            if st.button(f"EDITAR_{r['id']}", key=f"btn_{r['id']}"):
                st.session_state.cliente_selecionado = r.to_dict()
                st.rerun()

    with tab2:
        st.subheader("🚀 CADASTRAR NOVO CLIENTE")
        with st.form("add_new", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            n_nome = col_a.text_input("NOME COMPLETO")
            n_user = col_b.text_input("USUÁRIO / LOGIN")
            n_senha = col_a.text_input("SENHA")
            n_whats = col_b.text_input("WHATSAPP (Ex: 629...)")
            n_venc = col_a.date_input("DATA DE VENCIMENTO", value=hoje + timedelta(days=30))
            n_sist = col_b.selectbox("SISTEMA", ["P2P", "IPTV"])
            n_mensal = col_a.number_input("VALOR MENSALIDADE", value=35.0)
            n_custo = col_b.number_input("VALOR CUSTO", value=10.0)
            n_img = st.file_uploader("UPLOAD DA LOGO DO SERVIDOR", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("🚀 FINALIZAR CADASTRO"):
                l_b = base64.b64encode(n_img.read()).decode() if n_img else ""
                novo_id = int(df['id'].max() + 1) if not df.empty else 1
                sheet.append_row([novo_id, n_nome.upper(), n_user, n_senha, "SERVIDOR", n_sist, n_venc.strftime('%Y-%m-%d'), n_custo, n_mensal, n_whats, "", l_b])
                st.success("✅ Cliente Cadastrado com Sucesso!"); time.sleep(1); st.rerun()

# --- (Tabs 3 e 4 permanecem as mesmas de cobrança e backup) ---
