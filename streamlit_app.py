import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io
import base64

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    
    /* Estilo para a lista de cobrança e cartões */
    .cliente-row { border-radius: 12px; padding: 12px; margin-bottom: 10px; display: flex; align-items: center; gap: 20px; border: 1px solid #30363d; }
    .row-vencido { background-color: #331111; border-left: 8px solid #ff4b4b; }
    .row-hoje { background-color: #3d2b11; border-left: 8px solid #ffa500; }
    .row-breve { background-color: #333311; border-left: 8px solid #ffff00; }
    .row-em-dia { background-color: #112233; border-left: 8px solid #00d4ff; }
    
    .logo-externa { width: 85px; height: 85px; border-radius: 10px; object-fit: contain; background: #21262d; border: 1px solid #444; }
    .info-container { flex-grow: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .info-txt { font-size: 14px; color: #ffffff; }
    
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 12px; text-align: center; border: 1px solid #30363d; margin-bottom: 10px; }
    .metric-label { font-size: 11px; font-weight: bold; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 20px; font-weight: bold; color: #ffffff; margin-top: 5px; }
    
    /* Estilo dos botões de cliente */
    div.stButton > button {
        width: 100%;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 20px !important;
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: white !important;
        border-radius: 12px !important;
    }
    div.stButton > button:hover {
        border-color: #00d4ff !important;
        background-color: #1c2128 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES AUXILIARES ---
def image_to_base64(image_file):
    if image_file is not None:
        try: return base64.b64encode(image_file.read()).decode()
        except: return None
    return None

def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento TEXT, custo REAL, mensalidade REAL, 
                  inicio TEXT, observacao TEXT, logo_blob TEXT)''')
    conn.commit(); conn.close()

def get_servidores():
    return ["UNITV", "UNIPLAY", "P2BRAZ", "MUNDOGF", "PLAY TV", "TV EXPRESS", "REDPLAY"]

init_db()

# --- 4. CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- 5. HEADER ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

# --- 6. DASHBOARD ---
if not df.empty:
    hoje = datetime.now().date()
    df['mensalidade'] = pd.to_numeric(df['mensalidade'], errors='coerce').fillna(0)
    df['custo'] = pd.to_numeric(df['custo'], errors='coerce').fillna(0)
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 0)
    
    bruto = df['mensalidade'].sum()
    custos = df['custo'].sum()
    liquido = bruto - custos
    vencidos = len(df[df["dias_res"] < 0])
    vencendo_3 = len(df[(df["dias_res"] >= 0) & (df["dias_res"] <= 3)])

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">CLIENTES</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value" style="color:#ff4b4b;">{vencidos}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">3 DIAS</div><div class="metric-value" style="color:#ffff00;">{vencendo_3}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">BRUTO</div><div class="metric-value" style="color:#00ff00;">R${bruto:,.0f}</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-label">LÍQUIDO</div><div class="metric-value" style="color:#00d4ff;">R${liquido:,.0f}</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="metric-card"><div class="metric-label">CUSTOS</div><div class="metric-value">R${custos:,.0f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 7. ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADD CLIENTE", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔎 Pesquisar cliente...", placeholder="Digite nome ou usuário...")
    if not df.empty:
        df_f = df[df['nome'].notnull() & (df['nome'].astype(str).str.strip() != '')].copy()
        if busca:
            df_f = df_f[df_f['nome'].str.contains(busca, case=False, na=False) | df_f['usuario'].str.contains(busca, case=False, na=False)]

        for _, r in df_f.sort_values(by='nome').iterrows():
            label_btn = f"👤 {str(r['nome']).upper()}  |  🔑 {r['usuario']}  |  📶 {r['servidor']}"
            
            # Cada cliente vira um botão que abre um expansor de detalhes
            if st.button(label_btn, key=f"btn_{r['id']}"):
                with st.container():
                    st.info(f"Detalhes do Cliente: {r['nome']}")
                    det1, det2, det3 = st.columns(3)
                    det1.write(f"**WhatsApp:** {r['whatsapp']}")
                    det1.write(f"**Senha:** {r['senha']}")
                    det2.write(f"**Vencimento:** {r['vencimento']}")
                    det2.write(f"**Sistema:** {r['sistema'] if r['sistema'] else 'N/A'}")
                    det3.write(f"**Mensalidade:** R$ {r['mensalidade']:.2f}")
                    det3.write(f"**Custo:** R$ {r['custo']:.2f}")
                    st.write(f"**Observações:** {r['observacao'] if r['observacao'] else 'Nenhuma'}")
                    st.divider()

with tab2:
    st.subheader("🚀 Cadastro de Cliente")
    with st.form("add"):
        c1, c2 = st.columns(2)
        n_n = c1.text_input("NOME DO CLIENTE")
        n_u = c2.text_input("USUÁRIO")
        n_s = c1.text_input("SENHA")
        n_srv = c2.selectbox("SERVIDOR", get_servidores())
        n_v = c1.date_input("VENCIMENTO", value=datetime.now().date()+timedelta(days=30))
        n_sis = c2.text_input("SISTEMA (Ex: Android, TV Box)")
        n_c = c1.number_input("CUSTO (R$)", value=10.0)
        n_m = c2.number_input("MENSALIDADE (R$)", value=35.0)
        n_w = st.text_input("WHATSAPP (Ex: 62999999999)")
        n_obs = st.text_area("OBSERVAÇÕES")
        n_l = st.file_uploader("LOGOMARCA", type=['png','jpg'])
        if st.form_submit_button("🚀 SALVAR CLIENTE"):
            if n_n.strip() == "": st.error("O nome é obrigatório!")
            else:
                l_b = image_to_base64(n_l)
                conn = sqlite3.connect('supertv_gestao.db')
                conn.execute("""INSERT INTO clientes 
                             (nome, usuario, senha, servidor, vencimento, sistema, custo, mensalidade, whatsapp, observacao, logo_blob) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                            (n_n, n_u, n_s, n_srv, n_v.strftime('%Y-%m-%d'), n_sis, n_c, n_m, n_w, n_obs, l_b))
                conn.commit(); conn.close(); st.rerun()

with tab3:
    st.subheader("🚨 Cobranças")
    pix = "62.326.879/0001-13"
    if not df.empty:
        sel_todos = st.toggle("✅ Selecionar Todos")
        clientes_selecionados = []
        for idx, c in df.sort_values(by='dias_res').iterrows():
            if c['dias_res'] < 0: cls, status = "row-vencido", "🔴 VENCIDO"
            elif c['dias_res'] == 0: cls, status = "row-hoje", "🟠 HOJE"
            elif 1 <= c['dias_res'] <= 3: cls, status = "row-breve", "🟡 1-3 DIAS"
            else: cls, status = "row-em-dia", "🔵 EM DIA"
            
            col_ch, col_ca = st.columns([0.1, 0.9])
            with col_ch:
                if st.checkbox("", value=sel_todos, key=f"cob_{idx}"): clientes_selecionados.append(c)
            with col_ca:
                st.markdown(f'<div class="cliente-row {cls}"><b>{str(c["nome"]).upper()}</b> | {status} | Vence: {c["vencimento"]} ({c["dias_res"]} dias)</div>', unsafe_allow_html=True)
        
        if st.button(f"📲 DISPARAR ({len(clientes_selecionados)})", use_container_width=True):
            for item in clientes_selecionados:
                msg = f"Olá {str(item['nome']).split()[0]}! 👋 Sua assinatura {item['servidor']} vence em {item['dias_res']} dias. Valor: R$ {item['mensalidade']:.2f}. Pix: {pix}"
                st.link_button(f"Enviar para {item['nome']}", f"https://wa.me/55{item['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Manutenção")
    if st.button("🗑️ LIMPAR INVÁLIDOS"):
        conn = sqlite3.connect('supertv_gestao.db')
        conn.execute("DELETE FROM clientes WHERE nome IS NULL OR nome = ''")
        conn.commit(); conn.close(); st.success("Banco limpo!"); st.rerun()
