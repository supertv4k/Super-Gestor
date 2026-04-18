import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io
import base64

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# =========================
# CSS (MANTIDO)
# =========================
st.markdown("""
<style>
.main { background-color: #0e1117; color: white; }
.header-container { display: flex; flex-direction: column; align-items: center; }
.metric-container { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
.metric-label { color: white; font-size: 14px; font-weight: bold; }
.val-azul { color: #00d4ff; font-size: 24px; font-weight: bold; }
.val-verde { color: #28a745; font-size: 24px; font-weight: bold; }
.val-laranja { color: #ffa500; font-size: 24px; font-weight: bold; }
.val-vermelho { color: #ff4b4b; font-size: 24px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# =========================
# BANCO (OTIMIZADO)
# =========================
def get_conn():
    return sqlite3.connect("supertv_gestao.db")

def load_data():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    return df

# CACHE (IMPORTANTE PARA LEVEZA)
@st.cache_data(ttl=5)
def get_data():
    df = load_data()
    if df.empty:
        return df

    hoje = datetime.now().date()
    df["dt_venc"] = pd.to_datetime(df["vencimento"], errors="coerce").dt.date
    df["dias_res"] = df["dt_venc"].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    return df

# =========================
# HEADER
# =========================
st.markdown("""
<div class="header-container">
<h2>📺 SUPERTV4K GESTÃO PRO</h2>
</div>
""", unsafe_allow_html=True)

df = get_data()

# =========================
# MÉTRICAS (OTIMIZADO)
# =========================
if not df.empty:
    total = len(df)
    vencidos = len(df[df["dias_res"] < 0])
    ativos = total - vencidos
    hoje_venc = len(df[df["dias_res"] == 0])

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("TOTAL", total)
    c2.metric("ATIVOS", ativos)
    c3.metric("HOJE", hoje_venc)
    c4.metric("VENCIDOS", vencidos)

# =========================
# ABAS
# =========================
tab1, tab2, tab3, tab4 = st.tabs(["CLIENTES", "CADASTRO", "COBRANÇA", "BACKUP"])

# =========================
# LISTA CLIENTES (OTIMIZADO)
# =========================
with tab1:
    busca = st.text_input("🔎 Buscar cliente")

    if not df.empty:
        df_f = df.copy()
        if busca:
            df_f = df_f[df_f["nome"].str.contains(busca, case=False, na=False)]

        for _, r in df_f.iterrows():
            st.write(f"👤 {r['nome']} | {r['usuario']} | {r['vencimento']}")

# =========================
# CADASTRO
# =========================
with tab2:
    with st.form("cadastro"):
        nome = st.text_input("Cliente")
        user = st.text_input("Usuário")
        senha = st.text_input("Senha")
        servidor = st.text_input("Servidor")
        sistema = st.selectbox("Sistema", ["IPTV", "P2P"])
        venc = st.date_input("Vencimento", datetime.now() + timedelta(days=30))
        custo = st.number_input("Custo", value=10.0)
        valor = st.number_input("Valor Cobrado", value=35.0)
        whatsapp = st.text_input("WhatsApp")

        if st.form_submit_button("Salvar"):
            conn = get_conn()
            conn.execute("""
                INSERT INTO clientes (nome, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, inicio, whatsapp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (nome, user, senha, servidor, sistema, venc.strftime("%Y-%m-%d"), custo, valor, datetime.now().strftime("%Y-%m-%d"), whatsapp))
            conn.commit()
            conn.close()
            st.success("Cliente salvo!")

# =========================
# COBRANÇA (LEVE)
# =========================
with tab3:
    if not df.empty:
        for _, c in df.iterrows():
            cor = "🔴" if c["dias_res"] < 0 else "🟡" if c["dias_res"] <= 2 else "🟢"
            st.write(f"{cor} {c['nome']} - vence {c['vencimento']}")

# =========================
# BACKUP (CSV LEVE)
# =========================
with tab4:
    if st.button("Gerar backup"):
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Baixar CSV", csv, "backup.csv", "text/csv")
