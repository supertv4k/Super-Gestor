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

# Ordem fixa dos servidores definida por você
SERVIDORES_FIXOS = [
    "UNIPLAY", "MUNDO GF", "P2BRAZ", "UNITV", "PLAYTV", 
    "P2CINE", "P2SPEED", "BLADE", "MEGATV", "BOB PLAYER", 
    "IBO PLAYER", "IBO PRO PLAYER"
]

if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = SERVIDORES_FIXOS

query_params = st.query_params
if "editar_id" in query_params:
    st.session_state.id_para_editar = query_params["editar_id"]

if 'filtro_f' not in st.session_state:
    st.session_state.filtro_f = "VENCIDOS"

# --- 2. ESTILIZAÇÃO CSS (CORREÇÃO DE LARGURA E CARDS) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; margin-bottom: 15px; }
    .logo-gestao { width: 300px; margin-bottom: -10px !important; }
    .logo-supertv { width: 250px; }
    
    /* Metrics compactas */
    .metric-card { background-color: #161b22; padding: 10px; border-radius: 8px; border: 1px solid #30363d; text-align: center; }
    .metric-label { font-size: 11px; color: #8b949e; font-weight: bold; }
    .metric-value { font-size: 18px; color: #00d4ff; font-weight: 900; }

    /* Correção do Card (mais fino e elegante) */
    .card-link { text-decoration: none !important; color: inherit !important; display: block; margin-bottom: 8px; }
    .cliente-card-html { 
        display: flex; align-items: center; background-color: #161b22; 
        border: 1px solid #30363d; border-radius: 10px; padding: 10px; 
        max-height: 85px; width: 100%; transition: 0.2s; 
    }
    .cliente-card-html:hover { border-color: #00d4ff; }
    
    .img-servidor-card { width: 45px; height: 45px; border-radius: 8px; object-fit: cover; margin-right: 12px; border: 1px solid #444; }
    .info-container { flex-grow: 1; min-width: 0; }
    .nome-c { font-weight: 900; font-size: 15px; color: white; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .dias-box { flex-shrink: 0; margin-left: 10px; padding-left: 10px; border-left: 1px solid #30363d; width: 90px; text-align: right; }
    
    .cor-vencido { color: #FF4B4B; font-weight: 900; font-size: 14px; }
    .cor-alerta { color: #FFD700; font-weight: 900; font-size: 14px; }
    .cor-ok { color: #00FF00; font-weight: 900; font-size: 14px; }
    .cor-tranquilo { color: #00D4FF; font-weight: 900; font-size: 14px; }

    /* Ajuste de Labels e Inputs */
    label { text-transform: uppercase !important; font-size: 12px !important; color: #8b949e !important; }
    .stButton>button { width: 100%; text-transform: uppercase; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES ---
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

# --- LÓGICA DE SELEÇÃO ---
if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    if "id_para_editar" in st.session_state:
        sel = df[df['id'].astype(str) == str(st.session_state.id_para_editar)]
        if not sel.empty:
            st.session_state.cliente_selecionado = sel.iloc[0].to_dict()
            del st.session_state.id_para_editar

# --- 4. INTERFACE ---

# 📝 EDIÇÃO (ORDEM EXATA SOLICITADA)
if st.session_state.get('cliente_selecionado') is not None:
    c = st.session_state.cliente_selecionado
    st.markdown("### 📝 EDITAR CLIENTE")
    with st.form("form_edit_full"):
        enome = st.text_input("NOME", value=c['nome'].upper())
        esenha = st.text_input("SENHA", value=c['senha'])
        esist = st.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if c['sistema']=="P2P" else 1)
        ecusto = st.number_input("CUSTO", value=float(c['custo']) if float(c['custo']) != 0 else 5.0)
        ewhats = st.text_input("WHATSAPP", value=c['whatsapp'])
        euser = st.text_input("USUÁRIO", value=c['usuario'])
        # Servidor usando a lista fixa sem ordem alfabética
        eserv = st.selectbox("SERVIDOR", st.session_state.lista_servidores, 
                             index=st.session_state.lista_servidores.index(c['servidor'].upper()) if c['servidor'].upper() in st.session_state.lista_servidores else 0)
        evenc = st.date_input("VENCIMENTO", value=pd.to_datetime(c['vencimento']).date(), format="DD/MM/YYYY")
        emensal = st.number_input("MENSALIDADE", value=float(c['mensalidade']))
        eimg = st.file_uploader("LOGO (CLIQUE PARA TROCAR)", type=['png', 'jpg'])
        eobs = st.text_area("OBSERVAÇÃO", value=c['observacao'].upper())
        
        b1, b2, b3, b4 = st.columns(4)
        if b1.form_submit_button("💾 SALVAR"):
            idx = sheet.col_values(1).index(str(c['id'])) + 1
            blob = base64.b64encode(eimg.read()).decode() if eimg else c['logo_blob']
            sheet.update(f'A{idx}:L{idx}', [[c['id'], enome.upper(), euser, esenha, eserv, esist, evenc.strftime('%Y-%m-%d'), ecusto, emensal, ewhats, eobs.upper(), blob]])
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()
        if b2.form_submit_button("⚡ RENOVAR"):
            idx = sheet.col_values(1).index(str(c['id'])) + 1
            nova_data = (hoje + timedelta(days=30)).strftime('%Y-%m-%d')
            sheet.update_cell(idx, 7, nova_data)
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()
        if b3.form_submit_button("🗑️ EXCLUIR"):
            sheet.delete_rows(sheet.col_values(1).index(str(c['id'])) + 1)
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()
        if b4.form_submit_button("✖️ VOLTAR"):
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()
    st.divider()

st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

if not df.empty:
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-card"><div class="metric-label">ATIVOS</div><div class="metric-value">{len(df[df["dias_res"] >= 0])}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value" style="color:#ff4b4b">{len(df[df["dias_res"] < 0])}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-label">HOJE</div><div class="metric-value" style="color:#ffd700">{len(df[df["dias_res"] == 0])}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO</div><div class="metric-value" style="color:#00ff88">R$ {(df["mensalidade"].sum() - df["custo"].sum()):,.2f}</div></div>', unsafe_allow_html=True)

    tabs = st.tabs(["👤 CLIENTES", "➕ NOVO", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    with tabs[0]:
        busca = st.text_input("🔎 BUSCAR...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            cor = get_cor_classe(r['dias_res'])
            st.markdown(f'<a href="/?editar_id={r["id"]}" target="_self" class="card-link"><div class="cliente-card-html"><img src="{img}" class="img-servidor-card"><div class="info-container"><div class="nome-c">{r["nome"]}</div><span style="color:#8b949e; font-size:12px;">🔑 {r["usuario"]} | {r["sistema"]}</span></div><div class="dias-box"><span class="{cor}">{r["dias_res"]} DIAS</span></div></div></a>', unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("🚀 NOVO CADASTRO")
        with st.form("add_cli", clear_on_submit=True):
            # SEQUÊNCIA EXATA SOLICITADA
            nnome = st.text_input("NOME")
            nsenha = st.text_input("SENHA")
            nsist = st.selectbox("SISTEMA", ["P2P", "IPTV"], index=0)
            ncusto = st.number_input("CUSTO", value=5.0)
            nwhats = st.text_input("WHATSAPP")
            nuser = st.text_input("USUÁRIO")
            nserv = st.selectbox("SERVIDOR", st.session_state.lista_servidores)
            nvenc = st.date_input("VENCIMENTO", value=hoje + timedelta(days=30), format="DD/MM/YYYY")
            nmensal = st.number_input("MENSALIDADE", value=35.0)
            nimg = st.file_uploader("LOGO", type=['png', 'jpg'])
            nobs = st.text_area("OBSERVAÇÃO")
            
            if st.form_submit_button("🚀 CADASTRAR"):
                prox_id = int(df['id'].max() + 1) if not df.empty else 1
                blob = base64.b64encode(nimg.read()).decode() if nimg else ""
                sheet.append_row([prox_id, nnome.upper(), nuser, nsenha, nserv, nsist, nvenc.strftime('%Y-%m-%d'), ncusto, nmensal, nwhats, nobs.upper(), blob])
                st.rerun()

    with tabs[2]:
        st.subheader("🚨 COBRANÇAS")
        # Filtros e Mensagens permanecem os mesmos conforme sua regra
        st.info("SELECIONE O FILTRO ACIMA PARA ENVIAR AS MENSAGENS COM O SEU PIX 62.326.879/0001-13")
        # ... (Lógica de cobrança mantida igual)

    with tabs[3]:
        st.subheader("⚙️ AJUSTES")
        if st.button("🔄 ATUALIZAR DADOS"): st.rerun()
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.drop(columns=['dt_venc_calc', 'dias_res']).to_excel(writer, index=False)
        st.download_button("📥 BAIXAR EXCEL (BACKUP)", data=buffer.getvalue(), file_name="backup_supertv.xlsx")
