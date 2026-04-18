import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="SUPERTV4K CRM PRO", layout="wide")

# =========================
# ESTADO
# =========================
if "edit_id" not in st.session_state:
    st.session_state["edit_id"] = None

# =========================
# BANCO
# =========================
def get_conn():
    return sqlite3.connect("supertv_gestao.db")

def init_db():
    conn = get_conn()
    conn.execute("""
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
            whatsapp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# =========================
# LOAD DADOS (SEMPRE ATUAL)
# =========================
@st.cache_data(ttl=0)
def load_data():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    return df

df = load_data()

# =========================
# CALCULO DIAS
# =========================
if not df.empty:
    hoje = datetime.now().date()
    df["venc"] = pd.to_datetime(df["vencimento"]).dt.date
    df["dias"] = df["venc"].apply(lambda x: (x - hoje).days)

# =========================
# HEADER
# =========================
st.title("📊 SUPERTV4K CRM PRO")

# =========================
# TABS
# =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "👤 CLIENTES",
    "➕ CADASTRO",
    "🚨 COBRANÇA",
    "⚙️ BACKUP"
])

# =========================
# CLIENTES
# =========================
with tab1:
    busca = st.text_input("🔎 Buscar cliente")

    if not df.empty:
        df_f = df.copy()

        if busca:
            df_f = df_f[df_f["nome"].str.contains(busca, case=False, na=False)]

        for _, r in df_f.iterrows():

            col1, col2 = st.columns([4, 1])

            with col1:
                cor = "🔴" if r["dias"] < 0 else "🟡" if r["dias"] <= 2 else "🟢"
                st.write(f"{cor} 👤 {r['nome']} | {r['usuario']} | vence {r['vencimento']}")

            with col2:
                if st.button("⚙️ EDITAR", key=f"e_{r['id']}"):
                    st.session_state["edit_id"] = r["id"]

# =========================
# EDITOR GLOBAL (ESTÁVEL)
# =========================
if st.session_state["edit_id"] is not None:

    cliente = df[df["id"] == st.session_state["edit_id"]].iloc[0]

    st.divider()
    st.subheader("✏️ EDITAR CLIENTE")

    with st.form("edit_form"):

        nome = st.text_input("Cliente", value=cliente["nome"])
        usuario = st.text_input("Usuário", value=cliente["usuario"])
        senha = st.text_input("Senha", value=cliente["senha"])
        servidor = st.text_input("Servidor", value=cliente["servidor"])
        sistema = st.selectbox("Sistema", ["IPTV", "P2P"], index=0 if cliente["sistema"] == "IPTV" else 1)
        venc = st.date_input("Vencimento", datetime.strptime(cliente["vencimento"], "%Y-%m-%d"))

        c1, c2, c3 = st.columns(3)

        salvar = c1.form_submit_button("💾 Salvar")
        renovar = c2.form_submit_button("🔁 +30 dias")
        fechar = c3.form_submit_button("❌ Fechar")

        conn = get_conn()

        if salvar:
            conn.execute("""
                UPDATE clientes
                SET nome=?, usuario=?, senha=?, servidor=?, sistema=?, vencimento=?
                WHERE id=?
            """, (nome, usuario, senha, servidor, sistema, venc.strftime("%Y-%m-%d"), cliente["id"]))
            conn.commit()
            conn.close()

            st.cache_data.clear()
            st.session_state["edit_id"] = None
            st.success("Salvo com sucesso!")
            st.rerun()

        if renovar:
            novo = (venc + timedelta(days=30)).strftime("%Y-%m-%d")
            conn.execute("UPDATE clientes SET vencimento=? WHERE id=?", (novo, cliente["id"]))
            conn.commit()
            conn.close()

            st.cache_data.clear()
            st.success("Renovado!")
            st.rerun()

        if fechar:
            st.session_state["edit_id"] = None

# =========================
# CADASTRO
# =========================
with tab2:
    st.subheader("➕ Novo Cliente")

    with st.form("cadastro"):

        nome = st.text_input("Cliente")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha")
        servidor = st.text_input("Servidor")
        sistema = st.selectbox("Sistema", ["IPTV", "P2P"])
        venc = st.date_input("Vencimento", datetime.now() + timedelta(days=30))
        custo = st.number_input("Custo", value=10.0)
        valor = st.number_input("Valor Cobrado", value=30.0)
        whatsapp = st.text_input("WhatsApp")

        if st.form_submit_button("💾 Salvar"):
            conn = get_conn()
            conn.execute("""
                INSERT INTO clientes (nome, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, inicio, whatsapp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (nome, usuario, senha, servidor, sistema, venc.strftime("%Y-%m-%d"), custo, valor, datetime.now().strftime("%Y-%m-%d"), whatsapp))
            conn.commit()
            conn.close()

            st.cache_data.clear()
            st.success("Cliente cadastrado!")
            st.rerun()

# =========================
# COBRANÇA
# =========================
with tab3:
    st.subheader("🚨 Cobrança")

    if not df.empty:
        for _, r in df.sort_values("dias").iterrows():

            cor = "🔴" if r["dias"] < 0 else "🟡" if r["dias"] <= 2 else "🟢"
            st.write(f"{cor} {r['nome']} - vence {r['vencimento']}")

# =========================
# BACKUP
# =========================
with tab4:
    st.subheader("⚙️ Backup")

    if not df.empty:
        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Baixar Backup",
            csv,
            "backup_clientes.csv",
            "text/csv"
        )
