import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 380px; margin-bottom: -20px !important; }
    .logo-supertv { width: 160px; }
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 12px; text-align: center; border: 1px solid #30363d; margin-bottom: 10px; }
    .metric-label { font-size: 11px; font-weight: bold; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 22px; font-weight: bold; color: #ff0000; margin-top: 5px; }
    
    div.stButton > button, div.stDownloadButton > button, div.stFormSubmitButton > button, [data-testid="stLinkButton"] > a {
        background: linear-gradient(135deg, #ff0000 0%, #c0c0c0 100%) !important;
        color: #ffffff !important; font-weight: 900 !important; font-size: 16px !important;
        border-radius: 10px !important; border: 2px solid #ffffff44 !important;
        height: 50px !important; width: 100% !important; text-transform: uppercase !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.7) !important;
    }
    .stExpander > details > summary { background: linear-gradient(135deg, #ff0000 0%, #c0c0c0 100%) !important; color: #ffffff !important; padding: 15px !important; border-radius: 10px !important; font-weight: 800 !important; font-size: 20px !important; }
    .client-detail-card { background: #1c2128; padding: 20px; border-radius: 10px; border-left: 8px solid #ff0000; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, vencimento DATE, custo REAL, mensalidade REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    conn.commit(); conn.close()

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    conn.close()
    return lista if lista else ["UNIPlAY", "MUNDOGF", "P2BRAZ"]

init_db()

# --- 4. CONTROLE DE NAVEGAÇÃO ---
if 'aba_atual' not in st.session_state:
    st.session_state.aba_atual = 0  # Inicia na aba Gestão

# --- 5. CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

if 'selecionados' not in st.session_state:
    st.session_state.selecionados = []

# --- 6. HEADER ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

# --- MÉTRICAS ---
if not df.empty:
    hoje = datetime.now().date()
    df['venc_dt'] = pd.to_datetime(df['vencimento']).dt.date
    df['dias_res'] = (df['venc_dt'] - hoje).apply(lambda x: x.days)
    m1, m2, m3 = st.columns(3)
    m1.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL CLIENTES</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value">{len(df[df["dias_res"] < 0])}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-label">VENCEM EM 3 DIAS</div><div class="metric-value">{len(df[(df["dias_res"] >= 0) & (df["dias_res"] <= 3)])}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 7. SISTEMA DE ABAS ---
# Usamos o index do session_state para controlar para onde o sistema vai
titulos_abas = ["👤 GESTÃO", "➕ NOVO", "📢 COBRANÇA", "⚙️ AJUSTES"]
aba_ativa = st.tabs(titulos_abas)

# ABA GESTÃO
with aba_ativa[0]:
    busca = st.text_input("🔍 PESQUISAR")
    if not df.empty:
        for _, r in df.iterrows():
            if busca.lower() in r['nome'].lower() or busca.lower() in str(r['usuario']).lower():
                with st.expander(f"👤 {r['nome'].upper()} / {r['usuario']}"):
                    with st.form(key=f"ed_{r['id']}"):
                        c1, c2 = st.columns(2)
                        en, ew = c1.text_input("Nome", value=r['nome']), c2.text_input("WhatsApp", value=r['whatsapp'])
                        c3, c4 = st.columns(2)
                        eu, es = c3.text_input("Usuário", value=r['usuario']), c4.text_input("Senha", value=r['senha'])
                        srvs = get_servidores()
                        esrv = st.selectbox("Servidor", srvs, index=srvs.index(r['servidor']) if r['servidor'] in srvs else 0)
                        c5, c6 = st.columns(2)
                        ev = c5.date_input("Vencimento", value=pd.to_datetime(r['vencimento']).date())
                        em = c6.number_input("Valor", value=float(r['mensalidade']))
                        if st.form_submit_button("💾 SALVAR"):
                            c = sqlite3.connect('supertv_gestao.db'); c.execute("UPDATE clientes SET nome=?, whatsapp=?, usuario=?, senha=?, servidor=?, vencimento=?, mensalidade=? WHERE id=?", (en, ew, eu, es, esrv, str(ev), em, r['id'])); c.commit(); st.rerun()

# ABA NOVO (CADASTRO COM REDIRECIONAMENTO)
with aba_ativa[1]:
    st.subheader("🚀 Cadastro de Novo Cliente")
    with st.form("form_cadastro", clear_on_submit=True):
        f1, f2 = st.columns(2)
        n_n, w_n = f1.text_input("NOME COMPLETO"), f2.text_input("WHATSAPP")
        f3, f4 = st.columns(2)
        u_n, s_n = f3.text_input("USUÁRIO"), f4.text_input("SENHA")
        srv_n = st.selectbox("SERVIDOR", get_servidores())
        v_n = st.date_input("VENCIMENTO", value=datetime.now() + timedelta(days=30))
        f5, f6 = st.columns(2)
        c_n, m_n = f5.number_input("CUSTO", value=0.0), f6.number_input("VALOR", value=35.0)
        
        if st.form_submit_button("🚀 CADASTRAR CLIENTE"):
            if n_n and u_n:
                conn = sqlite3.connect('supertv_gestao.db')
                conn.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, vencimento, custo, mensalidade) VALUES (?,?,?,?,?,?,?,?)", (n_n, w_n, u_n, s_n, srv_n, str(v_n), c_n, m_n))
                conn.commit(); conn.close()
                st.success("Cadastrado com sucesso! Redirecionando...")
                # O Truque: st.rerun() limpa o estado e volta para a aba inicial (0)
                st.rerun()
            else:
                st.error("Preencha os campos obrigatórios!")

# ABA COBRANÇA
with aba_ativa[2]:
    st.subheader("📢 Cobrança")
    pix_chave = "62.326.879/0001-13"
    if not df.empty:
        df_aviso = df[df['dias_res'] <= 3].copy()
        c1, c2 = st.columns(2)
        if c1.button("✅ SELECIONAR TODOS"): st.session_state.selecionados = df_aviso['id'].tolist(); st.rerun()
        if c2.button("❌ LIMPAR"): st.session_state.selecionados = []; st.rerun()
        for _, cl in df_aviso.iterrows():
            check = st.checkbox(f"Aviso: {cl['nome']}", value=(cl['id'] in st.session_state.selecionados), key=f"p_{cl['id']}")
            if check and cl['id'] not in st.session_state.selecionados: st.session_state.selecionados.append(cl['id'])
            elif not check and cl['id'] in st.session_state.selecionados: st.session_state.selecionados.remove(cl['id'])
        if st.session_state.selecionados:
            for sid in st.session_state.selecionados:
                cli = df[df['id'] == sid].iloc[0]
                msg = f"Olá {cli['nome']}! Sua renovação Supertv4k está próxima. Pix: {pix_chave}"
                st.link_button(f"ENVIAR: {cli['nome']}", f"https://wa.me/{cli['whatsapp']}?text={urllib.parse.quote(msg)}")

# ABA AJUSTES
with aba_ativa[3]:
    st.subheader("⚙️ Configurações")
    ns = st.text_input("Novo Servidor")
    if st.button("ADD SERVIDOR"):
        if ns:
            c = sqlite3.connect('supertv_gestao.db'); c.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (ns,)); c.commit(); st.rerun()
    st.divider()
    f_up = st.file_uploader("📥 Importar Excel", type=["xlsx"])
    if f_up and st.button("PROCESSAR"):
        pd.read_excel(f_up).to_sql('clientes', sqlite3.connect('supertv_gestao.db'), if_exists='append', index=False); st.rerun()
    if not df.empty:
        tow = io.BytesIO(); df.to_excel(tow, index=False)
        st.download_button("📤 BAIXAR BACKUP", data=tow.getvalue(), file_name="backup_supertv4k.xlsx")
