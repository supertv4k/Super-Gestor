import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io
import base64

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# ======================
# CSS (igual ao seu)
# ======================
st.markdown("""
<style>
.main { background-color: #0e1117; color: white; }

.header-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
    margin-bottom: 30px;
}

.logo-gestao { width: 450px; margin-bottom: -20px !important; }
.logo-supertv { width: 380px; }

.metric-container {
    background-color: #161b22;
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #30363d;
    text-align: center;
}

.metric-label { color: white; font-size: 14px; font-weight: bold; }
.val-azul { color: #00d4ff; font-size: 24px; font-weight: bold; }
.val-verde { color: #28a745; font-size: 24px; font-weight: bold; }
.val-laranja { color: #ffa500; font-size: 24px; font-weight: bold; }
.val-vermelho { color: #ff4b4b; font-size: 24px; font-weight: bold; }

.cliente-row {
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 10px;
    border: 1px solid #30363d;
}
</style>
""", unsafe_allow_html=True)

# ======================
# DB
# ======================
def get_conn():
    return sqlite3.connect("supertv_gestao.db")

def init_db():
    conn = get_conn()
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
        observacao TEXT,
        logo_blob TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ======================
# ORDEM FIXA OFICIAL
# ======================
COLUNAS_FIXAS = [
    "nome",
    "usuario",
    "senha",
    "servidor",
    "sistema",
    "vencimento",
    "custo",
    "mensalidade",
    "inicio",
    "whatsapp",
    "observacao",
    "logo_blob"
]

# ======================
# LOAD
# ======================
conn = get_conn()
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# ======================
# NORMALIZAÇÃO (IMPORTANTE)
# ======================
if not df.empty:
    df = df[[c for c in COLUNAS_FIXAS if c in df.columns]]

    hoje = datetime.now().date()
    df["dt_venc"] = pd.to_datetime(df["vencimento"], errors="coerce").dt.date
    df["dias_res"] = df["dt_venc"].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)

# ======================
# HEADER
# ======================
st.markdown("""
<div class="header-container">
<img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao">
<img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv">
</div>
""", unsafe_allow_html=True)

# ======================
# EXPORTAÇÃO (ORDEM FIXA CORRETA)
# ======================
def exportar_excel(df):
    df_export = df.copy()

    # GARANTE ORDEM EXATA PEDIDA
    df_export = df_export.reindex(columns=COLUNAS_FIXAS)

    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="clientes")

    buffer.seek(0)
    return buffer

# ======================
# ABAS
# ======================
tab1, tab2, tab3, tab4 = st.tabs(["CLIENTES", "NOVO", "COBRANÇA", "AJUSTES"])

# ======================
# CLIENTES
# ======================
with tab1:
    st.subheader("Clientes")

    if not df.empty:
        for _, r in df.iterrows():
            st.write(f"{r['nome']} | {r['usuario']} | {r['servidor']} | {r['vencimento']}")

# ======================
# NOVO CLIENTE
# ======================
with tab2:
    st.subheader("Cadastro")

    with st.form("form"):

        nome = st.text_input("CLIENTE")
        usuario = st.text_input("USUÁRIO")
        senha = st.text_input("SENHA")
        servidor = st.text_input("SERVIDOR")
        sistema = st.text_input("SISTEMA")

        vencimento = st.date_input("VENCIMENTO", datetime.now() + timedelta(days=30))
        custo = st.number_input("CUSTO", value=0.0)
        mensalidade = st.number_input("VALOR COBRADO", value=0.0)

        inicio = st.date_input("INÍCIOU DIA", datetime.now())

        whatsapp = st.text_input("WHATSAPP")
        observacao = st.text_area("OBSERVAÇÃO")

        img = st.file_uploader("IMAGEM")

        if st.form_submit_button("SALVAR"):

            logo = base64.b64encode(img.read()).decode() if img else None

            conn = get_conn()
            conn.execute("""
            INSERT INTO clientes (
                nome,usuario,senha,servidor,sistema,
                vencimento,custo,mensalidade,inicio,
                whatsapp,observacao,logo_blob
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                nome,usuario,senha,servidor,sistema,
                vencimento.strftime("%Y-%m-%d"),
                custo,mensalidade,
                inicio.strftime("%Y-%m-%d"),
                whatsapp,observacao,logo
            ))

            conn.commit()
            conn.close()

            st.rerun()

# ======================
# COBRANÇA
# ======================
with tab3:
    st.subheader("Cobrança")
    st.info("Sem alteração estrutural")

# ======================
# AJUSTES (IMPORT / EXPORT CORRIGIDO)
# ======================
with tab4:
    st.subheader("Ajustes")

    conn = get_conn()
    df_b = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()

    # ================= DOWNLOAD CORRETO =================
    if st.button("BAIXAR LISTA (ORDEM CORRETA)"):

        df_b = df_b.reindex(columns=COLUNAS_FIXAS)

        excel = exportar_excel(df_b)

        st.download_button(
            "⬇️ DOWNLOAD EXCEL",
            data=excel.getvalue(),
            file_name="clientes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # ================= IMPORT CORRIGIDO =================
    up = st.file_uploader("IMPORTAR EXCEL", type=["xlsx"])

    if up and st.button("IMPORTAR"):

        df_import = pd.read_excel(up)

        # força ordem correta
        for c in COLUNAS_FIXAS:
            if c not in df_import.columns:
                df_import[c] = None

        df_import = df_import[COLUNAS_FIXAS]

        conn = get_conn()
        df_import.to_sql("clientes", conn, if_exists="append", index=False)
        conn.commit()
        conn.close()

        st.rerun()
