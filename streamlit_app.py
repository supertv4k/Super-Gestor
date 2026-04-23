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
    label { color: white !important; font-weight: bold !important; text-transform: uppercase !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXÃO E FUNÇÕES ---
def conectar_gs():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1ntE8RpofySu5IFupuvOZxZnrnmHKzaYbyqAQ-Mzc8so").sheet1
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

# REMOVIDO O CACHE PARA FORÇAR LEITURA REAL-TIME
def carregar_dados(sheet):
    if sheet:
        # Força o gspread a buscar os dados sem usar cache interno
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame(columns=["id", "nome", "usuario", "senha", "servidor", "sistema", "vencimento", "custo", "mensalidade", "whatsapp", "observacao", "logo_blob"])
        
        # Limpeza rigorosa da coluna sistema
        if 'sistema' in df.columns:
            df['sistema'] = df['sistema'].astype(str).str.strip().str.upper()
            df['sistema'] = df['sistema'].replace({'NONE': 'P2P', '': 'P2P', 'NAN': 'P2P'})
            df['sistema'] = df['sistema'].fillna('P2P')
            
        df = df[df['nome'].astype(str).str.strip() != ""]
        return df
    return pd.DataFrame()

if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = ["UNIPLAY", "MUNDO GF", "P2BRAZ", "UNITV", "PLAYTV", "P2CINE", "P2SPEED", "BLADE", "MEGATV", "BOB PLAYER", "IBO PLAYER", "IBO PRO PLAYER", "OUTROS"]

def format_data_br(data_str):
    try: return datetime.strptime(str(data_str), '%Y-%m-%d').strftime('%d/%m/%Y')
    except: return data_str

# --- 4. INTERFACE ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
# Carregamos os dados garantindo que não há cache
df = carregar_dados(sheet)

if not df.empty:
    hoje = datetime.now().date()
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    df_ativos = df[df['dias_res'] >= 0]
    
    m_val = pd.to_numeric(df_ativos['mensalidade'], errors='coerce').fillna(0)
    c_val = pd.to_numeric(df_ativos['custo'], errors='coerce').fillna(0)
    lucro_total = m_val.sum() - c_val.sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.markdown(f'<div class="metric-container"><div class="metric-label">TOTAL</div><div class="val-azul">{len(df)}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-container"><div class="metric-label">ATIVOS</div><div class="val-verde">{len(df_ativos)}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-container"><div class="metric-label">VENCE HOJE</div><div class="val-laranja">{len(df[df["dias_res"] == 0])}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-container"><div class="metric-label">VENCIDOS</div><div class="val-vermelho">{len(df[df["dias_res"] < 0])}</div></div>', unsafe_allow_html=True)
    m5.markdown(f'<div class="metric-container"><div class="metric-label">LUCRO ESTIMADO</div><div class="val-lucro">R$ {lucro_total:,.2f}</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR CLIENTE", "🚨 COBRANÇA", "⚙️ AJUSTES"])

# --- TAB 1: CLIENTES (EDIÇÃO) ---
with tab1:
    if st.session_state.get('cliente_selecionado') is not None:
        c_sel = st.session_state.cliente_selecionado
        st.markdown(f'<div class="edit-panel"><h3>📝 EDITANDO: {str(c_sel.get("nome")).upper()}</h3></div>', unsafe_allow_html=True)
        
        with st.form("edit_form"):
            en_nome = st.text_input("NOME", value=str(c_sel.get('nome')).upper())
            en_user = st.text_input("USUÁRIO", value=c_sel.get('usuario'))
            en_senha = st.text_input("SENHA", value=c_sel.get('senha'))
            
            # Servidor
            servidores_atuais = st.session_state.lista_servidores
            idx_serv = servidores_atuais.index(c_sel.get('servidor')) if c_sel.get('servidor') in servidores_atuais else 0
            en_serv = st.selectbox("SERVIDOR", servidores_atuais, index=idx_serv)
            
            # Sistema (Selectbox fixo)
            opcoes_sist = ["IPTV", "P2P"]
            sist_banco = str(c_sel.get('sistema', 'P2P')).upper().strip()
            idx_sist = opcoes_sist.index(sist_banco) if sist_banco in opcoes_sist else 1
            en_sist = st.selectbox("SISTEMA", opcoes_sist, index=idx_sist)
            
            curr_venc = pd.to_datetime(c_sel.get('vencimento')).date()
            col_v1, col_v2 = st.columns([3, 1])
            en_venc = col_v1.date_input("VENCIMENTO", value=curr_venc, format="DD/MM/YYYY")
            if col_v2.form_submit_button("+30 DIAS"):
                en_venc = curr_venc + timedelta(days=30)
            
            en_custo = st.number_input("CUSTO", value=float(c_sel.get('custo') or 0))
            en_mensal = st.number_input("MENSALIDADE", value=float(c_sel.get('mensalidade') or 0))
            en_whats = st.text_input("WHATSAPP", value=c_sel.get('whatsapp'))
            en_obs = st.text_area("OBSERVAÇÃO", value=c_sel.get('observacao'))
            en_img = st.file_uploader("TROCAR LOGO", type=['png', 'jpg', 'jpeg'])
            
            b_salvar, b_excluir, b_fechar = st.columns(3)
            
            if b_salvar.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                l_b = base64.b64encode(en_img.read()).decode() if en_img else c_sel.get('logo_blob', '')
                ids = [str(i) for i in sheet.col_values(1)]
                try:
                    row_idx = ids.index(str(c_sel['id'])) + 1
                    nova_linha = [str(c_sel['id']), en_nome.upper(), en_user, en_senha, en_serv, en_sist, en_venc.strftime('%Y-%m-%d'), en_custo, en_mensal, en_whats, en_obs, l_b]
                    sheet.update(range_name=f'A{row_idx}:L{row_idx}', values=[nova_linha])
                    
                    st.session_state.cliente_selecionado = None
                    st.cache_data.clear()
                    st.success("✅ SALVO! RECARREGANDO...")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

            if b_excluir.form_submit_button("🗑️ EXCLUIR"):
                ids = [str(i) for i in sheet.col_values(1)]
                row_idx = ids.index(str(c_sel['id'])) + 1
                sheet.delete_rows(row_idx)
                st.session_state.cliente_selecionado = None
                st.cache_data.clear()
                st.rerun()
                
            if b_fechar.form_submit_button("✖️ FECHAR"):
                st.session_state.cliente_selecionado = None
                st.rerun()

    busca = st.text_input("🔎 PESQUISAR...")
    df_f = df[df['nome'].str.contains(busca, case=False, na=False) | df['usuario'].str.contains(busca, case=False, na=False)] if busca else df
    
    for _, r in df_f.sort_values(by='dias_res').iterrows():
        img_tag = f"data:image/png;base64,{r['logo_blob']}" if r.get('logo_blob') else "https://i.imgur.com/vH9XvI0.png"
        col_img, col_btn = st.columns([1, 10])
        col_img.markdown(f'<img src="{img_tag}" class="img-servidor">', unsafe_allow_html=True)
        
        # EXIBIÇÃO DO SISTEMA NO BOTÃO
        sistema_btn = str(r.get('sistema', 'P2P')).upper()
        txt = f"{str(r.get('nome')).upper()} | 🔑 {r.get('usuario')} | 📅 {format_data_br(r.get('vencimento'))} |  {sistema_btn}"
        
        if col_btn.button(txt, key=f"btn_{r['id']}"):
            st.session_state.cliente_selecionado = r.to_dict()
            st.rerun()

# --- TAB 2: ADICIONAR CLIENTE ---
with tab2:
    st.subheader("🚀 NOVO CLIENTE")
    with st.form("add_new", clear_on_submit=True):
        n_nome = st.text_input("NOME")
        n_user = st.text_input("USUÁRIO")
        n_senha = st.text_input("SENHA")
        n_serv = st.selectbox("SERVIDOR", st.session_state.lista_servidores)
        n_sist = st.selectbox("SISTEMA", ["IPTV", "P2P"])
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
            st.cache_data.clear()
            st.success("✅ CADASTRADO!")
            st.rerun()

# --- TAB 3: COBRANÇA (SIMPLIFICADA PARA O EXEMPLO) ---
with tab3:
    st.subheader("🚨 COBRANÇA")
    st.info("Utilize para enviar mensagens automáticas.")

# --- TAB 4: AJUSTES ---
with tab4:
    st.subheader("⚙️ AJUSTES")
    if st.button("🔄 FORÇAR ATUALIZAÇÃO COMPLETA"):
        st.cache_data.clear()
        st.rerun()
