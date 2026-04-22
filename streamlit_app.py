
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse
import io
import base64

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS (Original Gilmar) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    .metric-container { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .metric-label { color: white; font-size: 14px; font-weight: bold; margin-bottom: 5px; }
    .val-azul { color: #00d4ff; font-size: 24px; font-weight: bold; }
    .val-verde { color: #28a745; font-size: 24px; font-weight: bold; }
    .val-laranja { color: #ffa500; font-size: 24px; font-weight: bold; }
    .val-vermelho { color: #ff4b4b; font-size: 24px; font-weight: bold; }
    .val-lucro { color: #00ff88; font-size: 24px; font-weight: bold; }
    .img-servidor { width: 55px; height: 55px; border-radius: 8px; object-fit: cover; border: 1px solid #444; }
    div.stButton > button { text-align: left !important; background-color: #161b22 !important; border: 1px solid #30363d !important; color: white !important; border-radius: 12px !important; padding: 12px !important; width: 100%; }
    .edit-panel { background-color: #1c2128; padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXÃO COM GOOGLE SHEETS (GSPREAD) ---
def conectar_gs():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # Usa o JSON que colamos no Secrets
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        # Abre a planilha pelo ID
        return client.open_by_key("1R3MmGHAD3Qy5mp8GQTEHmQhUR0X2rD3J").sheet1
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return None

def carregar_dados(sheet):
    if sheet:
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    return pd.DataFrame()

def format_data_br(data_str):
    try:
        return datetime.strptime(str(data_str), '%Y-%m-%d').strftime('%d/%m/%Y')
    except: return data_str

def get_servidores():
    return ["UNIPLAY", "MUNDO GF", "P2BRAZ", "UNITV", "PLAYTV", "P2CINE", "P2SPEED", "BLADE", "MEGATV", "BOB PLAYER", "IBO PLAYER", "IBO PRO PLAYER", "OUTROS"]

# --- 4. LÓGICA DE ESTADO ---
if 'cliente_selecionado' not in st.session_state:
    st.session_state.cliente_selecionado = None

# --- 5. INTERFACE ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)

if not df.empty:
    hoje = datetime.now().date()
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    df_ativos = df[df['dias_res'] >= 0]
    lucro_total = pd.to_numeric(df_ativos['mensalidade'], errors='coerce').sum() - pd.to_numeric(df_ativos['custo'], errors='coerce').sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.markdown(f'<div class="metric-container"><div class="metric-label">TOTAL</div><div class="val-azul">{len(df)}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-container"><div class="metric-label">ATIVOS</div><div class="val-verde">{len(df_ativos)}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-container"><div class="metric-label">VENCE HOJE</div><div class="val-laranja">{len(df[df["dias_res"] == 0])}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-container"><div class="metric-label">VENCIDOS</div><div class="val-vermelho">{len(df[df["dias_res"] < 0])}</div></div>', unsafe_allow_html=True)
    m5.markdown(f'<div class="metric-container"><div class="metric-label">LUCRO ESTIMADO</div><div class="val-lucro">R$ {lucro_total:,.2f}</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ NOVO CADASTRO", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    if st.session_state.cliente_selecionado is not None:
        c_sel = st.session_state.cliente_selecionado
        st.markdown(f'<div class="edit-panel"><h3>📝 Editando: {str(c_sel["nome"]).upper()}</h3></div>', unsafe_allow_html=True)
        with st.form("edit_form"):
            col1, col2, col3 = st.columns(3)
            en_nome = col1.text_input("Nome", value=c_sel['nome'])
            en_user = col2.text_input("Usuário", value=c_sel['usuario'])
            en_venc = col3.date_input("Vencimento", value=pd.to_datetime(c_sel['vencimento']).date())
            en_whats = col1.text_input("WhatsApp", value=c_sel['whatsapp'])
            en_custo = col2.number_input("Custo", value=float(c_sel['custo']))
            en_mensal = col3.number_input("Valor Cobrado", value=float(c_sel['mensalidade']))
            
            if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                # Busca a linha correta na planilha para atualizar
                ids = sheet.col_values(1)
                row_idx = ids.index(str(c_sel['id'])) + 1
                sheet.update_cell(row_idx, 2, en_nome)
                sheet.update_cell(row_idx, 3, en_user)
                sheet.update_cell(row_idx, 7, en_venc.strftime('%Y-%m-%d'))
                sheet.update_cell(row_idx, 8, en_custo)
                sheet.update_cell(row_idx, 9, en_mensal)
                sheet.update_cell(row_idx, 10, en_whats)
                st.session_state.cliente_selecionado = None
                st.success("Atualizado!")
                st.rerun()

    busca = st.text_input("🔎 Pesquisar cliente...", placeholder="Nome ou Usuário")
    if not df.empty:
        df_f = df[df['nome'].str.contains(busca, case=False, na=False) | df['usuario'].str.contains(busca, case=False, na=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res', ascending=True).iterrows():
            img_tag = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            c1, c2 = st.columns([1, 10])
            c1.markdown(f'<img src="{img_tag}" class="img-servidor">', unsafe_allow_html=True)
            if c2.button(f"{str(r['nome']).upper()} | 🔑 {r['usuario']} | 📅 {format_data_br(r['vencimento'])}", key=f"b_{r['id']}"):
                st.session_state.cliente_selecionado = r.to_dict()
                st.rerun()

with tab2:
    st.subheader("🚀 Novo Cadastro")
    with st.form("add_new", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        n_nome = f1.text_input("Nome")
        n_user = f2.text_input("Usuário")
        n_senha = f3.text_input("Senha")
        n_serv = f1.selectbox("Servidor", get_servidores())
        n_venc = f3.date_input("Vencimento", value=datetime.now() + timedelta(days=30))
        n_whats = f1.text_input("WhatsApp")
        n_valor = f3.number_input("Valor Cobrado", value=35.0)
        n_img = st.file_uploader("Logo", type=['png', 'jpg'])
        
        if st.form_submit_button("🚀 CADASTRAR CLIENTE"):
            if sheet:
                l_b = base64.b64encode(n_img.read()).decode() if n_img else ""
                novo_id = int(df['id'].max() + 1) if not df.empty else 1
                nova_linha = [novo_id, n_nome, n_user, n_senha, n_serv, "P2P", n_venc.strftime('%Y-%m-%d'), 10.0, n_valor, n_whats, "", l_b]
                sheet.append_row(nova_linha)
                st.success("✅ Salvo no Google Sheets!")
                st.rerun()

with tab3:
    st.subheader("🚨 Cobrança Automática")
    pix_cnpj = "62.326.879/0001-13"
    if not df.empty:
        df_c = df[df['dias_res'] <= 3]
        for _, c in df_c.sort_values(by='dias_res').iterrows():
            msg = f"⚠️ *{str(c['nome']).upper()}, SUA ASSINATURA VENCE EM BREVE!* \n\nPara renovar, faça o PIX: {pix_cnpj}"
            st.link_button(f"📲 Cobrar: {c['nome']}", f"https://wa.me/55{c['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Configurações")
    if st.button("🔄 Sincronizar Agora"):
        st.cache_data.clear()
        st.rerun()
