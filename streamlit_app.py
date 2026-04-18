import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="SUPERTV4K PRO", layout="wide")

DB = "supertv.db"

# =====================
# DB
# =====================
def init_db():
    conn = sqlite3.connect(DB)
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
# LOAD SEM CACHE BUGADO
# =====================
def load():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM clientes ORDER BY id DESC", conn)
    conn.close()
    return df

# =====================
# SERVIDORES
# =====================
SERVIDORES = [
    "UNIPLAY","MUNDO GF","UNITV","P2BRAZ","BLADETV",
    "P2CINETV","P2SPEEDTV","PLAYTV","MEGATV"
]

# =====================
# STATE
# =====================
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

def set_edit(i):
    st.session_state.edit_id = i

def close_edit():
    st.session_state.edit_id = None

# =====================
# DATA
# =====================
df = load()

st.title("📊 SUPERTV4K PRO")

# =====================
# LISTA
# =====================
st.subheader("👤 CLIENTES")

for _, r in df.iterrows():

    c1, c2, c3 = st.columns([4,4,2])

    c1.write(f"**{r['cliente']}** | {r['usuario']} | {r['servidor']}")
    c2.write(f"📅 {r['vencimento']}")

    if c3.button("Editar", key=f"e_{r['id']}"):
        set_edit(r["id"])

# =====================
# EDITAR (BLOCO CORRIGIDO)
# =====================
if st.session_state.edit_id is not None:

    cli = df[df["id"] == st.session_state.edit_id].iloc[0]

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

        salvar = st.form_submit_button("💾 SALVAR ALTERAÇÕES")

        if salvar:

            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            cur.execute("""
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

            st.success("✔ Atualizado com sucesso")

            # 🔥 ISSO AQUI É O QUE ESTAVA FALTANDO
            close_edit()
            st.rerun()

    if st.button("⬅️ VOLTAR"):
        close_edit()
        st.rerun()

# =====================
# NOVO CLIENTE (CORRIGIDO)
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

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        cur.execute("""
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

        st.success("✔ Cliente salvo")

        # 🔥 FORÇA RELOAD REAL
        st.rerun()
