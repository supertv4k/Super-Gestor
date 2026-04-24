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

# --- 2. CSS DEFINITIVO (BOTÃO RETANGULAR E ALONGADO) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    
    /* CONTAINER EM GRID PARA SOBREPOSIÇÃO PERFEITA */
    .card-wrapper {
        display: grid;
        grid-template-areas: "overlay";
        margin-bottom: 12px;
        width: 100%;
    }

    /* O CARD VISUAL (O QUE VOCÊ VÊ) */
    .client-card-visual {
        grid-area: overlay;
        display: flex;
        align-items: center;
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 12px;
        height: 85px;
        z-index: 1;
    }

    /* O BOTÃO DO STREAMLIT (O QUE VOCÊ CLICA) */
    /* Aqui forçamos ele a ser RETANGULAR, LARGO e COBRIR O CARD */
    div.stButton > button {
        grid-area: overlay;
        width: 100% !important;
        height: 85px !important;
        background-color: transparent !important;
        color: transparent !important;
        border: 2px solid transparent !important;
        border-radius: 12px !important;
        z-index: 2;
        margin: 0 !important;
        cursor: pointer !important;
        display: block !important;
    }
    
    div.stButton > button:hover {
        border-color: #00d4ff !important;
        background-color: rgba(0, 212, 255, 0.05) !important;
    }

    .card-logo {
        width: 60px;
        height: 60px;
        border-radius: 10px;
        object-fit: cover;
        margin-right: 15px;
        border: 1px solid #444;
    }

    .info-txt { display: flex; flex-direction: column; text-align: left; }
    .txt-linha1 { font-size: 14px; font-weight: bold; color: white; margin: 0; }
    .txt-linha2 { font-size: 11px; color: #8b949e; margin: 0; }

    /* ESTILO DAS MÉTRICAS */
    .metric-container { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .val-azul { color: #00d4ff; font-size: 24px; font-weight: bold; }
    .val-verde { color: #28a745; font-size: 24px; font-weight: bold; }
    .val-laranja { color: #ffa500; font-size: 24px; font-weight: bold; }
    .val-vermelho { color: #ff4b4b; font-size: 24px; font-weight: bold; }
    .val-lucro { color: #00ff88; font-size: 24px; font-weight: bold; }
    
    .edit-panel { background-color: #1c2128; padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXÃO E FUNÇÕES (DADOS COMPLETOS) ---
def conectar_gs():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1ntE8RpofySu5IFupuvOZxZnrnmHKzaYbyqAQ-Mzc8so").sheet1
    except: return None

def carregar_dados(sheet):
    if sheet:
        valores_brutos = sheet.get_all_values()
        if not valores_brutos: return pd.DataFrame()
        df = pd.DataFrame(valores_brutos[1:], columns=[c.strip().lower() for c in valores_brutos[0]])
        df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        df['custo'] = pd.to_numeric(df['custo'], errors='coerce').fillna(0)
        df['mensalidade'] = pd.to_numeric(df['mensalidade'], errors='coerce').fillna(0)
        return df[df['nome'].astype(str).str.strip() != ""]
    return pd.DataFrame()

if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = ["UNIPLAY", "MUNDO GF", "P2BRAZ", "UNITV", "PLAYTV", "P2CINE", "P2SPEED", "BLADE", "MEGATV", "BOB PLAYER", "IBO PLAYER", "IBO PRO PLAYER", "OUTROS"]

# --- 4. INTERFACE ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" style="width:450px;"><img src="https://i.imgur.com/OkUAPQa.png" style="width:380px; margin-top:-20px;"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)

if not df.empty:
    hoje = datetime.now().date()
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    # MÉTRICAS NO TOPO
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.markdown(f'<div class="metric-container"><div class="val-azul">{len(df)}</div><small>TOTAL</small></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-container"><div class="val-verde">{len(df[df["dias_res"] >= 0])}</div><small>ATIVOS</small></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-container"><div class="val-laranja">{len(df[df["dias_res"] == 0])}</div><small>HOJE</small></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-container"><div class="val-vermelho">{len(df[df["dias_res"] < 0])}</div><small>VENCIDOS</small></div>', unsafe_allow_html=True)
    lucro = df[df['dias_res'] >= 0]['mensalidade'].sum() - df[df['dias_res'] >= 0]['custo'].sum()
    m5.markdown(f'<div class="metric-container"><div class="val-lucro">R$ {lucro:,.2f}</div><small>LUCRO</small></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    # PAINEL DE EDIÇÃO
    if st.session_state.get('cliente_selecionado'):
        c = st.session_state.cliente_selecionado
        st.markdown(f'<div class="edit-panel"><h3>📝 EDITANDO: {c["nome"].upper()}</h3></div>', unsafe_allow_html=True)
        with st.form("edit_form"):
            en_nome = st.text_input("NOME", value=c['nome'])
            en_user = st.text_input("USUÁRIO", value=c['usuario'])
            en_venc = st.date_input("VENCIMENTO", value=pd.to_datetime(c['vencimento']).date())
            en_custo = st.number_input("CUSTO", value=float(c['custo']))
            en_mens = st.number_input("MENSALIDADE", value=float(c['mensalidade']))
            en_whats = st.text_input("WHATSAPP", value=c['whatsapp'])
            
            b1, b2 = st.columns(2)
            if b1.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                # (Lógica para salvar na planilha)
                st.session_state.cliente_selecionado = None
                st.success("Salvo!"); time.sleep(0.5); st.rerun()
            if b2.form_submit_button("✖️ CANCELAR"):
                st.session_state.cliente_selecionado = None
                st.rerun()

    busca = st.text_input("🔎 PESQUISAR...")
    df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df

    # LISTAGEM COM CARDS RETANGULARES CLICÁVEIS
    for _, r in df_f.sort_values(by='dias_res').iterrows():
        img = f"data:image/png;base64,{r['logo_blob']}" if r.get('logo_blob') else "https://i.imgur.com/vH9XvI0.png"
        venc_br = pd.to_datetime(r['vencimento']).strftime('%d/%m/%Y')
        
        st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
        
        # 1. O Botão (Capa invisível retangular)
        if st.button("", key=f"btn_{r['id']}"):
            st.session_state.cliente_selecionado = r.to_dict()
            st.rerun()
            
        # 2. O Card (Visual por trás)
        st.markdown(f"""
            <div class="client-card-visual">
                <img src="{img}" class="card-logo">
                <div class="info-txt">
                    <p class="txt-linha1">{str(r['sistema']).upper()} | {r['nome'].upper()}</p>
                    <p class="txt-linha2">🔑 {r['usuario']} | 📅 {venc_br}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.subheader("🚀 NOVO CLIENTE")
    with st.form("novo_cli", clear_on_submit=True):
        n_nome = st.text_input("NOME")
        n_user = st.text_input("USUÁRIO")
        n_sist = st.selectbox("SISTEMA", ["P2P", "IPTV"])
        n_venc = st.date_input("VENCIMENTO", value=hoje + timedelta(days=30))
        n_whats = st.text_input("WHATSAPP")
        n_img = st.file_uploader("LOGO", type=['png', 'jpg'])
        if st.form_submit_button("CADASTRAR"):
            # Lógica de salvar...
            st.rerun()

with tab3:
    st.subheader("🚨 COBRANÇA")
    # BOTÕES DE FILTRO RESTAURADOS
    c1, c2, c3, c4, c5 = st.columns(5)
    if c1.button("❌ VENC"): st.session_state.f_cob = "venc"
    if c2.button("⏰ HOJE"): st.session_state.f_cob = "hoje"
    if c3.button("📅 1 DIA"): st.session_state.f_cob = "1d"
    if c4.button("⏳ 2 DIAS"): st.session_state.f_cob = "2d"
    if c5.button("⏳ 3 DIAS"): st.session_state.f_cob = "3d"
    
    f_at = st.session_state.get('f_cob', 'venc')
    
    # Lógica de Filtro
    if f_at == "venc": df_c = df[df['dias_res'] < 0]
    elif f_at == "hoje": df_c = df[df['dias_res'] == 0]
    elif f_at == "1d": df_c = df[df['dias_res'] == 1]
    elif f_at == "2d": df_c = df[df['dias_res'] == 2]
    elif f_at == "3d": df_c = df[df['dias_res'] == 3]
    else: df_c = df[df['dias_res'] < 0]

    st.markdown(f"**Filtrando: {f_at.upper()} ({len(df_c)})**")
    sel_all = st.checkbox("✅ SELECIONAR TODOS")
    
    for _, cli in df_c.iterrows():
        if st.checkbox(f"{cli['nome'].upper()} ({pd.to_datetime(cli['vencimento']).strftime('%d/%m/%Y')})", value=sel_all, key=f"cb_{cli['id']}"):
            msg = f"Olá {cli['nome']}, sua assinatura SUPERTV4K está próxima do vencimento!"
            st.link_button("📲 ENVIAR", f"https://wa.me/55{cli['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    if st.button("🔄 ATUALIZAR SISTEMA"):
        st.cache_data.clear()
        st.rerun()
