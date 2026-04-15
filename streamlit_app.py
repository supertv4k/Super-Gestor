import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS COMPLETA (DESIGN METALIZADO E TEXTO BRANCO) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    
    /* Centralização das Logos */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 25px;
    }

    /* Cards de Métricas (Organizados de 2 em 2) */
    .metric-card {
        background-color: #161b22;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #30363d;
        margin-bottom: 10px;
    }
    .metric-label { font-size: 11px; font-weight: bold; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 24px; font-weight: bold; color: #ff0000; margin-top: 5px; }
    
    /* BOTÕES GERAIS E DE FORMULÁRIO */
    div.stButton > button, 
    div.stDownloadButton > button, 
    div.stFormSubmitButton > button,
    [data-testid="stLinkButton"] > a {
        background: linear-gradient(135deg, #ff0000 0%, #c0c0c0 100%) !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        font-size: 16px !important;
        border-radius: 10px !important;
        border: 2px solid #ffffff44 !important;
        height: 50px !important;
        width: 100% !important;
        text-transform: uppercase !important;
        transition: 0.4s !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3) !important;
    }

    /* O FAMOSO BOTÃO DO CLIENTE (EXPANDER) */
    .stExpander { border: none !important; margin-bottom: 15px !important; }
    .stExpander > details > summary {
        background: linear-gradient(135deg, #ff0000 0%, #c0c0c0 100%) !important;
        color: #ffffff !important;
        padding: 12px 15px !important;
        border-radius: 12px !important;
        border: 2px solid #ffffff44 !important;
        list-style: none !important;
    }

    /* EFEITO HOVER */
    button:hover, summary:hover, a:hover {
        transform: scale(1.01) !important;
        filter: brightness(1.1) !important;
        box-shadow: 0px 0px 20px rgba(255, 0, 0, 0.5) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento DATE, custo REAL, mensalidade REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    conn.commit()
    conn.close()

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    conn.close()
    return lista if lista else ["UNIPlAY", "MUNDOGF", "P2BRAZ"]

init_db()

# --- 4. HEADER (LOGOS) ---
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
col_a, col_b, col_c = st.columns([1, 4, 1])
with col_b:
    img_col1, img_col2 = st.columns(2)
    img_col1.image("https://i.imgur.com/CKq9BVx.png", use_container_width=True) # Supertv4k
    img_col2.image("https://i.imgur.com/OkUAPQa.png", use_container_width=True) # Gestão
st.markdown('</div>', unsafe_allow_html=True)

# --- 5. CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- 6. DASHBOARD DE MÉTRICAS (DUAS EM DUAS) ---
if not df.empty:
    hoje = datetime.now().date()
    df['venc_dt'] = pd.to_datetime(df['vencimento']).dt.date
    df['dias_res'] = (df['venc_dt'] - hoje).apply(lambda x: x.days)
    
    total, bruto, custos = len(df), df['mensalidade'].sum(), df['custo'].sum()
    em_dia = len(df[df['dias_res'] > 0])
    vencidos = len(df[df['dias_res'] < 0])
    vence_3d = len(df[(df['dias_res'] >= 0) & (df['dias_res'] <= 3)])

    m1, m2 = st.columns(2)
    with m1: st.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL CLIENTES</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="metric-card"><div class="metric-label">EM DIA</div><div class="metric-value">{em_dia}</div></div>', unsafe_allow_html=True)
    
    m3, m4 = st.columns(2)
    with m3: st.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value">{vencidos}</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="metric-card"><div class="metric-label">VENCE EM 3 DIAS</div><div class="metric-value">{vence_3d}</div></div>', unsafe_allow_html=True)
    
    m5, m6 = st.columns(2)
    with m5: st.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO BRUTO</div><div class="metric-value">R$ {bruto:,.2f}</div></div>', unsafe_allow_html=True)
    with m6: st.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO LÍQUIDO</div><div class="metric-value">R$ {bruto-custos:,.2f}</div></div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="metric-card"><div class="metric-label">CUSTOS COM CRÉDITOS</div><div class="metric-value">R$ {custos:,.2f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 7. ABAS PRINCIPAIS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 GESTÃO", "➕ CADASTRAR", "📢 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔍 PESQUISAR CLIENTE OU USUÁRIO")
    if not df.empty:
        for _, r in df.iterrows():
            if busca.lower() in r['nome'].lower() or busca.lower() in str(r['usuario']).lower():
                
                # DESIGN DO CABEÇALHO: NOME (CIMA) | INFO (BAIXO)
                header_format = f"👤 {r['nome'].upper()} \n U: {r['usuario']} | S: {r['senha']} | ({r.get('sistema', 'IPTV')})"
                
                with st.expander(header_format):
                    # Forçando o texto branco e grande dentro do expander via Markdown
                    st.markdown(f"""
                    <div style='background-color: #161b22; padding: 10px; border-radius: 5px; border-left: 5px solid red;'>
                        <h2 style='color: white; margin-bottom: 0px;'>{r['nome'].upper()}</h2>
                        <p style='color: #c0c0c0; font-size: 18px;'><b>User:</b> {r['usuario']} | <b>Senha:</b> {r['senha']} | <b>Sist:</b> {r.get('sistema', 'IPTV')}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.form(key=f"edit_form_{r['id']}"):
                        c1, c2 = st.columns(2)
                        en = c1.text_input("Nome", value=r['nome'])
                        ew = c2.text_input("WhatsApp", value=r['whatsapp'])
                        
                        c3, c4 = st.columns(2)
                        eu = c3.text_input("Usuário", value=r['usuario'])
                        es = c4.text_input("Senha", value=r['senha'])
                        
                        srv_list = get_servidores()
                        esrv = st.selectbox("Servidor", srv_list, index=srv_list.index(r['servidor']) if r['servidor'] in srv_list else 0)
                        
                        c5, c6, c7 = st.columns(3)
                        ev = c5.date_input("Vencimento", value=pd.to_datetime(r['vencimento']).date())
                        em = c6.number_input("Mensalidade R$", value=float(r['mensalidade']))
                        esis = c7.radio("Sistema", ["IPTV", "P2P"], index=0 if r.get('sistema') == "IPTV" else 1, horizontal=True)
                        
                        st.divider()
                        b_save, b_renew, b_del = st.columns(3)
                        
                        if b_save.form_submit_button("💾 SALVAR"):
                            conn = sqlite3.connect('supertv_gestao.db')
                            conn.execute("UPDATE clientes SET nome=?, whatsapp=?, usuario=?, senha=?, servidor=?, vencimento=?, mensalidade=?, sistema=? WHERE id=?", (en, ew, eu, es, esrv, str(ev), em, esis, r['id']))
                            conn.commit(); st.rerun()

                        if b_renew.form_submit_button("🔄 +30 DIAS"):
                            nova_data = pd.to_datetime(r['vencimento']).date() + timedelta(days=30)
                            conn = sqlite3.connect('supertv_gestao.db')
                            conn.execute("UPDATE clientes SET vencimento=? WHERE id=?", (str(nova_data), r['id']))
                            conn.commit(); st.success("Renovado!"); st.rerun()
                        
                        if b_del.form_submit_button("🗑️ EXCLUIR"):
                            conn = sqlite3.connect('supertv_gestao.db')
                            conn.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                            conn.commit(); st.rerun()

with tab2:
    with st.form("cad_novo", clear_on_submit=True):
        st.subheader("🚀 Novo Cliente")
        f1, f2 = st.columns(2); n = f1.text_input("NOME"); w = f2.text_input("WHATSAPP")
        f3, f4 = st.columns(2); u = f3.text_input("USER"); s = f4.text_input("SENHA")
        srv = st.selectbox("SERVIDOR", get_servidores())
        v = st.date_input("VENCIMENTO", value=datetime.now() + timedelta(days=30))
        f5, f6, f7 = st.columns(3)
        cu = f5.number_input("CUSTO", 0.0); me = f6.number_input("VALOR", 35.0)
        si = f7.radio("SISTEMA", ["IPTV", "P2P"], horizontal=True)
        if st.form_submit_button("🚀 CADASTRAR AGORA"):
            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, vencimento, custo, mensalidade, sistema) VALUES (?,?,?,?,?,?,?,?,?)", (n, w, u, s, srv, str(v), cu, me, si))
            conn.commit(); st.success("Cadastrado!"); st.rerun()

with tab3:
    st.subheader("📢 Cobrança")
    pix_chave = "62.326.879/0001-13"
    if not df.empty:
        df_c = df[df['dias_res'] <= 3]
        for _, c in df_c.iterrows():
            msg = f"Olá {c['nome']}! Sua assinatura Supertv4k vence em breve. Renove via PIX: {pix_chave}"
            st.link_button(f"📲 ENVIAR PARA {c['nome']}", f"https://wa.me/{c['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Ajustes")
    ns = st.text_input("Nome do Servidor")
    if st.button("➕ ADICIONAR"):
        if ns:
            conn = sqlite3.connect('supertv_gestao.db'); conn.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (ns,)); conn.commit(); st.rerun()
    st.divider()
    if not df.empty:
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        st.download_button("📥 BAIXAR EXCEL (BACKUP)", data=buf.getvalue(), file_name="backup_supertv.xlsx")
