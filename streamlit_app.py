import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="SUPERTV4K PRO", layout="wide")

# =========================
# DB INIT
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
# SERVIDORES
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
# DATA
# =========================
def load_data():
    conn = sqlite3.connect("supertv_gestao.db")
    df = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    return df

# =========================
# SESSION CONTROL
# =========================
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

def editar(id_):
    st.session_state.edit_id = id_

def voltar():
    st.session_state.edit_id = None
    st.rerun()

# =========================
# UI
# =========================
st.title("📊 SUPERTV4K DASHBOARD PRO")

df = load_data()

# =========================
# LISTA OU EDITOR
# =========================
if st.session_state.edit_id is None:

    st.subheader("👤 CLIENTES")

    if df.empty:
        st.warning("Nenhum cliente cadastrado.")
    else:

        for _, r in df.iterrows():

            col1, col2, col3 = st.columns([4,3,2])

            col1.write(f"👤 **{r['nome']}** | {r['usuario']}")
            col2.write(f"📡 {r['servidor']} | 📅 {r['vencimento']}")

            if col3.button("✏️ EDITAR", key=f"e_{r['id']}"):
                editar(r["id"])

# =========================
# EDITAR CLIENTE (FLUXO CORRETO)
# =========================
else:

    cliente = df[df["id"] == st.session_state.edit_id].iloc[0]

    st.subheader("✏️ EDITAR CLIENTE")

    with st.form("form_edit"):

        # ORDEM EXATA
        nome = st.text_input("CLIENTE", cliente["nome"])
        usuario = st.text_input("USUÁRIO", cliente["usuario"])
        senha = st.text_input("SENHA", cliente["senha"])

        servidor = st.selectbox(
            "SERVIDOR",
            get_servidores(),
            index=get_servidores().index(cliente["servidor"]) if cliente["servidor"] in get_servidores() else 0
        )

        sistema = st.selectbox("SISTEMA", ["IPTV", "P2P"])

        vencimento = st.date_input("VENCIMENTO", datetime.strptime(cliente["vencimento"], "%Y-%m-%d"))

        custo = st.number_input("CUSTO", value=float(cliente["custo"]))
        valor = st.number_input("VALOR COBRADO", value=float(cliente["mensalidade"]))

        inicio = st.date_input("INÍCIOU DIA", datetime.strptime(cliente["inicio"], "%Y-%m-%d"))

        whatsapp = st.text_input("WHATSAPP", cliente["whatsapp"])
        obs = st.text_area("OBSERVAÇÃO", cliente["observacao"])

        salvar = st.form_submit_button("💾 SALVAR ALTERAÇÕES")

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

            st.success("✔ Cliente atualizado com sucesso")

            voltar()

    if st.button("⬅️ VOLTAR"):
        voltar()

# =========================
# CADASTRO NOVO
# =========================
st.divider()
st.subheader("➕ NOVO CLIENTE")

with st.form("cad"):

    nome = st.text_input("CLIENTE")
    usuario = st.text_input("USUÁRIO")
    senha = st.text_input("SENHA")

    servidor = st.selectbox("SERVIDOR", get_servidores())
    sistema = st.selectbox("SISTEMA", ["IPTV", "P2P"])

    vencimento = st.date_input("VENCIMENTO")
    custo = st.number_input("CUSTO", value=10.0)
    valor = st.number_input("VALOR COBRADO", value=35.0)

    inicio = st.date_input("INÍCIOU DIA")

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

        st.success("✔ Cliente salvo")
        st.rerun()
