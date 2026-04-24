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

# --- 2. CSS PARA ALINHAMENTO LADO A LADO (PERFEITO) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    
    /* CONTAINER QUE SEGURA A LOGO E O BOTÃO JUNTOS */
    .button-wrapper {
        position: relative !important;
        display: block !important;
        width: 100% !important;
        margin-bottom: 10px !important;
        height: 75px !important; /* Altura fixa para o conjunto */
    }

    /* IMAGEM POSICIONADA EXATAMENTE AO LADO DO TEXTO */
    .logo-overlay {
        position: absolute !important;
        left: 10px !important;
        top: 50% !important;
        transform: translateY(-50%) !important; /* Centraliza verticalmente no botão */
        width: 55px !important;
        height: 55px !important;
        border-radius: 12px !important;
        object-fit: cover !important;
        border: 1px solid #444 !important;
        z-index: 10 !important;
        pointer-events: none !important;
    }

    /* O BOTÃO QUE "ABRIGA" A LOGO */
    div.stButton > button {
        width: 100% !important;
        height: 75px !important;
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: white !important;
        border-radius: 15px !important;
        padding-left: 75px !important; /* Espaço para a logo não cobrir o texto */
        text-align: left !important;
        font-size: 12px !important;
        line-height: 1.4 !important;
        display: flex !important;
        align-items: center !important;
    }

    /* Ajuste para o texto dentro do botão */
    div.stButton > button p {
        margin: 0 !important;
        white-space: pre-line !important;
    }

    .metric-container { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .val-azul { color: #00d4ff; font-size: 24px; font-weight: bold; }
    .val-verde { color: #28a745; font-size: 24px; font-weight: bold; }
    .val-laranja { color: #ffa500; font-size: 24px; font-weight: bold; }
    .val-vermelho { color: #ff4b4b; font-size: 24px; font-weight: bold; }
    .val-lucro { color: #00ff88; font-size: 24px; font-weight: bold; }
    .edit-panel { background-color: #1c2128; padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; margin-bottom: 25px; }
    label { color: white !important; font-weight: bold !important; text-transform: uppercase !important; }
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
        if 'id' in df.columns:
            df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        if 'sistema' in df.columns:
            df['sistema'] = df['sistema'].astype(str).str.strip().str.upper()
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        df['custo'] = pd.to_numeric(df['custo'], errors='coerce').fillna(0)
        df['mensalidade'] = pd.to_numeric(df['mensalidade'], errors='coerce').fillna(0)
        df = df[df['nome'].astype(str).str.strip() != ""]
        return df
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
    m2.markdown(f'<div class="metric-container"><div class="val-verde">{len(df_ativos)}</div><small>ATIVOS</small></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-container"><div class="val-laranja">{len(df[df["dias_res"] == 0])}</div><small>HOJE</small></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-container"><div class="val-vermelho">{len(df[df["dias_res"] < 0])}</div><small>VENCIDOS</small></div>', unsafe_allow_html=True)
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
            en_venc = st.date_input("VENCIMENTO", value=pd.to_datetime(c_sel.get('vencimento')).date(), format="DD/MM/YYYY")
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
    df_f = df[df['nome'].str.contains(busca, case=False, na=False) | df['usuario'].str.contains(busca, case=False, na=False)] if busca else df
    
    # --- LISTAGEM COM LOGO EMBUTIDA E ALINHADA ---
    for _, r in df_f.sort_values(by='dias_res').iterrows():
        img_tag = f"data:image/png;base64,{r['logo_blob']}" if r.get('logo_blob') else "https://i.imgur.com/vH9XvI0.png"
        sist = str(r.get('sistema')).upper() if r.get('sistema') else "P2P"
        
        # Texto com sistema e quebras de linha para melhor visualização
        txt_display = f"{sist} | {str(r.get('nome'))[:12].upper()}\n🔑 {r.get('usuario')[:10]} | 📅 {format_data_br(r.get('vencimento'))}"
        
        # Envelopamos o conjunto para garantir o alinhamento relativo
        st.markdown(f'<div class="button-wrapper">', unsafe_allow_html=True)
        
        # A logo "flutua" dentro do wrapper, centralizada pelo top:50% do CSS
        st.markdown(f'<img src="{img_tag}" class="logo-overlay">', unsafe_allow_html=True)
        
        if st.button(txt_display, key=f"btn_{r['id']}"):
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
        n_venc = st.date_input("VENCIMENTO", value=hoje + timedelta(days=30), format="DD/MM/YYYY")
        n_custo = st.number_input("CUSTO", value=10.0)
        n_mensal = st.number_input("MENSALIDADE", value=35.0)
        n_whats = st.text_input("WHATSAPP")
        n_obs = st.text_area("OBSERVAÇÃO")
        n_img = st.file_uploader("LOGO", type=['png', 'jpg', 'jpeg'])
        if st.form_submit_button("🚀 CADASTRAR"):
            l_b = base64.b64encode(n_img.read()).decode() if n_img else ""
            novo_id = int(df['id'].max() + 1) if not df.empty else 1
            sheet.append_row([novo_id, n_nome.upper(), n_user, n_senha, n_serv, n_sist, n_venc.strftime('%Y-%m-%d'), n_custo, n_mensal, n_whats, n_obs, l_b])
            st.success("✅ Cadastrado!"); time.sleep(1); st.rerun()

# Abas de Cobrança e Ajustes mantidas conforme o padrão
with tab3:
    st.subheader("🚨 COBRANÇA")
    pix_cnpj = "62.326.879/0001-13"
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    if col_f1.button("❌ VENC"): st.session_state.filtro_cob = "vencidos"
    if col_f2.button("⏰ HOJE"): st.session_state.filtro_cob = "hoje"
    if col_f3.button("📅 AMN"): st.session_state.filtro_cob = "amanha"
    
    filtro_atual = st.session_state.get('filtro_cob', 'vencidos')
    df_c = df[df['dias_res'] < 0] if filtro_atual == "vencidos" else df[df['dias_res'] == 0]
    
    for _, cli in df_c.iterrows():
        st.link_button(f"📲 {str(cli['nome']).upper()}", f"https://wa.me/55{cli['whatsapp']}?text=Vencimento")

with tab4:
    st.subheader("⚙️ AJUSTES")
    if st.button("🔄 SINCRONIZAR"):
        st.cache_data.clear()
        st.rerun()
