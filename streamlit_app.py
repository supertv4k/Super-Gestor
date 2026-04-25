import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse
import base64
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTV4K GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 20px; }
    .logo-gestao { width: 400px; margin-bottom: -15px !important; }
    .logo-supertv { width: 350px; }
    
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .metric-label { font-size: 14px; color: #8b949e; font-weight: bold; }
    .metric-value { font-size: 22px; color: #00d4ff; font-weight: 900; }
    .lucro { color: #00ff7f; }

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

    div.stButton > button {
        width: 100% !important; height: 75px !important;
        background-color: transparent !important; border: 1px solid transparent !important;
        color: transparent !important; position: relative; z-index: 10; cursor: pointer;
    }
    div.stButton > button:hover { border: 1px solid #00d4ff !important; background-color: rgba(0, 212, 255, 0.05) !important; }
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
        if len(valores) < 2: return pd.DataFrame()
        
        # Forçamos tudo para minúsculo para bater com sua planilha
        colunas = ["id", "nome", "usuario", "senha", "servidor", "sistema", "vencimento", "custo", "mensalidade", "whatsapp", "observacao", "logo_blob"]
        df = pd.DataFrame(valores[1:], columns=colunas[:len(valores[0])])
        
        # Ajustes de tipos e limpeza
        df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        df['custo'] = pd.to_numeric(df['custo'].str.replace(',', '.'), errors='coerce').fillna(0)
        df['mensalidade'] = pd.to_numeric(df['mensalidade'].str.replace(',', '.'), errors='coerce').fillna(0)
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        return df[df['nome'].str.strip() != ""]
    return pd.DataFrame()

# --- 4. INTERFACE ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)
hoje = datetime.now().date()

if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    # MÉTRICAS
    lucro_total = df['mensalidade'].sum() - df['custo'].sum()
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-card"><div class="metric-label">👤 ATIVOS</div><div class="metric-value">{len(df[df["dias_res"] >= 0])}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">❌ VENCIDOS</div><div class="metric-value" style="color:#ff4b4b">{len(df[df["dias_res"] < 0])}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-label">📅 HOJE</div><div class="metric-value">{len(df[df["dias_res"] == 0])}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-label">💰 LUCRO</div><div class="metric-value lucro">R$ {lucro_total:,.2f}</div></div>', unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    with t1:
        # EDIÇÃO (FOCADA EM MINÚSCULOS)
        if st.session_state.get('cliente_selecionado') is not None:
            c = st.session_state.cliente_selecionado
            st.markdown(f"### 📝 EDITAR: {c['nome'].upper()}")
            with st.form("edit_form"):
                ca, cb = st.columns(2)
                e_nome = ca.text_input("NOME", value=c['nome'])
                e_user = cb.text_input("USUÁRIO", value=c['usuario'])
                e_senha = ca.text_input("SENHA", value=c['senha'])
                e_serv = cb.text_input("SERVIDOR", value=c['servidor'])
                e_sist = ca.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if c['sistema'] == "P2P" else 1)
                e_venc = cb.date_input("VENCIMENTO", value=pd.to_datetime(c['vencimento']).date())
                e_custo = ca.number_input("CUSTO", value=float(c['custo']))
                e_mensal = cb.number_input("MENSALIDADE", value=float(c['mensalidade']))
                e_whats = ca.text_input("WHATSAPP", value=c['whatsapp'])
                e_obs = cb.text_area("OBSERVAÇÃO", value=c['observacao'])
                e_img = st.file_uploader("ALTERAR LOGO", type=['png', 'jpg'])
                
                bs, be, bc = st.columns(3)
                if bs.form_submit_button("💾 SALVAR"):
                    idx = sheet.col_values(1).index(str(c['id'])) + 1
                    blob = base64.b64encode(e_img.read()).decode() if e_img else c['logo_blob']
                    sheet.update(f'A{idx}:L{idx}', [[c['id'], e_nome.upper(), e_user, e_senha, e_serv.upper(), e_sist, e_venc.strftime('%Y-%m-%d'), e_custo, e_mensal, e_whats, e_obs, blob]])
                    st.session_state.cliente_selecionado = None
                    st.rerun()
                if be.form_submit_button("🗑️ EXCLUIR"):
                    sheet.delete_rows(sheet.col_values(1).index(str(c['id'])) + 1)
                    st.session_state.cliente_selecionado = None
                    st.rerun()
                if bc.form_submit_button("✖️ FECHAR"):
                    st.session_state.cliente_selecionado = None
                    st.rerun()

        # LISTAGEM DE CLIENTES
        busca = st.text_input("🔎 PESQUISAR CLIENTE...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            # Recupera LOGO_BLOB (minúsculo agora)
            img_html = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            d_cor = "vencido" if r['dias_res'] < 0 else ""
            d_txt = f"VENCIDO HÁ {abs(r['dias_res'])} DIAS" if r['dias_res'] < 0 else (f"FALTAM {r['dias_res']} DIAS" if r['dias_res'] > 0 else "VENCE HOJE")
            
            st.markdown(f'''
                <div class="cliente-card">
                    <img src="{img_html}" class="img-servidor-card">
                    <div class="info-text">
                        <div class="linha-topo"><span class="nome-c">{r['nome']}</span><span class="dias-destaque {d_cor}">{d_txt}</span></div>
                        <span class="detalhe-c">🔑 {r['usuario']} | {r['servidor']} | 📅 {pd.to_datetime(r['vencimento']).strftime('%d/%m/%Y')}</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            if st.button(f"btn_{r['id']}", key=f"btn_{r['id']}"):
                st.session_state.cliente_selecionado = r.to_dict()
                st.rerun()

    with t2:
        # ADICIONAR (ORDEM EXATA SOLICITADA)
        st.subheader("🚀 NOVO CADASTRO")
        with st.form("add_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            n_nome = col_a.text_input("NOME")
            n_user = col_b.text_input("USUÁRIO")
            n_senha = col_a.text_input("SENHA")
            n_serv = col_b.text_input("SERVIDOR")
            n_sist = col_a.selectbox("SISTEMA", ["P2P", "IPTV"])
            n_venc = col_b.date_input("VENCIMENTO", value=hoje + timedelta(days=30))
            n_custo = col_a.number_input("CUSTO", value=10.0)
            n_mensal = col_b.number_input("MENSALIDADE", value=35.0)
            n_whats = col_a.text_input("WHATSAPP")
            n_obs = col_b.text_area("OBSERVAÇÃO")
            n_img = st.file_uploader("LOGO SERVIDOR", type=['png', 'jpg'])
            
            if st.form_submit_button("🚀 CADASTRAR CLIENTE"):
                prox_id = int(df['id'].max() + 1) if not df.empty else 1
                blob = base64.b64encode(n_img.read()).decode() if n_img else ""
                sheet.append_row([prox_id, n_nome.upper(), n_user, n_senha, n_serv.upper(), n_sist, n_venc.strftime('%Y-%m-%d'), n_custo, n_mensal, n_whats, n_obs, blob])
                st.success("Cliente salvo com sucesso!"); time.sleep(1); st.rerun()

    with t3:
        # ABA DE COBRANÇA
        st.subheader("🚨 FILTROS DE COBRANÇA")
        pix = "\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA O COMPROVANTE!"
        # Filtros rápidos
        f_selecionado = st.radio("Selecione o filtro:", ["Todos", "Vencidos", "Vencendo Hoje", "Vencendo Amanhã"], horizontal=True)
        
        if f_selecionado == "Vencidos": df_c = df[df['dias_res'] < 0]; msg = "🚨 VENCEU!" + pix
        elif f_selecionado == "Vencendo Hoje": df_c = df[df['dias_res'] == 0]; msg = "⏰ VENCE HOJE!" + pix
        elif f_selecionado == "Vencendo Amanhã": df_c = df[df['dias_res'] == 1]; msg = "⏰ VENCE AMANHÃ!" + pix
        else: df_c = df; msg = "Lembrete SUPERTV4K."

        st.divider()
        for _, cli in df_c.iterrows():
            c_c1, c_c2 = st.columns([4, 1])
            c_c1.write(f"👤 **{cli['nome']}** | Vence em: {pd.to_datetime(cli['vencimento']).strftime('%d/%m/%Y')}")
            c_c2.link_button("📲 WHATSAPP", f"https://wa.me/55{cli['whatsapp']}?text={urllib.parse.quote(msg)}")

    with t4:
        st.subheader("⚙️ AJUSTES")
        if st.button("🔄 SINCRONIZAR DADOS"): st.rerun()
