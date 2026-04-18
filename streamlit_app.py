import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

# =====================
# CONFIG
# =====================
st.set_page_config(page_title="SUPERTV4K PRO", layout="wide")

# =====================
# DB LOCAL (ESTÁVEL)
# =====================
def init_db():
    conn = sqlite3.connect("supertv.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT,
        usuario TEXT,
        senha TEXT,
        servidor TEXT,
        sistema TEXT,
        vencimento TEXT,
        custo REAL,
        valor REAL,
        inicio TEXT,
        whatsapp TEXT,
        observacao TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =====================
# LOAD DATA
# =====================
def load_data():
    conn = sqlite3.connect("supertv.db")
    df = pd.read_sql("SELECT * FROM clientes ORDER BY id DESC", conn)
    conn.close()
    return df

# =====================
# SERVIDORES
# =====================
SERVIDORES = [
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

# =====================
# DASHBOARD
# =====================
st.title("📊 SUPERTV4K DASHBOARD PRO")

df = load_data()

if not df.empty:
    total = len(df)

    vencidos = len(df[pd.to_datetime(df["vencimento"]) < pd.to_datetime(date.today())])
    ativos = total - vencidos

    c1, c2, c3 = st.columns(3)
    c1.metric("Clientes", total)
    c2.metric("Ativos", ativos)
    c3.metric("Vencidos", vencidos)

# =====================
# LISTA
# =====================
st.subheader("👤 CLIENTES")

for _, r in df.iterrows():

    col1, col2, col3 = st.columns([4,4,2])

    col1.write(f"**{r['cliente']}** | {r['usuario']} | {r['servidor']}")
    col2.write(f"📅 {r['vencimento']}")

    if col3.button("Editar", key=r["id"]):
        st.session_state.edit = r["id"]

# =====================
# EDITAR
# =====================
if "edit" in st.session_state:

    cli = df[df["id"] == st.session_state.edit].iloc[0]

    st.divider()
    st.subheader("✏️ EDITAR CLIENTE")

    with st.form("edit_form"):

        cliente = st.text_input("CLIENTE", cli["cliente"])
        usuario = st.text_input("USUÁRIO", cli["usuario"])
        senha = st.text_input("SENHA", cli["senha"])

        servidor = st.selectbox("SERVIDOR", SERVIDORES)
        sistema = st.selectbox("SISTEMA", ["IPTV", "P2P"])

        vencimento = st.date_input("VENCIMENTO")
        custo = st.number_input("CUSTO", value=float(cli["custo"]))
        valor = st.number_input("VALOR COBRADO", value=float(cli["valor"]))

        inicio = st.date_input("INÍCIOU DIA")

        whatsapp = st.text_input("WHATSAPP", cli["whatsapp"])
        obs = st.text_area("OBSERVAÇÃO", cli["observacao"])

        if st.form_submit_button("SALVAR"):

            conn = sqlite3.connect("supertv.db")
            c = conn.cursor()

            c.execute("""
                UPDATE clientes SET
                    cliente=?, usuario=?, senha=?,
                    servidor=?, sistema=?,
                    vencimento=?, custo=?, valor=?,
                    inicio=?, whatsapp=?, observacao=?
                WHERE id=?
            """, (
                cliente, usuario, senha,
                servidor, sistema,
                vencimento.strftime("%Y-%m-%d"),
                custo, valor,
                inicio.strftime("%Y-%m-%d"),
                whatsapp, obs,
                cli["id"]
            ))

            conn.commit()
            conn.close()

            st.success("✔ Salvo com sucesso")

            del st.session_state["edit"]
            st.rerun()

# =====================
# NOVO CLIENTE
# =====================
st.divider()
st.subheader("➕ NOVO CLIENTE")

with st.form("novo"):

    cliente = st.text_input("CLIENTE")
    usuario = st.text_input("USUÁRIO")
    senha = st.text_input("SENHA")

    servidor = st.selectbox("SERVIDOR", SERVIDORES)
    sistema = st.selectbox("SISTEMA", ["IPTV", "P2P"])

    vencimento = st.date_input("VENCIMENTO")
    custo = st.number_input("CUSTO", value=0.0)
    valor = st.number_input("VALOR COBRADO", value=0.0)

    inicio = st.date_input("INÍCIOU DIA")

    whatsapp = st.text_input("WHATSAPP")
    obs = st.text_area("OBSERVAÇÃO")

    if st.form_submit_button("SALVAR"):

        conn = sqlite3.connect("supertv.db")
        c = conn.cursor()

        c.execute("""
            INSERT INTO clientes (
                cliente, usuario, senha,
                servidor, sistema,
                vencimento, custo, valor,
                inicio, whatsapp, observacao
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            cliente, usuario, senha,
            servidor, sistema,
            vencimento.strftime("%Y-%m-%d"),
            custo, valor,
            inicio.strftime("%Y-%m-%d"),
            whatsapp, obs
        ))

        conn.commit()
        conn.close()

        st.success("✔ Cliente adicionado")
        st.rerun()
