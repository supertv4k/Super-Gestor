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

# --- 2. CSS DEFINITIVO (CARD TOTALMENTE CLICÁVEL) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    
    /* ESTILO DO CARD VISUAL */
    .client-card {
        display: flex;
        align-items: center;
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 15px;
        padding: 10px;
        height: 80px;
        width: 100%;
        position: relative;
    }
    .card-logo {
        width: 55px;
        height: 55px;
        border-radius: 10px;
        object-fit: cover;
        margin-right: 15px;
        border: 1px solid #444;
    }
    .card-info {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .info-nome { font-size: 14px; font-weight: bold; color: white; margin: 0; }
    .info-detalhes { font-size: 11px; color: #8b949e; margin: 0; }

    /* O SEGREDO: O BOTÃO OCUPA 100% DO CONTAINER E FICA INVISÍVEL */
    .stButton > button {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 80px !important;
        background: transparent !important;
        border: 1px solid #30363d !important;
        color: transparent !important;
        z-index: 10 !important;
        border-radius: 15px !important;
    }
    .stButton > button:hover {
        border-color: #00d4ff !important;
        background: rgba(0, 212, 255, 0.05) !important;
    }

    /* CONTAINER DO CARD */
    .card-container {
        position: relative;
        height: 80px;
        margin-bottom: 15px;
    }

    .metric-container { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .val-azul { color: #00d4ff; font-size: 24px; font-weight: bold; }
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
    except Exception as e:
        st.error(f"Erro: {e}")
        return None

def carregar_dados(sheet):
    if sheet:
        valores_brutos = sheet.get_all_values()
        if not valores_brutos: return pd.DataFrame()
        cabecalho = [str(c).strip().lower() for c in valores_brutos[0]]
        df = pd.DataFrame(valores_brutos[1:], columns=cabecalho)
        df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
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
    df_ativos = df[df['dias_res'] >= 0]
    lucro_total = df_ativos['mensalidade'].sum() - df_ativos['custo'].sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.markdown(f'<div class="metric-container"><div class="val-azul">{len(df)}</div><small>TOTAL</small></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-container"><div style="color:#28a745; font-size:24px; font-weight:bold;">{len(df_ativos)}</div><small>ATIVOS</small></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-container"><div style="color:#ffa500; font-size:24px; font-weight:bold;">{len(df[df["dias_res"] == 0])}</div><small>HOJE</small></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-container"><div style="color:#ff4b4b; font-size:24px; font-weight:bold;">{len(df[df["dias_res"] < 0])}</div><small>VENCIDOS</small></div>', unsafe_allow_html=True)
    m5.markdown(f'<div class="metric-container"><div class="val-lucro">R$ {lucro_total:,.2f}</div><small>LUCRO</small></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    if st.session_state.get('cliente_selecionado') is not None:
        c_sel = st.session_state.cliente_selecionado
        st.markdown(f'<div class="edit-panel"><h3>📝 EDITANDO: {str(c_sel.get("nome")).upper()}</h3></div>', unsafe_allow_html=True)
        with st.form("edit_form"):
            en_nome = st.text_input("NOME", value=str(c_sel.get('nome')).upper())
            en_user = st.text_input("USUÁRIO", value=c_sel.get('usuario'))
            en_senha = st.text_input("SENHA", value=c_sel.get('senha'))
            en_serv = st.selectbox("SERVIDOR", st.session_state.lista_servidores, index=st.session_state.lista_servidores.index(c_sel.get('servidor')) if c_sel.get('servidor') in st.session_state.lista_servidores else 0)
            en_sist = st.selectbox("SISTEMA", ["IPTV", "P2P"], index=0 if c_sel.get('sistema') == "IPTV" else 1)
            en_venc = st.date_input("VENCIMENTO", value=pd.to_datetime(c_sel.get('vencimento')).date())
            en_custo = st.number_input("CUSTO", value=float(c_sel.get('custo') or 0))
            en_mensal = st.number_input("MENSALIDADE", value=float(c_sel.get('mensalidade') or 0))
            en_whats = st.text_input("WHATSAPP", value=c_sel.get('whatsapp'))
            en_obs = st.text_area("OBSERVAÇÃO", value=c_sel.get('observacao'))
            en_img = st.file_uploader("TROCAR LOGO", type=['png', 'jpg', 'jpeg'])
            
            b_salvar, b_excluir, b_fechar = st.columns(3)
            if b_salvar.form_submit_button("💾 SALVAR"):
                l_b = base64.b64encode(en_img.read()).decode() if en_img else c_sel.get('logo_blob', '')
                ids = sheet.col_values(1)
                row_idx = ids.index(str(c_sel['id'])) + 1
                dados = [str(c_sel['id']), en_nome.upper(), en_user, en_senha, en_serv, en_sist, en_venc.strftime('%Y-%m-%d'), en_custo, en_mensal, en_whats, en_obs, l_b]
                sheet.update(range_name=f'A{row_idx}:L{row_idx}', values=[dados])
                st.session_state.cliente_selecionado = None
                st.success("✅ Salvo!"); time.sleep(1); st.rerun()
            if b_excluir.form_submit_button("🗑️ EXCLUIR"):
                ids = sheet.col_values(1)
                row_idx = ids.index(str(c_sel['id'])) + 1
                sheet.delete_rows(row_idx)
                st.session_state.cliente_selecionado = None
                st.rerun()
            if b_fechar.form_submit_button("✖️ FECHAR"):
                st.session_state.cliente_selecionado = None
                st.rerun()

    busca = st.text_input("🔎 PESQUISAR CLIENTE...")
    df_f = df[df['nome'].str.contains(busca, case=False, na=False)] if busca else df
    
    # --- LISTAGEM COM CARDS 100% CLICÁVEIS ---
    for _, r in df_f.sort_values(by='dias_res').iterrows():
        img_b64 = f"data:image/png;base64,{r['logo_blob']}" if r.get('logo_blob') else "https://i.imgur.com/vH9XvI0.png"
        sist = str(r.get('sistema')).upper()
        venc = format_data_br(r.get('vencimento'))
        
        # Envolvemos tudo em um container relativo
        st.markdown(f'<div class="card-container">', unsafe_allow_html=True)
        
        # 1. Card Visual (Fundo)
        st.markdown(f"""
            <div class="client-card">
                <img src="{img_b64}" class="card-logo">
                <div class="card-info">
                    <p class="info-nome">{sist} | {str(r['nome']).upper()}</p>
                    <p class="info-detalhes">🔑 {r['usuario']} | 📅 {venc}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 2. Botão Invisível (Frente) - Ele cobre exatamente o card acima
        if st.button("", key=f"btn_{r['id']}"):
            st.session_state.cliente_selecionado = r.to_dict()
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.subheader("🚀 NOVO CLIENTE")
    with st.form("add_new", clear_on_submit=True):
        n_nome = st.text_input("NOME")
        n_user = st.text_input("USUÁRIO")
        n_senha = st.text_input("SENHA")
        n_serv = st.selectbox("SERVIDOR", st.session_state.lista_servidores)
        n_sist = st.selectbox("SISTEMA", ["P2P", "IPTV"])
        n_venc = st.date_input("VENCIMENTO", value=hoje + timedelta(days=30))
        n_custo = st.number_input("CUSTO", value=10.0)
        n_mensal = st.number_input("MENSALIDADE", value=35.0)
        n_whats = st.text_input("WHATSAPP (EX: 11999999999)")
        n_obs = st.text_area("OBSERVAÇÃO")
        n_img = st.file_uploader("LOGO", type=['png', 'jpg', 'jpeg'])
        if st.form_submit_button("🚀 CADASTRAR"):
            l_b = base64.b64encode(n_img.read()).decode() if n_img else ""
            novo_id = int(df['id'].max() + 1) if not df.empty else 1
            sheet.append_row([novo_id, n_nome.upper(), n_user, n_senha, n_serv, n_sist, n_venc.strftime('%Y-%m-%d'), n_custo, n_mensal, n_whats, n_obs, l_b])
            st.success("✅ Cadastrado!"); time.sleep(1); st.rerun()

with tab3:
    st.subheader("🚨 CENTRAL DE COBRANÇA")
    pix_cnpj = "62.326.879/0001-13"
    
    # --- BOTÕES DE FILTRO RESTAURADOS ---
    cf1, cf2, cf3, cf4, cf5 = st.columns(5)
    if cf1.button("❌ VENC"): st.session_state.f_cob = "venc"
    if cf2.button("⏰ HOJE"): st.session_state.f_cob = "hoje"
    if cf3.button("📅 AMN"): st.session_state.f_cob = "amn"
    if cf4.button("⏳ 2D"): st.session_state.f_cob = "2d"
    if cf5.button("⏳ 3D"): st.session_state.f_cob = "3d"
    
    f_at = st.session_state.get('f_cob', 'venc')
    
    if f_at == "venc": df_c = df[df['dias_res'] < 0]
    elif f_at == "hoje": df_c = df[df['dias_res'] == 0]
    elif f_at == "amn": df_c = df[df['dias_res'] == 1]
    elif f_at == "2d": df_c = df[df['dias_res'] == 2]
    elif f_at == "3d": df_c = df[df['dias_res'] == 3]
    
    st.markdown(f"**Filtrando: {f_at.upper()} ({len(df_c)})**")
    sel_all = st.checkbox("✅ SELECIONAR TODOS", key="check_todos")
    
    for _, cli in df_c.iterrows():
        whats = str(cli.get('whatsapp')).strip()
        dias = cli['dias_res']
        if st.checkbox(f"{str(cli['nome']).upper()} | {format_data_br(cli['vencimento'])}", value=sel_all, key=f"cob_{cli['id']}"):
            msg = f"Olá {cli['nome']}, sua assinatura SUPERTV4K está próxima do vencimento. Pix: {pix_cnpj}"
            st.link_button(f"📲 ENVIAR WHATSAPP", f"https://wa.me/55{whats}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ AJUSTES")
    if st.button("🔄 SINCRONIZAR"):
        st.cache_data.clear()
        st.rerun()
