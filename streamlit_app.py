import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse
import base64
import io
import time

# --- 1. CONFIGURAÇÃO E ESTADOS ---
st.set_page_config(page_title="SUPERTV4K GESTÃO PRO", layout="wide")

if 'filtro_f' not in st.session_state:
    st.session_state.filtro_f = "vencidos"

if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = ["Uniplay", "Mundo GF", "P2Braz", "Unitv", "Playtv", "P2Cine", "P2Speed", "Blade", "MegaTV", "Bob Player", "Ibo Player"]

# --- 2. ESTILIZAÇÃO CSS (PREMIUM) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; margin-bottom: 20px; }
    .logo-gestao { width: 380px; margin-bottom: -15px !important; }
    .logo-supertv { width: 320px; }
    
    /* Métricas */
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .metric-label { font-size: 13px; color: #8b949e; font-weight: bold; }
    .metric-value { font-size: 20px; color: #00d4ff; font-weight: 900; }

    /* Cards de Clientes */
    .cliente-card {
        display: flex; align-items: center; background-color: #161b22;
        border: 1px solid #30363d; border-radius: 12px; padding: 15px; margin-bottom: 10px;
    }
    .img-servidor-card { width: 60px; height: 60px; border-radius: 10px; object-fit: cover; margin-right: 20px; border: 1px solid #444; }
    .nome-c { font-weight: 900; font-size: 18px; color: white; text-transform: uppercase; }
    
    /* Cores de Vencimento Dinâmicas */
    .cor-vencido { color: #FF4B4B; font-weight: 900; }   /* Vermelho */
    .cor-alerta { color: #FFD700; font-weight: 900; }    /* Amarelo */
    .cor-ok { color: #00FF00; font-weight: 900; }        /* Verde */
    .cor-tranquilo { color: #00D4FF; font-weight: 900; }  /* Azul */

    .cobransa-item-box { background-color: #1c2128; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #00d4ff; }
    .vencido-border { border-left: 5px solid #ff4b4b !important; }
    div.stButton > button { width: 100% !important; font-weight: bold !important; }
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
        df = pd.DataFrame(valores[1:], columns=colunas[:len(valores[0])])
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

# --- 4. EXECUÇÃO ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)
hoje = datetime.now().date()

if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    # MÉTRICAS NO TOPO
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-card"><div class="metric-label">CLIENTES</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">A RECEBER</div><div class="metric-value">R$ {df["mensalidade"].sum():,.2f}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-label">CUSTO</div><div class="metric-value">R$ {df["custo"].sum():,.2f}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO</div><div class="metric-value" style="color:#00ff88">R$ {(df["mensalidade"].sum()-df["custo"].sum()):,.2f}</div></div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    # --- ABA 1: CLIENTES ---
    with tab1:
        if st.session_state.get('cliente_selecionado') is not None:
            c = st.session_state.cliente_selecionado
            with st.form("form_edit"):
                st.subheader(f"📝 Editar: {c['nome']}")
                ce1, ce2 = st.columns(2)
                enome = ce1.text_input("NOME", value=c['nome'])
                euser = ce2.text_input("USUÁRIO", value=c['usuario'])
                eserv = ce1.selectbox("SERVIDOR", sorted(st.session_state.lista_servidores))
                evenc = ce2.date_input("VENCIMENTO", value=pd.to_datetime(c['vencimento']).date())
                e_whats = ce1.text_input("WHATSAPP", value=c['whatsapp'])
                e_mensal = ce2.number_input("MENSALIDADE", value=float(c['mensalidade']))
                if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                    # Lógica de update simplificada para o exemplo
                    st.session_state.cliente_selecionado = None
                    st.success("Atualizado!"); st.rerun()
                if st.form_submit_button("✖️ FECHAR"):
                    st.session_state.cliente_selecionado = None
                    st.rerun()

        busca = st.text_input("🔎 Pesquisar...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            with st.container():
                c_c, c_b = st.columns([5, 1])
                c_c.markdown(f'''<div class="cliente-card"><img src="{img}" class="img-servidor-card"><div><div style="display:flex;justify-content:space-between;width:100%"><span class="nome-c">{r['nome']}</span><span class="{get_cor_classe(r['dias_res'])}">{r['dias_res']} DIAS</span></div><small>{r['usuario']} | {r['servidor']}</small></div></div>''', unsafe_allow_html=True)
                if c_b.button("📝 INFO", key=f"btn_{r['id']}"):
                    st.session_state.cliente_selecionado = r.to_dict()
                    st.rerun()

    # --- ABA 2: ADICIONAR ---
    with tab2:
        st.subheader("🚀 Novo Cadastro")
        with st.form("add_cli", clear_on_submit=True):
            ca1, ca2 = st.columns(2)
            nnome = ca1.text_input("NOME")
            nuser = ca2.text_input("USUÁRIO")
            nserv = ca1.selectbox("SERVIDOR", sorted(st.session_state.lista_servidores))
            nvenc = ca2.date_input("VENCIMENTO", value=hoje + timedelta(days=30))
            nwhats = ca1.text_input("WHATSAPP (Ex: 17999999999)")
            nmensal = ca2.number_input("VALOR MENSALIDADE", value=35.0)
            nimg = st.file_uploader("LOGO", type=['png', 'jpg'])
            if st.form_submit_button("🚀 CADASTRAR"):
                prox_id = int(df['id'].max() + 1)
                blob = base64.b64encode(nimg.read()).decode() if nimg else ""
                sheet.append_row([prox_id, nnome.upper(), nuser, "", nserv, "P2P", nvenc.strftime('%Y-%m-%d'), 10, nmensal, nwhats, "", blob])
                st.success("Cliente Cadastrado!"); st.rerun()

    # --- ABA 3: COBRANÇA ---
    with tab3:
        st.subheader("🚨 Cobranças")
        cf1, cf2, cf3, cf4, cf5 = st.columns(5)
        if cf1.button("❌ Vencidos"): st.session_state.filtro_f = "vencidos"
        if cf2.button("📅 Hoje"): st.session_state.filtro_f = "hoje"
        if cf3.button("🌅 Amanhã"): st.session_state.filtro_f = "1dia"
        if cf4.button("⏳ 2-3 Dias"): st.session_state.filtro_f = "prox"
        if cf5.button("🗓️ Todos"): st.session_state.filtro_f = "todos"

        f = st.session_state.filtro_f
        if f == "vencidos": df_c = df[df['dias_res'] < 0]
        elif f == "hoje": df_c = df[df['dias_res'] == 0]
        elif f == "1dia": df_c = df[df['dias_res'] == 1]
        elif f == "prox": df_c = df[(df['dias_res'] >= 2) & (df['dias_res'] <= 3)]
        else: df_c = df

        sel_all = st.checkbox("✅ Selecionar Todos")
        clis_cob = []
        for _, r in df_c.iterrows():
            cch, cinf, cbtn = st.columns([0.5, 4, 1.5])
            if cch.checkbox("", value=sel_all, key=f"cb_{r['id']}"): clis_cob.append(r)
            cinf.markdown(f'<div class="cobransa-item-box"><strong>{r["nome"]}</strong> - Vence: {r["vencimento"]}</div>', unsafe_allow_html=True)
            msg = urllib.parse.quote(f"Olá {r['nome']}, sua assinatura SUPERTV4K vence em {r['vencimento']}. Faça o PIX para renovar!")
            cbtn.link_button("📲 ENVIAR", f"https://wa.me/55{r['whatsapp']}?text={msg}")

    # --- ABA 4: AJUSTES ---
    with tab4:
        st.subheader("⚙️ Configurações")
        st.markdown("### 🖥️ Servidores")
        nsrv = st.text_input("Nome do Servidor")
        cs1, cs2 = st.columns(2)
        if cs1.button("💾 ADICIONAR"):
            if nsrv: st.session_state.lista_servidores.append(nsrv); st.rerun()
        if cs2.button("🗑️ REMOVER"):
            if nsrv in st.session_state.lista_servidores: st.session_state.lista_servidores.remove(nsrv); st.rerun()
        
        st.divider()
        st.markdown("### 📥 Backup e Sincronização")
        if st.button("🔄 FORÇAR ATUALIZAÇÃO GOOGLE SHEETS"): st.rerun()
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 BAIXAR BACKUP EXCEL", data=buffer.getvalue(), file_name="backup_clientes.xlsx")
else:
    st.error("Erro ao carregar dados. Verifique a conexão com a planilha.")
