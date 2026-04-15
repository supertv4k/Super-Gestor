import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO", layout="wide")

# --- ESTILIZAÇÃO CSS COMPLETA (VERMELHO + PRATA METALIZADO) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    
    /* Centralização das Logos */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
    }

    /* Estilo das Métricas em Duplas */
    .metric-card {
        background-color: #161b22;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #30363d;
        margin-bottom: 10px;
    }
    .metric-label { font-size: 11px; font-weight: bold; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 22px; font-weight: bold; color: #ff0000; margin-top: 5px; }
    
    /* 1. ESTILO DO BOTÃO DO CLIENTE (EXPANDER) */
    .stExpander { border: none !important; margin-bottom: 10px !important; }
    .stExpander > details > summary {
        background: linear-gradient(135deg, #ff0000 0%, #c0c0c0 100%) !important;
        color: #000000 !important;
        font-weight: bold !important;
        padding: 15px !important;
        border-radius: 10px !important;
        border: 1px solid #ffffff44 !important;
        list-style: none !important;
    }
    .stExpander > details > summary:hover {
        background: linear-gradient(135deg, #d30000 0%, #e0e0e0 100%) !important;
        box-shadow: 0px 4px 15px rgba(255, 0, 0, 0.4);
    }

    /* 2. ESTILO DE TODOS OS BOTÕES (CADASTRAR, SALVAR, +30 DIAS, EXCLUIR, ETC) */
    /* Pegando botões normais e botões de formulário */
    button[kind="primary"], button[kind="secondary"], .stButton>button, .stDownloadButton>button, [data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #ff0000 0%, #c0c0c0 100%) !important;
        color: #000000 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: 1px solid #ffffff33 !important;
        height: 45px !important;
        width: 100% !important;
        transition: 0.3s !important;
        text-transform: uppercase !important;
    }

    button:hover, .stButton>button:hover, [data-testid="stFormSubmitButton"] > button:hover {
        transform: scale(1.02) !important;
        background: linear-gradient(135deg, #d30000 0%, #e0e0e0 100%) !important;
        box-shadow: 0px 4px 15px rgba(255, 0, 0, 0.5) !important;
    }

    /* Estilo para o link do WhatsApp (botão de cobrança) */
    [data-testid="stLinkButton"] > a {
        background: linear-gradient(135deg, #ff0000 0%, #c0c0c0 100%) !important;
        color: #000000 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        padding: 10px !important;
        text-align: center !important;
        text-decoration: none !important;
        display: block !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento DATE, custo REAL, mensalidade REAL, observacao TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    conn.commit()
    conn.close()

init_db()

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    conn.close()
    return lista if lista else ["UNIPlAY", "MUNDOGF", "P2BRAZ"]

# --- HEADER CENTRALIZADO ---
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
c_logo1, c_logo2, c_logo3 = st.columns([1, 3, 1])
with c_logo2:
    l_col1, l_col2 = st.columns(2)
    l_col1.image("https://i.imgur.com/CKq9BVx.png", use_container_width=True)
    l_col2.image("https://i.imgur.com/OkUAPQa.png", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- DASHBOARD (MÉTRICAS EM DUPLAS) ---
if not df.empty:
    hoje = datetime.now().date()
    df['venc_dt'] = pd.to_datetime(df['vencimento']).dt.date
    df['dias_restantes'] = (df['venc_dt'] - hoje).apply(lambda x: x.days)
    
    total, bruto, custos = len(df), df['mensalidade'].sum(), df['custo'].sum()
    em_dia = len(df[df['dias_restantes'] > 0])
    vencidos = len(df[df['dias_restantes'] < 0])
    vence_3d = len(df[(df['dias_restantes'] >= 0) & (df['dias_restantes'] <= 3)])

    m1, m2 = st.columns(2); m1.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL CLIENTES</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True); m2.markdown(f'<div class="metric-card"><div class="metric-label">EM DIA</div><div class="metric-value">{em_dia}</div></div>', unsafe_allow_html=True)
    m3, m4 = st.columns(2); m3.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value">{vencidos}</div></div>', unsafe_allow_html=True); m4.markdown(f'<div class="metric-card"><div class="metric-label">VENCE EM 3 DIAS</div><div class="metric-value">{vence_3d}</div></div>', unsafe_allow_html=True)
    m5, m6 = st.columns(2); m5.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO BRUTO</div><div class="metric-value">R$ {bruto:,.2f}</div></div>', unsafe_allow_html=True); m6.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO LÍQUIDO</div><div class="metric-value">R$ {bruto-custos:,.2f}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-card"><div class="metric-label">CUSTOS COM CRÉDITOS</div><div class="metric-value">R$ {custos:,.2f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👥 CLIENTES", "➕ ADD CLIENTE", "📢 COBRANÇA", "⚙️ CONFIG"])

with tab1:
    busca = st.text_input("🔍 PESQUISAR NOME OU USUÁRIO...")
    if not df.empty:
        for _, r in df.iterrows():
            if busca.lower() in r['nome'].lower() or busca.lower() in str(r['usuario']).lower():
                # O NOME DO CLIENTE AGORA APARECE NO BOTÃO COM DEGRADÊ
                header_text = f"👤 {r['nome'].upper()} | U: {r['usuario']} | S: {r['senha']} | ({r.get('sistema', 'IPTV')})"
                with st.expander(header_text):
                    with st.form(key=f"ed_form_{r['id']}"):
                        c1, c2 = st.columns(2)
                        en, ew = c1.text_input("Nome", value=r['nome']), c2.text_input("WhatsApp", value=r['whatsapp'])
                        c3, c4 = st.columns(2)
                        eu, es = c3.text_input("Usuário", value=r['usuario']), c4.text_input("Senha", value=r['senha'])
                        
                        srv_list = get_servidores()
                        esrv = st.selectbox("Servidor", srv_list, index=srv_list.index(r['servidor']) if r['servidor'] in srv_list else 0)
                        
                        c5, c6, c7 = st.columns(3)
                        ev = c5.date_input("Vencimento", value=pd.to_datetime(r['vencimento']).date())
                        em = c6.number_input("Mensalidade R$", value=float(r['mensalidade']))
                        esis = c7.radio("Sistema", ["IPTV", "P2P"], index=0 if r.get('sistema') == "IPTV" else 1, horizontal=True)
                        
                        st.divider()
                        b_save, b_renew, b_del = st.columns(3)
                        if b_save.form_submit_button("💾 SALVAR"):
                            conn = sqlite3.connect('supertv_gestao.db'); conn.execute("UPDATE clientes SET nome=?, whatsapp=?, usuario=?, senha=?, servidor=?, vencimento=?, mensalidade=?, sistema=? WHERE id=?", (en, ew, eu, es, esrv, str(ev), em, esis, r['id'])); conn.commit(); st.rerun()
                        if b_renew.form_submit_button("🔄 +30 DIAS"):
                            nova = pd.to_datetime(r['vencimento']).date() + timedelta(days=30)
                            conn = sqlite3.connect('supertv_gestao.db'); conn.execute("UPDATE clientes SET vencimento=? WHERE id=?", (str(nova), r['id'])); conn.commit(); st.rerun()
                        if b_del.form_submit_button("🗑️ EXCLUIR"):
                            conn = sqlite3.connect('supertv_gestao.db'); conn.execute("DELETE FROM clientes WHERE id=?", (r['id'],)); conn.commit(); st.rerun()

with tab2:
    with st.form("add_cli", clear_on_submit=True):
        st.subheader("Novo Cadastro")
        n, w = st.text_input("NOME"), st.text_input("WHATSAPP")
        c1, c2 = st.columns(2); u, s = c1.text_input("USER"), c2.text_input("SENHA")
        srv = st.selectbox("SERVIDOR", get_servidores())
        v = st.date_input("VENCIMENTO", value=datetime.now() + timedelta(days=30))
        c3, c4, c5 = st.columns(3)
        cu, me = c3.number_input("CUSTO", 0.0), c4.number_input("VALOR", 35.0)
        sis = c5.radio("SISTEMA", ["IPTV", "P2P"], horizontal=True)
        if st.form_submit_button("🚀 CADASTRAR"):
            conn = sqlite3.connect('supertv_gestao.db'); conn.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, vencimento, custo, mensalidade, sistema) VALUES (?,?,?,?,?,?,?,?,?)", (n, w, u, s, srv, str(v), cu, me, sis)); conn.commit(); st.success("Cadastrado!"); st.rerun()

with tab3:
    st.subheader("📢 Central de Cobrança")
    pix_chave = "62.326.879/0001-13"
    if not df.empty:
        df_cob = df[df['dias_restantes'] <= 3]
        for _, c in df_cob.iterrows():
            msg = f"Olá {c['nome']}! Sua assinatura vence em breve. Renove via PIX: {pix_chave}"
            st.link_button(f"Enviar para {c['nome']}", f"https://wa.me/{c['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Configurações")
    new_srv = st.text_input("Novo Servidor")
    if st.button("➕ ADICIONAR"):
        if new_srv:
            conn = sqlite3.connect('supertv_gestao.db'); conn.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (new_srv,)); conn.commit(); st.success("Adicionado!"); st.rerun()
    st.divider()
    if not df.empty:
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        st.download_button("📥 BAIXAR LISTA EXCEL", data=buf.getvalue(), file_name="backup_supertv.xlsx")
