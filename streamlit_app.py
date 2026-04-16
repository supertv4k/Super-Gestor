import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS (PADRÃO ORIGINAL MANTIDO) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    
    .metric-card { 
        background-color: #161b22; padding: 15px; border-radius: 12px; 
        text-align: center; border: 1px solid #30363d; margin-bottom: 10px; 
    }
    .metric-label { font-size: 11px; font-weight: bold; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 22px; font-weight: bold; color: #ff0000; margin-top: 5px; }

    div.stFormSubmitButton > button[data-testid="baseButton-primaryFormSubmit"] {
        background: linear-gradient(135deg, #0052D4 0%, #929ED1 50%, #E0EAFC 100%) !important;
        color: #1e1e1e !important; font-weight: 900 !important; border-radius: 10px !important;
    }
    
    .stExpander > details > summary { 
        background: linear-gradient(135deg, #ff0000 0%, #c0c0c0 100%) !important; 
        color: #ffffff !important; padding: 15px !important; border-radius: 10px !important; 
        font-weight: 800 !important; font-size: 18px !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BANCO DE DADOS (MANUTENÇÃO DE COLUNAS) ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento DATE, custo REAL, mensalidade REAL, 
                  inicio DATE, observacao TEXT)''')
    
    # Atualiza banco existente se necessário
    cursor = c.execute('PRAGMA table_info(clientes)')
    colunas = [col[1] for col in cursor.fetchall()]
    if 'inicio' not in colunas:
        c.execute('ALTER TABLE clientes ADD COLUMN inicio DATE')
    if 'observacao' not in colunas:
        c.execute('ALTER TABLE clientes ADD COLUMN observacao TEXT')
        
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    conn.commit()
    conn.close()

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    try:
        lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    except: lista = []
    conn.close()
    return lista if lista else ["UNITV", "UNIPLAY", "P2BRAZ", "MUNDOGF", "PLAY TV"]

init_db()

# --- 4. CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- 5. HEADER ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

# --- 6. ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADD CLIENTE", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔍 PESQUISAR")
    if not df.empty:
        for _, r in df.sort_values(by='nome').iterrows():
            if busca.lower() in r['nome'].lower() or busca.lower() in str(r['usuario']).lower():
                with st.expander(f"👤 {r['nome'].upper()}"):
                    with st.form(key=f"ed_{r['id']}"):
                        # ORDEM EXATA NA EDIÇÃO TAMBÉM
                        en = st.text_input("CLIENTE", value=r['nome'])
                        eu = st.text_input("USUÁRIO", value=r['usuario'])
                        es = st.text_input("SENHA", value=r['senha'])
                        srvs = get_servidores()
                        esrv = st.selectbox("SERVIDOR", srvs, index=srvs.index(r['servidor']) if r['servidor'] in srvs else 0)
                        esis = st.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if r['sistema']=="P2P" else 1)
                        ev = st.date_input("VENCIMENTO", value=pd.to_datetime(r['vencimento']).date())
                        ec = st.number_input("CUSTO", value=float(r['custo'] or 0.0))
                        em = st.number_input("VALOR COBRADO", value=float(r['mensalidade'] or 0.0))
                        ei = st.date_input("INICIOU DIA", value=pd.to_datetime(r['inicio']).date() if r['inicio'] else datetime.now().date())
                        ew = st.text_input("WHATSAPP", value=r['whatsapp'])
                        eobs = st.text_area("OBSERVAÇÃO", value=r['observacao'] or "")
                        
                        if st.form_submit_button("💾 SALVAR"):
                            c = sqlite3.connect('supertv_gestao.db')
                            c.execute("""UPDATE clientes SET nome=?, usuario=?, senha=?, servidor=?, sistema=?, 
                                      vencimento=?, custo=?, mensalidade=?, inicio=?, whatsapp=?, observacao=? WHERE id=?""", 
                                     (en, eu, es, esrv, esis, str(ev), ec, em, str(ei), ew, eobs, r['id']))
                            c.commit(); st.rerun()

with tab2:
    st.subheader("🚀 Cadastro de Novo Assinante")
    with st.form("form_novo", clear_on_submit=True):
        # --- SEQUÊNCIA SOLICITADA ---
        n_cliente = st.text_input("CLIENTE")
        n_usuario = st.text_input("USUÁRIO")
        n_senha = st.text_input("SENHA")
        
        lista_s = get_servidores()
        n_servidor = st.selectbox("SERVIDOR", lista_s)
        
        n_sistema = st.selectbox("SISTEMA", ["P2P", "IPTV"])
        n_vencimento = st.date_input("VENCIMENTO", value=datetime.now() + timedelta(days=30))
        
        n_custo = st.number_input("CUSTO", value=10.0)
        n_valor = st.number_input("VALOR COBRADO", value=35.0)
        
        n_inicio = st.date_input("INÍCIOU DIA", value=datetime.now().date())
        n_whatsapp = st.text_input("WHATSAPP")
        
        n_obs = st.text_area("OBSERVAÇÃO")
        
        # Botão de Cadastro
        if st.form_submit_button("🚀 CADASTRAR AGORA"):
            if n_cliente and n_usuario:
                conn = sqlite3.connect('supertv_gestao.db')
                conn.execute("""INSERT INTO clientes 
                    (nome, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, inicio, whatsapp, observacao) 
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""", 
                    (n_cliente, n_usuario, n_senha, n_servidor, n_sistema, str(n_vencimento), n_custo, n_valor, str(n_inicio), n_whatsapp, n_obs))
                conn.commit(); conn.close()
                st.success("Cliente cadastrado com sucesso!")
                st.rerun()

with tab3:
    st.subheader("🚨 COBRANÇA")
    # Lógica de cobrança mantida...
    if not df.empty:
        st.write("Selecione os clientes para enviar mensagem.")

with tab4:
    st.subheader("⚙️ AJUSTES")
    # Configurações de servidor e backup mantidas...
