import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO", layout="wide")

# --- ESTILIZAÇÃO CSS (FOCO EM CENTRALIZAÇÃO E MÉTRICAS EM DUPLAS) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    
    /* Centralização das Logos */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 20px;
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
    .metric-label { font-size: 12px; font-weight: bold; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 24px; font-weight: bold; color: #ff4b4b; margin-top: 5px; }
    
    /* Botão de Nome do Cliente (Expander) */
    .stExpander { border: none !important; margin-bottom: 10px !important; }
    .stExpander > details > summary {
        background-color: #21262d !important;
        padding: 12px !important;
        border-radius: 8px !important;
        color: #ff4b4b !important;
        font-weight: bold !important;
        border: 1px solid #30363d !important;
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

# --- HEADER CENTRALIZADO (LOGOS) ---
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
col_logo_1, col_logo_2, col_logo_3 = st.columns([1, 2, 1])
with col_logo_2:
    c_img1, c_img2 = st.columns(2)
    c_img1.image("https://i.imgur.com/CKq9BVx.png", use_container_width=True) # Supertv4k
    c_img2.image("https://i.imgur.com/OkUAPQa.png", use_container_width=True) # Gestão
st.markdown('</div>', unsafe_allow_html=True)

# --- CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- DASHBOARD DE MÉTRICAS (DE DUAS EM DUAS) ---
if not df.empty:
    hoje = datetime.now().date()
    df['venc_dt'] = pd.to_datetime(df['vencimento']).dt.date
    df['dias_restantes'] = (df['venc_dt'] - hoje).apply(lambda x: x.days)
    
    total = len(df)
    em_dia = len(df[df['dias_restantes'] > 0])
    vencidos = len(df[df['dias_restantes'] < 0])
    vence_3d = len(df[(df['dias_restantes'] >= 0) & (df['dias_restantes'] <= 3)])
    bruto = df['mensalidade'].sum()
    custos = df['custo'].sum()
    liquido = bruto - custos

    # Linha 1
    m1, m2 = st.columns(2)
    with m1: st.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL DE CLIENTES</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="metric-card"><div class="metric-label">CLIENTES EM DIA</div><div class="metric-value">{em_dia}</div></div>', unsafe_allow_html=True)
    
    # Linha 2
    m3, m4 = st.columns(2)
    with m3: st.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value">{vencidos}</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="metric-card"><div class="metric-label">VENCE EM 3 DIAS</div><div class="metric-value">{vence_3d}</div></div>', unsafe_allow_html=True)
    
    # Linha 3
    m5, m6 = st.columns(2)
    with m5: st.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO BRUTO</div><div class="metric-value">R$ {bruto:,.2f}</div></div>', unsafe_allow_html=True)
    with m6: st.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO LÍQUIDO</div><div class="metric-value">R$ {liquido:,.2f}</div></div>', unsafe_allow_html=True)
    
    # Linha final (Custo Único)
    st.markdown(f'<div class="metric-card"><div class="metric-label">CUSTOS COM CRÉDITOS</div><div class="metric-value">R$ {custos:,.2f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👥 CLIENTES", "➕ ADD CLIENTE", "📢 COBRANÇA", "⚙️ CONFIG"])

with tab1:
    busca = st.text_input("🔍 PESQUISAR NOME...")
    if not df.empty:
        for _, r in df.iterrows():
            if busca.lower() in r['nome'].lower():
                # NOME DO CLIENTE COMO BOTÃO DE EXPANSÃO
                with st.expander(f"👤 {r['nome'].upper()}"):
                    with st.form(key=f"ed_form_{r['id']}"):
                        col1, col2 = st.columns(2)
                        en = col1.text_input("Nome", value=r['nome'])
                        ew = col2.text_input("WhatsApp", value=r['whatsapp'])
                        
                        col3, col4 = st.columns(2)
                        eu = col3.text_input("Usuário", value=r['usuario'])
                        es = col4.text_input("Senha", value=r['senha'])
                        
                        srv_list = get_servidores()
                        esrv = st.selectbox("Servidor", srv_list, index=srv_list.index(r['servidor']) if r['servidor'] in srv_list else 0)
                        
                        col5, col6 = st.columns(2)
                        ev = col5.date_input("Vencimento", value=pd.to_datetime(r['vencimento']).date())
                        em = col6.number_input("Mensalidade R$", value=float(r['mensalidade']))
                        
                        st.divider()
                        # BOTÕES DE AÇÃO
                        b_save, b_renew, b_del = st.columns(3)
                        
                        if b_save.form_submit_button("💾 SALVAR"):
                            conn = sqlite3.connect('supertv_gestao.db')
                            conn.execute("UPDATE clientes SET nome=?, whatsapp=?, usuario=?, senha=?, servidor=?, vencimento=?, mensalidade=? WHERE id=?", (en, ew, eu, es, esrv, str(ev), em, r['id']))
                            conn.commit(); st.rerun()

                        if b_renew.form_submit_button("🔄 +30 DIAS"):
                            nova_data = pd.to_datetime(r['vencimento']).date() + timedelta(days=30)
                            conn = sqlite3.connect('supertv_gestao.db')
                            conn.execute("UPDATE clientes SET vencimento=? WHERE id=?", (str(nova_data), r['id']))
                            conn.commit(); st.success(f"Renovado para {nova_data.strftime('%d/%m/%Y')}"); st.rerun()
                        
                        if b_del.form_submit_button("🗑️ EXCLUIR"):
                            conn = sqlite3.connect('supertv_gestao.db')
                            conn.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                            conn.commit(); st.rerun()

with tab2:
    with st.form("add_cli", clear_on_submit=True):
        st.subheader("Novo Cadastro")
        n = st.text_input("NOME")
        w = st.text_input("WHATSAPP")
        c1, c2 = st.columns(2); u = c1.text_input("USER"); s = c2.text_input("SENHA")
        srv = st.selectbox("SERVIDOR", get_servidores())
        v = st.date_input("VENCIMENTO", value=datetime.now() + timedelta(days=30))
        c3, c4 = st.columns(2); cu = c3.number_input("CUSTO", 0.0); me = c4.number_input("MENSALIDADE", 35.0)
        if st.form_submit_button("🚀 CADASTRAR"):
            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, vencimento, custo, mensalidade) VALUES (?,?,?,?,?,?,?,?)", (n, w, u, s, srv, str(v), cu, me))
            conn.commit(); st.success("Cadastrado!"); st.rerun()

with tab3:
    st.subheader("📢 Central de Cobrança")
    pix_chave = "62.326.879/0001-13"
    if not df.empty:
        df_cob = df[df['dias_restantes'] <= 3]
        for _, c in df_cob.iterrows():
            msg = f"Olá {c['nome']}! Sua assinatura vence em breve. Renove via PIX: {pix_chave}"
            st.link_button(f"Enviar WhatsApp para {c['nome']}", f"https://wa.me/{c['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Configurações")
    new_srv = st.text_input("Novo Servidor")
    if st.button("➕ ADICIONAR"):
        if new_srv:
            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (new_srv,))
            conn.commit(); st.success("Adicionado!"); st.rerun()
    
    st.divider()
    if not df.empty:
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        st.download_button("📥 BAIXAR EXCEL", data=buf.getvalue(), file_name="backup_clientes.xlsx")
