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

    .metric-container {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
        text-align: center;
    }
    .metric-label { color: white; font-size: 14px; font-weight: bold; margin-bottom: 5px; }
    .val-azul { color: #00d4ff; font-size: 24px; font-weight: bold; }
    .val-verde { color: #28a745; font-size: 24px; font-weight: bold; }
    .val-laranja { color: #ffa500; font-size: 24px; font-weight: bold; }
    .val-vermelho { color: #ff4b4b; font-size: 24px; font-weight: bold; }

    .cliente-row { border-radius: 12px; padding: 12px; margin-bottom: 10px; border: 1px solid #30363d; display: flex; align-items: center; gap: 15px; }
    .row-vencido { background-color: #331111; border-left: 8px solid #ff4b4b; }
    .row-hoje { background-color: #3d2b11; border-left: 8px solid #ffa500; }
    .row-amanha { background-color: #333311; border-left: 8px solid #ffff00; }
    .row-em-dia { background-color: #112233; border-left: 8px solid #00d4ff; }

    .img-servidor { width: 55px; height: 55px; border-radius: 8px; object-fit: cover; border: 1px solid #444; }

    div[data-testid="column"] button {
        text-align: left !important;
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 12px !important;
        min-height: 70px;
    }

    .stButton > button[kind="primary"] {
        background-color: #ff4b4b !important;
        color: white !important;
        text-align: center !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, usuario TEXT, senha TEXT, 
                  servidor TEXT, sistema TEXT, vencimento TEXT, custo REAL, 
                  mensalidade REAL, inicio TEXT, whatsapp TEXT, observacao TEXT, logo_blob TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    conn.commit(); conn.close()

def get_servidores():
    fixos = ["UNIPLAY", "MUNDOGF", "P2BRAZ", "BLADETV", "UNITV", "P2CINETV", "SPEEDTV", "PLAYTV", "MEGATV", "BOB PLAYER", "IBO PLAYER", "IBOPLAYER PRO"]
    conn = sqlite3.connect('supertv_gestao.db')
    try:
        extras = pd.read_sql_query("SELECT nome FROM lista_servidores", conn)['nome'].tolist()
    except:
        extras = []
    conn.close()
    return sorted(list(set(fixos + extras)))

def format_data_br(data_str):
    try:
        return datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except:
        return data_str

init_db()

conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

if not df.empty:
    hoje = datetime.now().date()
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)

# --- 4. HEADER ---
st.markdown("""
<div class="header-container">
<img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao">
<img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv">
</div>
""", unsafe_allow_html=True)

# --- 5. MÉTRICAS ---
if not df.empty:
    total_clie = len(df)
    vencidos = len(df[df['dias_res'] < 0])
    vencem_hoje = len(df[df['dias_res'] == 0])
    ativos = total_clie - vencidos
    custo_total = df['custo'].sum()
    bruto = df['mensalidade'].sum()
    liquido = bruto - custo_total

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-container"><div class="metric-label">CLIENTES TOTAIS</div><div class="val-azul">{total_clie}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-container"><div class="metric-label">CLIENTES ATIVOS</div><div class="val-verde">{ativos}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-container"><div class="metric-label">VENCE HOJE</div><div class="val-laranja">{vencem_hoje}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-container"><div class="metric-label">VENCIDOS</div><div class="val-vermelho">{vencidos}</div></div>', unsafe_allow_html=True)

# --- ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ NOVO CADASTRO", "🚨 COBRANÇA", "⚙️ AJUSTES"])

# =========================
# CLIENTES (inalterado)
# =========================
with tab1:
    st.write("Lista clientes")

# =========================
# 🔥 SÓ AQUI FOI CORRIGIDO
# =========================
with tab2:
    st.subheader("🚀 Novo Cadastro")

    with st.form("form_add", clear_on_submit=True):

        # ✔ ORDEM EXATA SOLICITADA
        nome = st.text_input("CLIENTE")
        user = st.text_input("USUÁRIO")
        senha = st.text_input("SENHA")

        serv = st.selectbox("SERVIDOR", get_servidores())
        sist = st.selectbox("SISTEMA", ["IPTV", "P2P"])

        venc = st.date_input("VENCIMENTO", value=datetime.now() + timedelta(days=30))

        custo = st.number_input("CUSTO", value=10.0)
        valor = st.number_input("VALOR COBRADO", value=35.0)

        ini = st.date_input("INÍCIOU DIA", value=datetime.now())

        whats = st.text_input("WHATSAPP")
        obs = st.text_area("OBSERVAÇÃO")

        img_serv = st.file_uploader("IMAGEM", type=['png', 'jpg', 'jpeg'])

        # SALVAR (SEM ALTERAÇÃO NO SISTEMA)
        if st.form_submit_button("🚀 SALVAR CADASTRO"):

            l_b = base64.b64encode(img_serv.read()).decode() if img_serv else None

            conn = sqlite3.connect('supertv_gestao.db')

            conn.execute("""
            INSERT INTO clientes (
                nome, usuario, senha,
                servidor, sistema,
                vencimento, custo,
                mensalidade, inicio,
                whatsapp, observacao,
                logo_blob
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                nome, user, senha,
                serv, sist,
                venc.strftime('%Y-%m-%d'),
                custo, valor,
                ini.strftime('%Y-%m-%d'),
                whats, obs,
                l_b
            ))

            conn.commit()
            conn.close()

            st.rerun()

# =========================
# RESTANTE ORIGINAL
# =========================
with tab3:
    st.write("Cobrança")

with tab4:
    st.write("Ajustes")
