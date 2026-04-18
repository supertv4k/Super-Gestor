import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="SUPERTV4K PRO", layout="wide")

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
    conn.commit()
    conn.close()

init_db()

# =========================
# LOAD DATA (SEMPRE ATUALIZADO)
# =========================
def load_data():
    conn = sqlite3.connect("supertv_gestao.db")
    df = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    return df

# =========================
# SESSION CONTROL (ESSENCIAL)
# =========================
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

def abrir_edicao(id_cliente):
    st.session_state.edit_id = id_cliente

def fechar_edicao():
    st.session_state.edit_id = None
    st.rerun()

# =========================
# DATA
# =========================
df = load_data()

st.title("📊 SUPERTV4K DASHBOARD PRO")

# =========================
# LISTA
# =========================
if st.session_state.edit_id is None:

    if df.empty:
        st.warning("Sem clientes cadastrados.")
        st.stop()

    for _, r in df.iterrows():

        col1, col2, col3 = st.columns([4, 3, 2])

        col1.write(f"👤 {r['nome']} | {r['usuario']}")
        col2.write(f"📡 {r['servidor']} | 📅 {r['vencimento']}")

        if col3.button("✏️ EDITAR", key=f"btn_{r['id']}"):
            abrir_edicao(r["id"])

# =========================
# EDITOR (TELA SEPARADA REAL)
# =========================
else:

    cliente = df[df["id"] == st.session_state.edit_id].iloc[0]

    st.subheader("✏️ EDITAR CLIENTE")

    with st.form("edit_form"):

        # ORDEM EXATA PEDIDA
        nome = st.text_input("CLIENTE", cliente["nome"])
        usuario = st.text_input("USUÁRIO", cliente["usuario"])
        senha = st.text_input("SENHA", cliente["senha"])

        servidor = st.text_input("SERVIDOR", cliente["servidor"])
        sistema = st.selectbox("SISTEMA", ["IPTV", "P2P"])

        vencimento = st.date_input(
            "VENCIMENTO",
            datetime.strptime(cliente["vencimento"], "%Y-%m-%d")
        )

        custo = st.number_input("CUSTO", value=float(cliente["custo"]))
        valor = st.number_input("VALOR COBRADO", value=float(cliente["mensalidade"]))

        inicio = st.date_input(
            "INÍCIOU DIA",
            datetime.strptime(cliente["inicio"], "%Y-%m-%d")
        )

        whatsapp = st.text_input("WHATSAPP", cliente["whatsapp"])
        obs = st.text_area("OBSERVAÇÃO", cliente["observacao"])

        salvar = st.form_submit_button("💾 SALVAR")

        if salvar:

            conn = sqlite3.connect("supertv_gestao.db")
            conn.execute("""
                UPDATE clientes SET
                    nome=?,
                    usuario=?,
                    senha=?,
                    servidor=?,
                    sistema=?,
                    vencimento=?,
                    custo=?,
                    mensalidade=?,
                    inicio=?,
                    whatsapp=?,
                    observacao=?
                WHERE id=?
            """, (
                nome, usuario, senha,
                servidor, sistema,
                vencimento.strftime("%Y-%m-%d"),
                custo, valor,
                inicio.strftime("%Y-%m-%d"),
                whatsapp, obs,
                cliente["id"]
            ))

            conn.commit()
            conn.close()

            st.success("✔ Atualizado com sucesso!")

            fechar_edicao()

    if st.button("⬅️ VOLTAR"):
        fechar_edicao()
