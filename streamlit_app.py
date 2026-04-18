import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io
import base64

# --- CONFIG ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- CSS ---
st.markdown("""
<style>
.main { background-color: #0e1117; color: white; }
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
</style>
""", unsafe_allow_html=True)

# --- DB ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT, usuario TEXT, senha TEXT,
        servidor TEXT, sistema TEXT,
        vencimento TEXT, custo REAL,
        mensalidade REAL, inicio TEXT,
        whatsapp TEXT, observacao TEXT,
        logo_blob TEXT)''')
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect('supertv_gestao.db')
    df = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    return df

init_db()

# 🔥 IMPORTANTE: sempre recarregar aqui
df = load_data()

if not df.empty:
    hoje = datetime.now().date()
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["CLIENTES", "CADASTRO", "COBRANÇA", "AJUSTES"])

# ======================
# CLIENTES FUNCIONANDO
# ======================
with tab1:
    st.subheader("Clientes")

    if not df.empty:
        for _, r in df.iterrows():
            st.write(f"{r['nome']} | {r['usuario']} | {r['servidor']} | {r['vencimento']}")
    else:
        st.warning("Nenhum cliente cadastrado")

# ======================
# CADASTRO CORRIGIDO
# ======================
with tab2:
    st.subheader("Novo Cadastro")

    with st.form("form", clear_on_submit=True):

        nome = st.text_input("CLIENTE")
        user = st.text_input("USUÁRIO")
        senha = st.text_input("SENHA")

        serv = st.text_input("SERVIDOR")
        sist = st.selectbox("SISTEMA", ["IPTV", "P2P"])

        venc = st.date_input("VENCIMENTO", datetime.now() + timedelta(days=30))

        custo = st.number_input("CUSTO", value=10.0)
        valor = st.number_input("VALOR COBRADO", value=35.0)

        ini = st.date_input("INÍCIOU DIA", datetime.now())

        whats = st.text_input("WHATSAPP")
        obs = st.text_area("OBSERVAÇÃO")

        img = st.file_uploader("IMAGEM", type=["png", "jpg", "jpeg"])

        if st.form_submit_button("SALVAR"):

            logo = base64.b64encode(img.read()).decode() if img else None

            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("""
                INSERT INTO clientes (
                    nome, usuario, senha,
                    servidor, sistema,
                    vencimento, custo,
                    mensalidade, inicio,
                    whatsapp, observacao,
                    logo_blob
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                nome, user, senha,
                serv, sist,
                venc.strftime("%Y-%m-%d"),
                custo, valor,
                ini.strftime("%Y-%m-%d"),
                whats, obs,
                logo
            ))
            conn.commit()
            conn.close()

            st.rerun()

# ======================
# COBRANÇA (RESTAURADO)
# ======================
with tab3:
    st.subheader("Cobrança")

    if df.empty:
        st.warning("Sem dados")
    else:
        for _, r in df.iterrows():
            st.write(f"🔴 {r['nome']} vence {r['vencimento']}")

# ======================
# AJUSTES (RESTAURADO)
# ======================
with tab4:
    st.subheader("Ajustes")

    up = st.file_uploader("Importar Excel", type=["xlsx"])

    if up and st.button("Importar"):
        pd.read_excel(up).to_sql('clientes', sqlite3.connect('supertv_gestao.db'),
                                 if_exists='append', index=False)
        st.rerun()

    if st.button("Backup"):
        out = io.BytesIO()
        pd.read_sql_query("SELECT * FROM clientes", sqlite3.connect('supertv_gestao.db')).to_excel(out, index=False)
        st.download_button("Baixar", out.getvalue(), "backup.xlsx")
