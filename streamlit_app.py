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
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 20px; }
    .logo-gestao { width: 400px; margin-bottom: -15px !important; }
    .logo-supertv { width: 350px; }
    
    /* Métricas */
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .metric-label { font-size: 14px; color: #8b949e; font-weight: bold; }
    .metric-value { font-size: 22px; color: #00d4ff; font-weight: 900; }
    .lucro { color: #00ff7f; }

    /* Card de Cliente */
    .cliente-card {
        display: flex; align-items: center; background-color: #161b22;
        border: 1px solid #30363d; border-radius: 8px; padding: 10px 15px;
        margin-bottom: -72px; position: relative; z-index: 1;
    }
    .img-servidor-card { width: 55px; height: 55px; border-radius: 8px; object-fit: cover; margin-right: 20px; border: 1px solid #444; }
    .info-text { display: flex; flex-direction: column; width: 100%; }
    .linha-topo { display: flex; justify-content: space-between; align-items: center; margin-right: 15px; }
    .nome-c { font-weight: 900; font-size: 17px; color: white; text-transform: uppercase; }
    .dias-destaque { font-weight: 900; font-size: 15px; color: #00d4ff; text-transform: uppercase; }
    .vencido { color: #ff4b4b; }

    /* Botão Invisível */
    div.stButton > button {
        width: 100% !important; height: 75px !important;
        background-color: transparent !important; border: 1px solid transparent !important;
        color: transparent !important; position: relative; z-index: 10; cursor: pointer;
    }
    div.stButton > button:hover { border: 1px solid #00d4ff !important; background-color: rgba(0, 212, 255, 0.05) !important; }

    .edit-panel { background-color: #1c2128; padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE DADOS ---
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
        df = pd.DataFrame(valores[1:], columns=[str(c).strip().lower() for c in valores[0]])
        for col in ['id', 'custo', 'mensalidade']:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        return df[df['nome'].astype(str).str.strip() != ""]
    return pd.DataFrame()

# --- 4. INTERFACE ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)
hoje = datetime.now().date()

if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    # --- MÉTRICAS ---
    ativos = len(df[df['dias_res'] >= 0])
    vencidos = len(df[df['dias_res'] < 0])
    venc_hoje = len(df[df['dias_res'] == 0])
    lucro = df['mensalidade'].sum() - df['custo'].sum()

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-card"><div class="metric-label">👤 ATIVOS</div><div class="metric-value">{ativos}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">❌ VENCIDOS</div><div class="metric-value" style="color:#ff4b4b">{vencidos}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-label">📅 HOJE</div><div class="metric-value">{venc_hoje}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-label">💰 LUCRO LÍQUIDO</div><div class="metric-value lucro">R$ {lucro:,.2f}</div></div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    with tab1:
        if st.session_state.get('cliente_selecionado') is not None:
            c = st.session_state.cliente_selecionado
            st.markdown(f'<div class="edit-panel"><h3>📝 EDITAR: {str(c.get("nome")).upper()}</h3></div>', unsafe_allow_html=True)
            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                en_nome = col1.text_input("NOME", value=str(c.get('nome')).upper())
                en_user = col2.text_input("USUÁRIO", value=c.get('usuario'))
                en_senha = col1.text_input("SENHA", value=c.get('senha'))
                en_venc = col2.date_input("VENCIMENTO", value=pd.to_datetime(c.get('vencimento')).date())
                en_whats = col1.text_input("WHATSAPP", value=c.get('whatsapp'))
                en_sist = col2.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if c.get('sistema') == "P2P" else 1)
                en_serv = col1.text_input("SERVIDOR", value=c.get('servidor'))
                en_mensal = col2.number_input("MENSALIDADE", value=float(c.get('mensalidade')))
                en_custo = col1.number_input("CUSTO", value=float(c.get('custo')))
                en_img = st.file_uploader("TROCAR LOGO", type=['png', 'jpg'])
                
                b_sal, b_exc, b_fec = st.columns(3)
                if b_sal.form_submit_button("💾 SALVAR"):
                    ids = sheet.col_values(1)
                    row = ids.index(str(int(c['id']))) + 1
                    img_blob = base64.b64encode(en_img.read()).decode() if en_img else c.get('logo_blob')
                    sheet.update(range_name=f'A{row}:L{row}', values=[[c['id'], en_nome.upper(), en_user, en_senha, en_serv.upper(), en_sist, en_venc.strftime('%Y-%m-%d'), en_custo, en_mensal, en_whats, "", img_blob]])
                    st.session_state.cliente_selecionado = None
                    st.rerun()
                if b_exc.form_submit_button("🗑️ EXCLUIR"):
                    sheet.delete_rows(sheet.col_values(1).index(str(int(c['id']))) + 1)
                    st.session_state.cliente_selecionado = None
                    st.rerun()
                if b_fec.form_submit_button("✖️ FECHAR"):
                    st.session_state.cliente_selecionado = None
                    st.rerun()

        busca = st.text_input("🔎 PESQUISAR...")
        df_f = df[df['nome'].str.contains(busca, case=False, na=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img_src = f"data:image/png;base64,{r['logo_blob']}" if r.get('logo_blob') else "https://i.imgur.com/vH9XvI0.png"
            dias = r['dias_res']
            txt_dias = f"VENCIDO HÁ {abs(dias)} DIAS" if dias < 0 else ("VENCE HOJE" if dias == 0 else f"FALTAM {dias} DIAS")
            classe = "dias-destaque vencido" if dias < 0 else "dias-destaque"

            st.markdown(f'''
                <div class="cliente-card">
                    <img src="{img_src}" class="img-servidor-card">
                    <div class="info-text">
                        <div class="linha-topo">
                            <span class="nome-c">{str(r["nome"]).upper()}</span>
                            <span class="{classe}">{txt_dias}</span>
                        </div>
                        <span class="detalhe-c">🔑 {r["usuario"]} | {r["sistema"]} | 📅 {pd.to_datetime(r["vencimento"]).strftime("%d/%m/%Y")}</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            if st.button(f"btn_{r['id']}", key=f"btn_{r['id']}"):
                st.session_state.cliente_selecionado = r.to_dict()
                st.rerun()

    with tab2:
        st.subheader("🚀 NOVO CADASTRO")
        with st.form("add_full", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n_nome = c1.text_input("NOME COMPLETO")
            n_user = c2.text_input("USUÁRIO / LOGIN")
            n_senha = c1.text_input("SENHA")
            n_whats = c2.text_input("WHATSAPP")
            n_venc = c1.date_input("VENCIMENTO", value=hoje + timedelta(days=30))
            n_sist = c2.selectbox("SISTEMA", ["P2P", "IPTV"])
            n_serv = c1.text_input("SERVIDOR")
            n_mensal = c2.number_input("VALOR MENSALIDADE", value=35.0)
            n_custo = c1.number_input("VALOR CUSTO", value=10.0)
            n_img = st.file_uploader("LOGO", type=['png', 'jpg'])
            if st.form_submit_button("🚀 CADASTRAR"):
                blob = base64.b64encode(n_img.read()).decode() if n_img else ""
                prox_id = int(df['id'].max() + 1) if not df.empty else 1
                sheet.append_row([prox_id, n_nome.upper(), n_user, n_senha, n_serv.upper(), n_sist, n_venc.strftime('%Y-%m-%d'), n_custo, n_mensal, n_whats, "", blob])
                st.rerun()

    with tab3:
        st.subheader("🚨 FILTROS DE COBRANÇA")
        cf1, cf2, cf3, cf4, cf5 = st.columns(5)
        if cf1.button("❌ Vencidos"): st.session_state.filtro = 'vencido'
        if cf2.button("📅 Hoje"): st.session_state.filtro = 'hoje'
        if cf3.button("🌅 Amanhã"): st.session_state.filtro = 'amanha'
        if cf4.button("⏳ 2-3 Dias"): st.session_state.filtro = '2-3dias'
        if cf5.button("✅ Todos"): st.session_state.filtro = 'todos'
        
        f = st.session_state.get('filtro', 'todos')
        if f == 'vencido': df_c = df[df['dias_res'] < 0]
        elif f == 'hoje': df_c = df[df['dias_res'] == 0]
        elif f == 'amanha': df_c = df[df['dias_res'] == 1]
        elif f == '2-3dias': df_c = df[(df['dias_res'] >= 2) & (df['dias_res'] <= 3)]
        else: df_c = df

        for _, cli in df_c.iterrows():
            col_a, col_b = st.columns([3, 1])
            col_a.write(f"👤 **{cli['nome']}** | {cli['usuario']}")
            msg = urllib.parse.quote(f"Olá {cli['nome']}, sua assinatura vence hoje/venceu. Pix: 62.326.879/0001-13")
            col_b.link_button("📲 COBRAR", f"https://wa.me/55{cli['whatsapp']}?text={msg}")

    with tab4:
        st.subheader("⚙️ AJUSTES DO SISTEMA")
        c_aj1, c_aj2 = st.columns(2)
        if c_aj1.button("🔄 FORÇAR SINCRONIZAÇÃO"): st.rerun()
        c_aj2.download_button("📥 BACKUP EXCEL (CSV)", df.to_csv(index=False).encode('utf-8-sig'), "backup_supertv.csv")
        
        st.divider()
        st.subheader("🖥️ SERVIDORES ATIVOS")
        servidores = df['servidor'].unique()
        for s in servidores:
            st.code(f"Servidor: {s} | Clientes: {len(df[df['servidor'] == s])}")
