import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime, date

# =====================
# CONFIG
# =====================
st.set_page_config(page_title="SUPERTV4K PRO", layout="wide")

# =====================
# CONEXÃO POSTGRES
# =====================
DB_URL = "postgresql://USER:PASSWORD@HOST:5432/DB"

def conn_db():
    return psycopg2.connect(DB_URL)

# =====================
# INIT DB
# =====================
def init_db():
    conn = conn_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id SERIAL PRIMARY KEY,
        cliente TEXT,
        usuario TEXT,
        senha TEXT,
        servidor TEXT,
        sistema TEXT,
        vencimento DATE,
        custo FLOAT,
        valor FLOAT,
        inicio DATE,
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
    conn = conn_db()
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
df = load_data()

st.title("📊 SUPERTV4K DASHBOARD PRO")

if not df.empty:

    total = len(df)
    vencidos = len(df[df["vencimento"] < date.today()])
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

        vencimento = st.date_input("VENCIMENTO", cli["vencimento"])
        custo = st.number_input("CUSTO", value=float(cli["custo"]))
        valor = st.number_input("VALOR COBRADO", value=float(cli["valor"]))

        inicio = st.date_input("INÍCIOU DIA", cli["inicio"])

        whatsapp = st.text_input("WHATSAPP", cli["whatsapp"])
        obs = st.text_area("OBSERVAÇÃO", cli["observacao"])

        if st.form_submit_button("SALVAR"):

            conn = conn_db()
            cur = conn.cursor()

            cur.execute("""
                UPDATE clientes SET
                    cliente=%s,
                    usuario=%s,
                    senha=%s,
                    servidor=%s,
                    sistema=%s,
                    vencimento=%s,
                    custo=%s,
                    valor=%s,
                    inicio=%s,
                    whatsapp=%s,
                    observacao=%s
                WHERE id=%s
            """, (
                cliente, usuario, senha,
                servidor, sistema,
                vencimento, custo, valor,
                inicio, whatsapp, obs,
                cli["id"]
            ))

            conn.commit()
            conn.close()

            st.success("✔ Atualizado com sucesso")

            del st.session_state["edit"]
            st.rerun()

    if st.button("⬅️ Voltar"):
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

    if st.form_submit_button("SALVAR CLIENTE"):

        conn = conn_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO clientes (
                cliente, usuario, senha,
                servidor, sistema,
                vencimento, custo, valor,
                inicio, whatsapp, observacao
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            cliente, usuario, senha,
            servidor, sistema,
            vencimento, custo, valor,
            inicio, whatsapp, obs
        ))

        conn.commit()
        conn.close()

        st.success("✔ Cliente cadastrado")
        st.rerun()
