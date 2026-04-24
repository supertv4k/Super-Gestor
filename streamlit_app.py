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

# --- 2. CSS PARA CARD CLICÁVEL REAL ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; margin-bottom: 20px; }
    
    /* O Card agora é um bloco que reage ao mouse */
    .client-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        transition: 0.3s;
        cursor: pointer;
    }
    .client-card:hover {
        border-color: #00d4ff;
        background-color: #1c2128;
    }
    
    .card-logo {
        width: 60px;
        height: 60px;
        border-radius: 10px;
        object-fit: cover;
        margin-right: 15px;
        border: 1px solid #444;
    }
    
    .info-nome { font-size: 16px; font-weight: bold; color: white; margin: 0; }
    .info-detalhes { font-size: 12px; color: #8b949e; margin: 0; }

    /* Estilo das métricas (Restauradas) */
    .metric-container { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .val-azul { color: #00d4ff; font-size: 24px; font-weight: bold; }
    .val-verde { color: #28a745; font-size: 24px; font-weight: bold; }
    .val-laranja { color: #ffa500; font-size: 24px; font-weight: bold; }
    .val-vermelho { color: #ff4b4b; font-size: 24px; font-weight: bold; }
    .val-lucro { color: #00ff88; font-size: 24px; font-weight: bold; }
    
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

# --- 4. INTERFACE ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" style="width:450px;"><img src="https://i.imgur.com/OkUAPQa.png" style="width:380px; margin-top:-20px;"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)

if not df.empty:
    hoje = datetime.now().date()
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    # MÉTRICAS RESTAURADAS
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.markdown(f'<div class="metric-container"><div class="val-azul">{len(df)}</div><small>TOTAL</small></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-container"><div class="val-verde">{len(df[df["dias_res"] >= 0])}</div><small>ATIVOS</small></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-container"><div class="val-laranja">{len(df[df["dias_res"] == 0])}</div><small>HOJE</small></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-container"><div class="val-vermelho">{len(df[df["dias_res"] < 0])}</div><small>VENCIDOS</small></div>', unsafe_allow_html=True)
    lucro = df[df['dias_res'] >= 0]['mensalidade'].sum() - df[df['dias_res'] >= 0]['custo'].sum()
    m5.markdown(f'<div class="metric-container"><div class="val-lucro">R$ {lucro:,.2f}</div><small>LUCRO</small></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    if st.session_state.get('cliente_selecionado'):
        c = st.session_state.cliente_selecionado
        with st.container(border=True):
            st.markdown(f"### 📝 EDITANDO: {c['nome'].upper()}")
            with st.form("edit_form"):
                en_nome = st.text_input("NOME", value=c['nome'])
                en_venc = st.date_input("VENCIMENTO", value=pd.to_datetime(c['vencimento']).date())
                c_edit1, c_edit2 = st.columns(2)
                if c_edit1.form_submit_button("💾 SALVAR"):
                    st.session_state.cliente_selecionado = None
                    st.rerun()
                if c_edit2.form_submit_button("✖️ FECHAR"):
                    st.session_state.cliente_selecionado = None
                    st.rerun()

    busca = st.text_input("🔎 PESQUISAR CLIENTE...")
    df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df

    # LISTAGEM USANDO BOTÃO COM HTML (FORMA SEGURA)
    for _, r in df_f.sort_values(by='dias_res').iterrows():
        img_b64 = f"data:image/png;base64,{r['logo_blob']}" if r.get('logo_blob') else "https://i.imgur.com/vH9XvI0.png"
        venc_format = pd.to_datetime(r['vencimento']).strftime('%d/%m/%Y')
        
        # Aqui o botão NÃO é invisível, ele RECEBE o conteúdo do card.
        # Para evitar que ele vire uma pílula, usamos o CSS lá em cima para forçar o botão a ser o card.
        card_html = f"""
            <div style="display: flex; align-items: center; text-align: left; width: 100%;">
                <img src="{img_b64}" style="width: 55px; height: 55px; border-radius: 10px; margin-right: 15px;">
                <div>
                    <div style="font-weight: bold; font-size: 14px;">{str(r['sistema']).upper()} | {r['nome'].upper()}</div>
                    <div style="font-size: 11px; color: #8b949e;">🔑 {r['usuario']} | 📅 {venc_format}</div>
                </div>
            </div>
        """
        
        if st.button(card_html, key=f"card_{r['id']}", use_container_width=True):
            st.session_state.cliente_selecionado = r.to_dict()
            st.rerun()

with tab3:
    st.subheader("🚨 CENTRAL DE COBRANÇA")
    pix_cnpj = "62.326.879/0001-13"
    
    # RESTAURANDO OS BOTÕES DE FILTRO
    cf1, cf2, cf3, cf4, cf5 = st.columns(5)
    if cf1.button("❌ VENC"): st.session_state.filtro_c = "venc"
    if cf2.button("⏰ HOJE"): st.session_state.filtro_c = "hoje"
    if cf3.button("📅 1 DIA"): st.session_state.filtro_c = "1d"
    if cf4.button("⏳ 2 DIAS"): st.session_state.filtro_c = "2d"
    if cf5.button("⏳ 3 DIAS"): st.session_state.filtro_c = "3d"
    
    f_at = st.session_state.get('filtro_c', 'venc')
    
    # Lógica de Filtro completa
    if f_at == "venc": df_c = df[df['dias_res'] < 0]
    elif f_at == "hoje": df_c = df[df['dias_res'] == 0]
    elif f_at == "1d": df_c = df[df['dias_res'] == 1]
    elif f_at == "2d": df_c = df[df['dias_res'] == 2]
    elif f_at == "3d": df_c = df[df['dias_res'] == 3]
    
    st.markdown(f"**Exibindo: {f_at.upper()} ({len(df_c)} clientes)**")
    
    selecionar_todos = st.checkbox("✅ SELECIONAR TODOS OS FILTRADOS")
    
    for _, cli in df_c.iterrows():
        if st.checkbox(f"{cli['nome'].upper()} | {pd.to_datetime(cli['vencimento']).strftime('%d/%m/%Y')}", value=selecionar_todos, key=f"cob_{cli['id']}"):
            msg = f"Sua assinatura SUPERTV4K vence em breve. Pix: {pix_cnpj}"
            st.link_button(f"📲 ENVIAR PARA {cli['nome'].upper()}", f"https://wa.me/55{cli['whatsapp']}?text={urllib.parse.quote(msg)}")
