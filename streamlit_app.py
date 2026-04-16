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

# --- 3. BANCO DE DADOS (FORÇANDO ATUALIZAÇÃO DE COLUNAS) ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento DATE, custo REAL, mensalidade REAL, 
                  inicio DATE, observacao TEXT)''')
    
    # Verificação de segurança: Adiciona colunas novas caso o banco seja antigo
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

if 'selecionados' not in st.session_state: st.session_state.selecionados = []

# --- 5. HEADER ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

# --- 6. DASHBOARD ---
if not df.empty:
    hoje = datetime.now().date()
    df['venc_dt'] = pd.to_datetime(df['vencimento']).dt.date
    df['dias_res'] = (df['venc_dt'] - hoje).apply(lambda x: x.days)
    bruto, custos = df['mensalidade'].sum(), df['custo'].sum()
    liquido = bruto - custos
    c1, c2, c3 = st.columns(3); c4, c5, c6 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL CLIENTES</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value">{len(df[df["dias_res"] < 0])}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">VENCEM EM 3 DIAS</div><div class="metric-value">{len(df[(df["dias_res"] >= 0) & (df["dias_res"] <= 3)])}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO BRUTO</div><div class="metric-value">R$ {bruto:,.2f}</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO LÍQUIDO</div><div class="metric-value">R$ {liquido:,.2f}</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="metric-card"><div class="metric-label">CUSTO CRÉDITOS</div><div class="metric-value">R$ {custos:,.2f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 7. ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADD CLIENTE", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔍 PESQUISAR POR NOME OU USUÁRIO")
    if not df.empty:
        for _, r in df.sort_values(by='nome').iterrows():
            if busca.lower() in r['nome'].lower() or busca.lower() in str(r['usuario']).lower():
                status_icon = "🔴" if r['dias_res'] < 0 else "🟢"
                with st.expander(f"{status_icon} {r['nome'].upper()} | {r['usuario']}"):
                    with st.form(key=f"ed_{r['id']}"):
                        col1, col2 = st.columns(2)
                        en = col1.text_input("CLIENTE", value=r['nome'])
                        eu = col2.text_input("USUÁRIO", value=r['usuario'])
                        es = col1.text_input("SENHA", value=r['senha'])
                        srvs = get_servidores()
                        esrv = col2.selectbox("SERVIDOR", srvs, index=srvs.index(r['servidor']) if r['servidor'] in srvs else 0)
                        esis = col1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if r['sistema']=="P2P" else 1)
                        ev = col2.date_input("VENCIMENTO", value=pd.to_datetime(r['vencimento']).date())
                        ec = col1.number_input("CUSTO", value=float(r['custo'] or 0.0))
                        em = col2.number_input("VALOR COBRADO", value=float(r['mensalidade'] or 0.0))
                        ei = col1.date_input("INICIOU DIA", value=pd.to_datetime(r['inicio']).date() if r['inicio'] else hoje)
                        ew = col2.text_input("WHATSAPP", value=r['whatsapp'])
                        eobs = st.text_area("OBSERVAÇÃO", value=r['observacao'] or "")
                        if st.form_submit_button("💾 SALVAR"):
                            c = sqlite3.connect('supertv_gestao.db')
                            c.execute("UPDATE clientes SET nome=?, usuario=?, senha=?, servidor=?, sistema=?, vencimento=?, custo=?, mensalidade=?, inicio=?, whatsapp=?, observacao=? WHERE id=?", 
                                     (en, eu, es, esrv, esis, str(ev), ec, em, str(ei), ew, eobs, r['id']))
                            c.commit(); st.rerun()

with tab2:
    st.subheader("🚀 Cadastro de Novo Assinante")
    with st.form("form_novo", clear_on_submit=True):
        # AQUI ESTÁ A SEQUÊNCIA EXATA QUE VOCÊ PEDIU:
        c1, c2 = st.columns(2)
        n_cliente = c1.text_input("CLIENTE")
        n_usuario = c2.text_input("USUÁRIO")
        
        n_senha = c1.text_input("SENHA")
        n_servidor = c2.selectbox("SERVIDOR", get_servidores())
        
        n_sistema = c1.selectbox("SISTEMA", ["P2P", "IPTV"])
        n_vencimento = c2.date_input("VENCIMENTO", value=datetime.now() + timedelta(days=30))
        
        n_custo = c1.number_input("CUSTO", value=10.0)
        n_valor = c2.number_input("VALOR COBRADO", value=35.0)
        
        n_inicio = c1.date_input("INÍCIOU DIA", value=datetime.now().date())
        n_whatsapp = c2.text_input("WHATSAPP")
        
        n_obs = st.text_area("OBSERVAÇÃO")
        
        if st.form_submit_button("🚀 CADASTRAR AGORA", type="primary"):
            if n_cliente and n_usuario:
                conn = sqlite3.connect('supertv_gestao.db')
                conn.execute("""INSERT INTO clientes 
                    (nome, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, inicio, whatsapp, observacao) 
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""", 
                    (n_cliente, n_usuario, n_senha, n_servidor, n_sistema, str(n_vencimento), n_custo, n_valor, str(n_inicio), n_whatsapp, n_obs))
                conn.commit(); conn.close(); st.success("Cadastrado!"); st.rerun()

with tab3:
    st.subheader("🚨 COBRANÇA")
    pix_chave = "62.326.879/0001-13"
    if not df.empty:
        df_aviso = df[df['dias_res'] <= 3].copy()
        for _, cl in df_aviso.iterrows():
            if st.checkbox(f"🔔 {cl['nome']} | Vence: {cl['vencimento']}", key=f"cob_{cl['id']}"):
                msg = f"Olá {cl['nome']}! Sua assinatura vence em {cl['vencimento']}. Renove via Pix: {pix_chave}"
                st.link_button(f"Enviar para {cl['nome']}", f"https://wa.me/55{cl['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ AJUSTES")
    ns = st.text_input("NOVO SERVIDOR")
    if st.button("ADICIONAR SERVIDOR"):
        if ns:
            c = sqlite3.connect('supertv_gestao.db')
            c.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (ns.upper(),))
            c.commit(); st.rerun()
    st.divider()
    if st.button("📥 DOWNLOAD BACKUP EXCEL"):
        tow = io.BytesIO(); df.to_excel(tow, index=False)
        st.download_button("Clique aqui para baixar", data=tow.getvalue(), file_name="backup_supertv.xlsx")
