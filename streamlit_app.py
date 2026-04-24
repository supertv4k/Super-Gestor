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

# --- 2. CSS AVANÇADO (CARDS CLICÁVEIS E FIXOS) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    
    /* ESTILO DO CARD */
    .client-card {
        display: flex;
        align-items: center;
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 15px;
        padding: 12px;
        position: relative;
        z-index: 1;
        height: 85px;
    }
    .card-logo {
        width: 60px;
        height: 60px;
        border-radius: 12px;
        object-fit: cover;
        margin-right: 15px;
        border: 1px solid #444;
    }
    .info-nome { font-size: 15px; font-weight: bold; color: white; }
    .info-detalhes { font-size: 11px; color: #8b949e; }

    /* BOTÃO QUE COBRE O CARD INTEIRO */
    .stButton > button {
        width: 100% !important;
        height: 85px !important;
        background-color: transparent !important;
        color: transparent !important;
        border: 1px solid #30363d !important;
        border-radius: 15px !important;
        position: absolute !important;
        z-index: 10 !important;
        top: 0;
        left: 0;
        transition: 0.3s;
    }
    .stButton > button:hover {
        border-color: #00d4ff !important;
        background-color: rgba(0, 212, 255, 0.05) !important;
    }
    .card-wrapper { position: relative; margin-bottom: 12px; }

    /* MÉTRICAS */
    .metric-container { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .val-azul { color: #00d4ff; font-size: 24px; font-weight: bold; }
    .val-lucro { color: #00ff88; font-size: 24px; font-weight: bold; }
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
        df = pd.DataFrame(valores[1:], columns=[c.strip().lower() for c in valores[0]])
        df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        df['custo'] = pd.to_numeric(df['custo'], errors='coerce').fillna(0)
        df['mensalidade'] = pd.to_numeric(df['mensalidade'], errors='coerce').fillna(0)
        return df[df['nome'] != ""]
    return pd.DataFrame()

# --- 4. INTERFACE ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)

if not df.empty:
    hoje = datetime.now().date()
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    # Métricas
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.markdown(f'<div class="metric-container"><div class="val-azul">{len(df)}</div><small>TOTAL</small></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-container"><div class="val-verde" style="color:#28a745; font-size:24px; font-weight:bold;">{len(df[df["dias_res"] >= 0])}</div><small>ATIVOS</small></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-container"><div class="val-laranja" style="color:#ffa500; font-size:24px; font-weight:bold;">{len(df[df["dias_res"] == 0])}</div><small>HOJE</small></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-container"><div class="val-vermelho" style="color:#ff4b4b; font-size:24px; font-weight:bold;">{len(df[df["dias_res"] < 0])}</div><small>VENCIDOS</small></div>', unsafe_allow_html=True)
    lucro = df[df['dias_res'] >= 0]['mensalidade'].sum() - df[df['dias_res'] >= 0]['custo'].sum()
    m5.markdown(f'<div class="metric-container"><div class="val-lucro">R$ {lucro:,.2f}</div><small>LUCRO</small></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    # Edição
    if st.session_state.get('cliente_selecionado'):
        c = st.session_state.cliente_selecionado
        with st.expander(f"📝 EDITANDO: {c['nome'].upper()}", expanded=True):
            with st.form("edit_form"):
                ed_nome = st.text_input("NOME", value=c['nome'])
                ed_venc = st.date_input("VENCIMENTO", value=pd.to_datetime(c['vencimento']).date())
                if st.form_submit_button("💾 SALVAR"):
                    # Aqui você manteria sua lógica de salvar na planilha
                    st.session_state.cliente_selecionado = None
                    st.rerun()
                if st.form_submit_button("✖️ FECHAR"):
                    st.session_state.cliente_selecionado = None
                    st.rerun()

    busca = st.text_input("🔎 PESQUISAR CLIENTE...")
    df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df

    for _, r in df_f.sort_values(by='dias_res').iterrows():
        img_b64 = f"data:image/png;base64,{r['logo_blob']}" if r.get('logo_blob') else "https://i.imgur.com/vH9XvI0.png"
        
        st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
        # O Card Visual (Fica por baixo)
        st.markdown(f"""
            <div class="client-card">
                <img src="{img_b64}" class="card-logo">
                <div class="card-info">
                    <div class="info-nome">{r['sistema']} | {r['nome'].upper()}</div>
                    <div class="info-detalhes">🔑 {r['usuario']} | 📅 {r['vencimento']}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        # O Botão Clicável (Fica por cima de tudo)
        if st.button(" ", key=f"btn_{r['id']}"):
            st.session_state.cliente_selecionado = r.to_dict()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.subheader("🚨 CENTRAL DE COBRANÇA")
    pix_cnpj = "62.326.879/0001-13"
    
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    if col_f1.button("❌ VENC"): st.session_state.f_cob = "venc"
    if col_f2.button("⏰ HOJE"): st.session_state.f_cob = "hoje"
    if col_f3.button("📅 AMN"): st.session_state.f_cob = "amn"
    if col_f4.button("⏳ 2D"): st.session_state.f_cob = "2d"
    if col_f5.button("⏳ 3D"): st.session_state.f_cob = "3d"
    
    f_ativo = st.session_state.get('f_cob', 'venc')
    # Filtro simplificado para demonstração
    df_c = df[df['dias_res'] < 0] if f_ativo == "venc" else df[df['dias_res'] == 0]
    
    sel_all = st.checkbox("✅ SELECIONAR TODOS")
    for _, cli in df_c.iterrows():
        if st.checkbox(f"{cli['nome'].upper()}", value=sel_all, key=f"c_{cli['id']}"):
            msg = f"Vencimento SUPERTV4K: {pix_cnpj}"
            st.link_button(f"📲 ENVIAR", f"https://wa.me/55{cli['whatsapp']}?text={urllib.parse.quote(msg)}")
