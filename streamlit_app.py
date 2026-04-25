import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse
import base64
import io

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="SUPERTV4K GESTÃO PRO", layout="wide")

if 'filtro_f' not in st.session_state:
    st.session_state.filtro_f = "vencidos"

if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = ["UNIPLAY", "MUNDO GF", "P2BRAZ", "UNITV", "PLAYTV", "P2CINE", "P2SPEED", "BLADE", "MEGA TV", "BOB PLAYER", "IBO PLAYER", "IBO PLAYER PRO"]

# --- 2. ESTILIZAÇÃO CSS (CORRIGIDA) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; margin-bottom: 20px; }
    .logo-gestao { width: 380px; margin-bottom: -15px !important; }
    .logo-supertv { width: 320px; }
    
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; margin-bottom: 20px; }
    .metric-label { font-size: 12px; color: #8b949e; font-weight: bold; text-transform: uppercase; }
    .metric-value { font-size: 20px; color: #00d4ff; font-weight: 900; }

    .card-link { text-decoration: none !important; color: inherit !important; display: block; margin-bottom: 12px; width: 100%; }
    
    .cliente-card-html {
        display: flex; 
        align-items: center; 
        justify-content: space-between; /* ISSO JOGA OS DIAS PARA A DIREITA */
        background-color: #161b22;
        border: 1px solid #30363d; 
        border-radius: 12px; 
        padding: 15px;
        min-height: 100px; 
        width: 100%; 
        transition: 0.2s;
    }
    .cliente-card-html:hover { border-color: #00d4ff; background-color: #1c2128; }
    
    .left-section { display: flex; align-items: center; flex-grow: 1; }
    .img-servidor-card { width: 60px; height: 60px; border-radius: 10px; object-fit: cover; margin-right: 15px; border: 1px solid #444; }
    .info-container { display: flex; flex-direction: column; justify-content: center; }
    .nome-c { font-weight: 900; font-size: 17px; color: white; text-transform: uppercase; line-height: 1.2; }
    
    .dias-box { 
        text-align: right; 
        padding-left: 15px; 
        border-left: 1px solid #30363d; 
        min-width: 110px; 
    }
    
    .cor-vencido { color: #FF4B4B; font-weight: 900; }
    .cor-alerta { color: #FFD700; font-weight: 900; }
    .cor-ok { color: #00FF00; font-weight: 900; }
    .cor-tranquilo { color: #00D4FF; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE DADOS ---
def conectar_gs():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return gspread.authorize(creds).open_by_key("1ntE8RpofySu5IFupuvOZxZnrnmHKzaYbyqAQ-Mzc8so").sheet1
    except: return None

def carregar_dados(sheet):
    if sheet:
        valores = sheet.get_all_values()
        if len(valores) < 2: return pd.DataFrame()
        colunas = ["id", "nome", "usuario", "senha", "servidor", "sistema", "vencimento", "custo", "mensalidade", "whatsapp", "observacao", "logo_blob"]
        df = pd.DataFrame(valores[1:], columns=colunas)
        for col in ['id', 'mensalidade', 'custo']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        return df[df['nome'].str.strip() != ""]
    return pd.DataFrame()

def get_cor_classe(dias):
    if dias < 0: return "cor-vencido"
    elif dias <= 2: return "cor-alerta"
    elif dias == 3: return "cor-ok"
    else: return "cor-tranquilo"

sheet = conectar_gs()
df = carregar_dados(sheet)
hoje = datetime.now().date()

# --- LÓGICA DE EDIÇÃO ---
if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    query_params = st.query_params
    if "editar_id" in query_params:
        sel = df[df['id'].astype(str) == str(query_params["editar_id"])]
        if not sel.empty:
            st.session_state.cliente_selecionado = sel.iloc[0].to_dict()

# --- 4. INTERFACE ---
if st.session_state.get('cliente_selecionado'):
    c = st.session_state.cliente_selecionado
    st.markdown("### 📝 EDITAR CLIENTE")
    with st.form("edit_form"):
        col1, col2 = st.columns(2)
        enome = col1.text_input("NOME", value=c['nome'])
        euser = col2.text_input("USUÁRIO", value=c['usuario'])
        evenc = col1.date_input("VENCIMENTO", value=pd.to_datetime(c['vencimento']).date())
        eserv = col2.selectbox("SERVIDOR", sorted(st.session_state.lista_servidores), index=st.session_state.lista_servidores.index(c['servidor']) if c['servidor'] in st.session_state.lista_servidores else 0)
        
        b1, b4 = st.columns(2)
        if b1.form_submit_button("💾 SALVAR"):
            idx = sheet.col_values(1).index(str(c['id'])) + 1
            sheet.update_cell(idx, 2, enome.upper())
            sheet.update_cell(idx, 7, evenc.strftime('%Y-%m-%d'))
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()
        if b4.form_submit_button("✖️ CANCELAR"):
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()

st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

if not df.empty:
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-card"><div class="metric-label">👤 Ativos</div><div class="metric-value">{len(df[df["dias_res"]>=0])}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">❌ Vencidos</div><div class="metric-value" style="color:#ff4b4b">{len(df[df["dias_res"]<0])}</div></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["👤 CLIENTES", "➕ NOVO", "🚨 COBRANÇA"])

    with tab1:
        busca = st.text_input("🔎 BUSCAR...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            cor = get_cor_classe(r['dias_res'])
            st.markdown(f'''
                <a href="/?editar_id={r['id']}" target="_self" class="card-link">
                    <div class="cliente-card-html">
                        <div class="left-section">
                            <img src="{img}" class="img-servidor-card">
                            <div class="info-container">
                                <div class="nome-c">{r['nome']}</div>
                                <span style="color:#8b949e; font-size:14px;">🔑 {r['usuario']} | 🖥️ {r['sistema']}</span>
                            </div>
                        </div>
                        <div class="dias-box">
                            <span class="{cor}" style="font-size:18px;">{r['dias_res']} DIAS</span><br>
                            <small style="color:#8b949e;">{r['dt_venc_calc'].strftime('%d/%m/%Y')}</small>
                        </div>
                    </div>
                </a>
            ''', unsafe_allow_html=True)

    with tab3:
        # --- BLOCO DE MENSAGENS COM ASPAS TRIPLAS ---
        msg_map = {
            "vencidos": """🚨SUA ASSINATURA DE TV VENCEU !
NÃO PREOCUPE, BASTA FAZER O PIX QUE REATIVAMOS PRA VOCÊ!
💠PIX CNPJ: 62.326.879/0001-13""",
            "hoje": """⚠️SUA ASSINATURA VENCE HOJE ⏰!
BASTA FAZER O PIX QUE RENOVAMOS PRA VOCÊ!
💠PIX CNPJ: 62.326.879/0001-13""",
            "todos": "OLÁ TUDO BEM? ME CHAMA QUE TENHO UMA NOTICIA PRA VOCÊ"
        }
        
        c_cols = st.columns(3)
        if c_cols[0].button("❌ VENCIDOS"): st.session_state.filtro_f = "vencidos"
        if c_cols[1].button("📅 HOJE"): st.session_state.filtro_f = "hoje"
        if c_cols[2].button("🗓️ TODOS"): st.session_state.filtro_f = "todos"
        
        filtro = st.session_state.filtro_f
        msg_atual = msg_map.get(filtro, msg_map["todos"])
        
        df_c = df if filtro == "todos" else (df[df['dias_res'] < 0] if filtro == "vencidos" else df[df['dias_res'] == 0])
        
        for _, r in df_c.iterrows():
            with st.container():
                col_box, col_btn = st.columns([5, 1])
                img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
                cor = get_cor_classe(r['dias_res'])
                col_box.markdown(f'<div class="cliente-card-html"><div class="left-section"><img src="{img}" class="img-servidor-card"><div class="info-container"><div class="nome-c">{r["nome"]}</div></div></div><div class="dias-box"><span class="{cor}">{r["dias_res"]} DIAS</span></div></div>', unsafe_allow_html=True)
                url_whats = f"https://wa.me/55{r['whatsapp']}?text={urllib.parse.quote(msg_atual)}"
                col_btn.link_button("📲 COBRAR", url_whats)
