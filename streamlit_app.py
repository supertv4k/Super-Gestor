import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import base64
import io

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="SUPERTV4K DASHBOARD PRO", layout="wide")

# =========================
# STYLE CLEAN PRO
# =========================
st.markdown("""
<style>
body { background-color: #0e1117; }

.card {
    background-color: #161b22;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #30363d;
}

.title {
    font-size: 18px;
    font-weight: bold;
    color: white;
}

.metric {
    font-size: 26px;
    font-weight: bold;
}

.green { color: #28a745; }
.red { color: #ff4b4b; }
.blue { color: #00d4ff; }
.orange { color: #ffa500; }
</style>
""", unsafe_allow_html=True)

# =========================
# DB
# =========================
def load_data():
    conn = sqlite3.connect("supertv_gestao.db")
    df = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    return df

# =========================
# INIT VIEW
# =========================
df = load_data()

if not df.empty:
    hoje = datetime.now().date()
    df["venc"] = pd.to_datetime(df["vencimento"], errors="coerce").dt.date
    df["dias"] = df["venc"].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)

# =========================
# HEADER DASHBOARD
# =========================
st.title("📊 SUPERTV4K DASHBOARD PRO")

# =========================
# METRICS
# =========================
if df.empty:
    st.warning("Nenhum cliente cadastrado ainda.")
else:

    total = len(df)
    vencidos = len(df[df["dias"] < 0])
    hoje_vence = len(df[df["dias"] == 0])
    ativos = total - vencidos

    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(f"""
    <div class="card">
        <div class="title">CLIENTES</div>
        <div class="metric blue">{total}</div>
    </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"""
    <div class="card">
        <div class="title">ATIVOS</div>
        <div class="metric green">{ativos}</div>
    </div>
    """, unsafe_allow_html=True)

    col3.markdown(f"""
    <div class="card">
        <div class="title">VENCE HOJE</div>
        <div class="metric orange">{hoje_vence}</div>
    </div>
    """, unsafe_allow_html=True)

    col4.markdown(f"""
    <div class="card">
        <div class="title">VENCIDOS</div>
        <div class="metric red">{vencidos}</div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# FILTROS
# =========================
st.divider()

filtro = st.selectbox(
    "🔎 FILTRAR CLIENTES",
    ["TODOS", "ATIVOS", "VENCIDOS", "VENCE HOJE", "3 DIAS", "7 DIAS"]
)

if not df.empty:

    if filtro == "VENCIDOS":
        df_view = df[df["dias"] < 0]
    elif filtro == "ATIVOS":
        df_view = df[df["dias"] >= 0]
    elif filtro == "VENCE HOJE":
        df_view = df[df["dias"] == 0]
    elif filtro == "3 DIAS":
        df_view = df[df["dias"].between(1, 3)]
    elif filtro == "7 DIAS":
        df_view = df[df["dias"].between(1, 7)]
    else:
        df_view = df

    # =========================
    # LISTA CLIENTES
    # =========================
    st.subheader("📋 CLIENTES")

    for _, r in df_view.sort_values("dias").iterrows():

        status = "green" if r["dias"] >= 5 else "orange" if r["dias"] >= 0 else "red"

        st.markdown(f"""
        <div class="card">
            <b>{r['nome']}</b> | {r['usuario']} | {r['servidor']}  
            <br>
            📅 Venc: {r['vencimento']} | 🔴 Status: <span class="{status}">{r['dias']} dias</span>
        </div>
        """, unsafe_allow_html=True)

# =========================
# CADASTRO SIMPLES E ESTÁVEL
# =========================
st.divider()
st.subheader("➕ NOVO CLIENTE")

with st.form("cad"):

    nome = st.text_input("CLIENTE")
    usuario = st.text_input("USUÁRIO")
    senha = st.text_input("SENHA")

    servidor = st.text_input("SERVIDOR")
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

        st.success("Cliente salvo!")
        st.rerun()
