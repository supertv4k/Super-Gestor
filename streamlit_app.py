import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="SUPERTV4K GESTÃO PRO", layout="wide")

# =========================
# 🎨 ESTILO + LOGOS
# =========================
st.markdown("""
<style>
.main {background-color: #0e1117; color: white;}
.card {
    background: #161b22;
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #30363d;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;">
<img src="https://i.imgur.com/CKq9BVx.png" width="350">
<br>
<img src="https://i.imgur.com/OkUAPQa.png" width="300">
</div>
""", unsafe_allow_html=True)

# =========================
# 🗄️ BANCO
# =========================
@st.cache_resource
def get_conn():
    return sqlite3.connect("clientes.db", check_same_thread=False)

def init_db():
    conn = get_conn()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        usuario TEXT,
        servidor TEXT,
        vencimento TEXT,
        valor REAL,
        whatsapp TEXT
    )
    """)
    conn.commit()

init_db()

# =========================
# 🔄 CARREGAR DADOS
# =========================
@st.cache_data(ttl=5)
def load_data():
    return pd.read_sql_query("SELECT * FROM clientes", get_conn())

df = load_data()

# =========================
# 📊 DASHBOARD
# =========================
st.title("📊 Painel de Clientes")

if not df.empty:
    hoje = datetime.now().date()
    df["dt"] = pd.to_datetime(df["vencimento"]).dt.date
    df["dias"] = df["dt"].apply(lambda x: (x - hoje).days)

    total = len(df)
    vencidos = len(df[df["dias"] < 0])
    ativos = total - vencidos

    c1, c2, c3 = st.columns(3)
    c1.metric("Clientes", total)
    c2.metric("Ativos", ativos)
    c3.metric("Vencidos", vencidos)

# =========================
# 🔍 BUSCA
# =========================
busca = st.text_input("🔎 Buscar cliente")

if busca:
    df = df[df["nome"].str.contains(busca, case=False, na=False)]

# =========================
# 📋 LISTA (OTIMIZADA)
# =========================
st.subheader("👥 Clientes")

for _, r in df.head(100).iterrows():
    if st.button(f"{r['nome']} | {r['usuario']} | {r['servidor']} | {r['vencimento']}", key=r['id']):
        st.session_state["edit"] = r["id"]

# =========================
# ✏️ EDIÇÃO
# =========================
if "edit" in st.session_state:
    cli = df[df["id"] == st.session_state["edit"]].iloc[0]

    st.subheader(f"✏️ Editar: {cli['nome']}")

    with st.form("edit_form"):
        nome = st.text_input("Nome", cli["nome"])
        usuario = st.text_input("Usuário", cli["usuario"])
        servidor = st.text_input("Servidor", cli["servidor"])
        venc = st.date_input("Vencimento", datetime.strptime(cli["vencimento"], "%Y-%m-%d"))
        valor = st.number_input("Valor", value=float(cli["valor"]))
        whats = st.text_input("WhatsApp", cli["whatsapp"])

        if st.form_submit_button("💾 Salvar"):
            conn = get_conn()
            conn.execute("""
            UPDATE clientes SET
            nome=?, usuario=?, servidor=?, vencimento=?, valor=?, whatsapp=?
            WHERE id=?
            """, (
                nome, usuario, servidor,
                venc.strftime("%Y-%m-%d"),
                valor, whats, cli["id"]
            ))
            conn.commit()

            st.success("Salvo com sucesso!")
            st.cache_data.clear()
            st.rerun()

# =========================
# ➕ NOVO CLIENTE
# =========================
st.subheader("➕ Novo Cliente")

with st.form("novo"):
    nome = st.text_input("Nome")
    usuario = st.text_input("Usuário")
    servidor = st.text_input("Servidor")
    venc = st.date_input("Vencimento", datetime.now()+timedelta(days=30))
    valor = st.number_input("Valor", value=35.0)
    whats = st.text_input("WhatsApp")

    if st.form_submit_button("Cadastrar"):
        conn = get_conn()
        conn.execute("""
        INSERT INTO clientes (nome, usuario, servidor, vencimento, valor, whatsapp)
        VALUES (?,?,?,?,?,?)
        """, (
            nome, usuario, servidor,
            venc.strftime("%Y-%m-%d"),
            valor, whats
        ))
        conn.commit()

        st.success("Cliente cadastrado!")
        st.cache_data.clear()
        st.rerun()

# =========================
# 📦 BACKUP SIMPLES
# =========================
st.subheader("📦 Backup")

if not df.empty:
    output = io.BytesIO()
    df.to_excel(output, index=False)

    st.download_button(
        "⬇️ Baixar Backup",
        data=output.getvalue(),
        file_name=f"backup_clientes_{datetime.now().strftime('%d-%m-%Y')}.xlsx"
    )
