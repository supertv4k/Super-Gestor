import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="SUPERTV4K DASHBOARD PRO", layout="wide")

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
# LOAD DATA
# =========================
def load_data():
    conn = sqlite3.connect("supertv_gestao.db")
    df = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    return df

df = load_data()

# =========================
# STATUS CALC
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
# SERVIDORES ADD
# =========================
with st.expander("⚙️ GERENCIAR SERVIDORES"):

    novo = st.text_input("Novo servidor")

    if st.button("➕ ADICIONAR"):
        if novo.strip():
            conn = sqlite3.connect("supertv_gestao.db")
            try:
                conn.execute("INSERT INTO servidores_extra (nome) VALUES (?)", (novo.upper(),))
                conn.commit()
                st.success("Adicionado!")
            except:
                st.warning("Já existe.")
            conn.close()
            st.rerun()

# =========================
# DASHBOARD
# =========================
if df.empty:
    st.warning("Sem clientes ainda.")
    st.stop()

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

# =========================
# FILTRO
# =========================
filtro = st.selectbox("FILTRAR", ["TODOS", "ATIVOS", "VENCIDOS", "HOJE"])

if filtro == "VENCIDOS":
    view = df[df["dias"] < 0]
elif filtro == "ATIVOS":
    view = df[df["dias"] >= 0]
elif filtro == "HOJE":
    view = df[df["dias"] == 0]
else:
    view = df

# =========================
# LISTA EDITÁVEL (CORRIGIDO)
# =========================
st.subheader("👤 CLIENTES")

for _, r in view.iterrows():

    with st.expander(f"👤 {r['nome']} | {r['usuario']} | {r['servidor']}"):

        with st.form(f"edit_{r['id']}"):

            col1, col2, col3 = st.columns(3)

            nome = col1.text_input("CLIENTE", r["nome"])
            usuario = col2.text_input("USUÁRIO", r["usuario"])
            senha = col3.text_input("SENHA", r["senha"])

            servidor = col1.selectbox(
                "SERVIDOR",
                get_servidores(),
                index=get_servidores().index(r["servidor"]) if r["servidor"] in get_servidores() else 0
            )

            sistema = col2.selectbox("SISTEMA", ["IPTV", "P2P"], index=0)

            venc = col3.date_input("VENCIMENTO", datetime.strptime(r["vencimento"], "%Y-%m-%d"))

            custo = col1.number_input("CUSTO", value=float(r["custo"]))
            valor = col2.number_input("VALOR COBRADO", value=float(r["mensalidade"]))
            inicio = col3.date_input("INÍCIOU DIA", datetime.strptime(r["inicio"], "%Y-%m-%d"))

            whatsapp = col1.text_input("WHATSAPP", r["whatsapp"])
            obs = st.text_area("OBSERVAÇÃO", r["observacao"])

            if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):

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
                    venc.strftime("%Y-%m-%d"),
                    custo, valor,
                    inicio.strftime("%Y-%m-%d"),
                    whatsapp, obs,
                    r["id"]
                ))

                conn.commit()
                conn.close()

                st.success("Atualizado!")
                st.rerun()
