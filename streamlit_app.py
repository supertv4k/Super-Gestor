import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="SUPERTV4K DASHBOARD PRO", layout="wide")

# =========================
# DB
# =========================
def init_db():
    conn = sqlite3.connect("supertv_gestao.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        usuario TEXT,
        senha TEXT,
        servidor TEXT,
        sistema TEXT,
        vencimento TEXT,
        custo REAL,
        mensalidade REAL,
        inicio TEXT,
        whatsapp TEXT,
        observacao TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS servidores_extra (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# SERVIDORES FIXOS + EXTRAS
# =========================
SERVIDORES_FIXOS = [
    "UNIPLAY",
    "MUNDO GF",
    "UNITV",
    "P2BRAZ",
    "BLADETV",
    "P2CINETV",
    "P2SPEEDTV",
    "PLAYTV",
    "MEGATV"
]

def get_servidores():
    conn = sqlite3.connect("supertv_gestao.db")
    df = pd.read_sql_query("SELECT nome FROM servidores_extra", conn)
    conn.close()

    extras = df["nome"].tolist() if not df.empty else []

    return sorted(list(set(SERVIDORES_FIXOS + extras)))

# =========================
# LOAD CLIENTES
# =========================
def load_data():
    conn = sqlite3.connect("supertv_gestao.db")
    df = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    return df

df = load_data()

# =========================
# STATUS
# =========================
if not df.empty:
    hoje = datetime.now().date()
    df["venc"] = pd.to_datetime(df["vencimento"], errors="coerce").dt.date
    df["dias"] = df["venc"].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)

# =========================
# HEADER
# =========================
st.title("📊 SUPERTV4K DASHBOARD PRO")

# =========================
# LISTA SERVIDORES (ADMIN)
# =========================
with st.expander("⚙️ GERENCIAR SERVIDORES"):

    novo_server = st.text_input("Adicionar novo servidor")

    if st.button("➕ ADICIONAR SERVIDOR"):
        if novo_server.strip() != "":
            conn = sqlite3.connect("supertv_gestao.db")
            try:
                conn.execute("INSERT INTO servidores_extra (nome) VALUES (?)", (novo_server.upper(),))
                conn.commit()
                st.success("Servidor adicionado!")
            except:
                st.warning("Servidor já existe.")
            conn.close()
            st.rerun()

# =========================
# CADASTRO
# =========================
st.subheader("➕ NOVO CLIENTE")

with st.form("cadastro"):

    nome = st.text_input("CLIENTE")
    usuario = st.text_input("USUÁRIO")
    senha = st.text_input("SENHA")

    servidor = st.selectbox("SERVIDOR", get_servidores())
    sistema = st.selectbox("SISTEMA", ["IPTV", "P2P"])

    vencimento = st.date_input("VENCIMENTO", datetime.now() + timedelta(days=30))
    custo = st.number_input("CUSTO", value=10.0)
    valor = st.number_input("VALOR COBRADO", value=35.0)

    inicio = st.date_input("INÍCIOU DIA", datetime.now())

    whatsapp = st.text_input("WHATSAPP")
    obs = st.text_area("OBSERVAÇÃO")

    if st.form_submit_button("SALVAR CLIENTE"):

        conn = sqlite3.connect("supertv_gestao.db")
        conn.execute("""
        INSERT INTO clientes (
            nome, usuario, senha,
            servidor, sistema,
            vencimento, custo,
            mensalidade, inicio,
            whatsapp, observacao
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            nome, usuario, senha,
            servidor, sistema,
            vencimento.strftime("%Y-%m-%d"),
            custo, valor,
            inicio.strftime("%Y-%m-%d"),
            whatsapp, obs
        ))
        conn.commit()
        conn.close()

        st.success("Cliente cadastrado!")
        st.rerun()

# =========================
# DASHBOARD
# =========================
st.divider()

if df.empty:
    st.warning("Nenhum cliente cadastrado.")
else:

    total = len(df)
    vencidos = len(df[df["dias"] < 0])
    ativos = total - vencidos
    hoje_v = len(df[df["dias"] == 0])

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("CLIENTES", total)
    c2.metric("ATIVOS", ativos)
    c3.metric("VENCE HOJE", hoje_v)
    c4.metric("VENCIDOS", vencidos)

    st.divider()

    filtro = st.selectbox("FILTRAR", ["TODOS", "ATIVOS", "VENCIDOS", "HOJE"])

    if filtro == "VENCIDOS":
        view = df[df["dias"] < 0]
    elif filtro == "ATIVOS":
        view = df[df["dias"] >= 0]
    elif filtro == "HOJE":
        view = df[df["dias"] == 0]
    else:
        view = df

    st.subheader("CLIENTES")

    for _, r in view.iterrows():

        st.write(f"""
        👤 {r['nome']} | {r['usuario']}  
        📡 {r['servidor']} | 📅 {r['vencimento']}  
        ---
        """)
