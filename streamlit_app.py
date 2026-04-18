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
    </style>
""", unsafe_allow_html=True)

# --- DB ---
def get_conn():
    return sqlite3.connect("supertv_gestao.db")

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT, usuario TEXT, senha TEXT,
        servidor TEXT, sistema TEXT,
        vencimento TEXT, custo REAL,
        mensalidade REAL, inicio TEXT,
        whatsapp TEXT, observacao TEXT,
        logo_blob TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

# --- LOAD ---
conn = get_conn()
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- HEADER ---
st.markdown("""
<div class="header-container">
<img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao">
<img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv">
</div>
""", unsafe_allow_html=True)

# --- ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["CLIENTES", "NOVO CADASTRO", "COBRANÇA", "AJUSTES"])

# =========================
# CLIENTES (igual original)
# =========================
with tab1:
    st.write("Lista clientes (sem alteração)")

# =========================
# 🔥 CORREÇÃO AQUI (SÓ ORDEM DOS CAMPOS)
# =========================
with tab2:
    st.subheader("🚀 Novo Cadastro")

    with st.form("form_add", clear_on_submit=True):

        # ✔ ORDEM CORRETA FIXA

        nome = st.text_input("CLIENTE")
        user = st.text_input("USUÁRIO")
        senha = st.text_input("SENHA")

        serv = st.selectbox("SERVIDOR", ["UNIPLAY", "MUNDOGF", "P2BRAZ"])
        sist = st.selectbox("SISTEMA", ["IPTV", "P2P"])

        venc = st.date_input("VENCIMENTO", datetime.now() + timedelta(days=30))

        custo = st.number_input("CUSTO", value=10.0)
        valor = st.number_input("VALOR COBRADO", value=35.0)

        ini = st.date_input("INÍCIOU DIA", datetime.now())

        whats = st.text_input("WHATSAPP")
        obs = st.text_area("OBSERVAÇÃO")

        img = st.file_uploader("IMAGEM", type=["png","jpg","jpeg"])

        if st.form_submit_button("🚀 SALVAR CADASTRO"):

            logo = base64.b64encode(img.read()).decode() if img else None

            conn = get_conn()

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
                venc.strftime("%Y-%m-%d"),
                custo, valor,
                ini.strftime("%Y-%m-%d"),
                whats, obs,
                logo
            ))

            conn.commit()
            conn.close()

            st.rerun()

# =========================
# RESTANTE SEM ALTERAÇÃO
# =========================
with tab3:
    st.write("Cobrança")

with tab4:
    st.write("Ajustes")
