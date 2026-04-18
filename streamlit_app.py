import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io
import base64

# CONFIG
st.set_page_config(page_title="SUPERTV4K GESTÃO PRO", layout="wide")

# CSS
st.markdown("""
<style>
.main { background-color: #0e1117; color: white; }
.header-container { display:flex; flex-direction:column; align-items:center; margin-bottom:30px; }
.logo-gestao { width:420px; }
.logo-supertv { width:350px; }

.metric-container {
    background:#161b22;
    padding:15px;
    border-radius:10px;
    border:1px solid #30363d;
    text-align:center;
}
.metric-label { font-size:14px; font-weight:bold; }
.val-azul { color:#00d4ff; font-size:24px; font-weight:bold; }
.val-verde { color:#28a745; font-size:24px; font-weight:bold; }
.val-laranja { color:#ffa500; font-size:24px; font-weight:bold; }
.val-vermelho { color:#ff4b4b; font-size:24px; font-weight:bold; }

.cliente-row { border-radius:12px; padding:12px; margin-bottom:10px; border:1px solid #30363d; display:flex; align-items:center; }
.row-vencido { background:#331111; border-left:8px solid red; }
.row-hoje { background:#3d2b11; border-left:8px solid orange; }
.row-amanha { background:#333311; border-left:8px solid yellow; }
.row-ok { background:#112233; border-left:8px solid #00d4ff; }

.img-servidor { width:55px; height:55px; border-radius:8px; }
</style>
""", unsafe_allow_html=True)

# BANCO
def conectar():
    return sqlite3.connect('supertv_gestao.db')

def init_db():
    conn = conectar()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        usuario TEXT UNIQUE,
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
    conn.execute("""
    CREATE TABLE IF NOT EXISTS lista_servidores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE
    )
    """)
    conn.commit()
    conn.close()

init_db()

def get_servidores():
    base = ["UNIPLAY","MUNDOGF","P2BRAZ","BLADETV","UNITV"]
    conn = conectar()
    extras = pd.read_sql("SELECT nome FROM lista_servidores", conn)["nome"].tolist()
    conn.close()
    return sorted(list(set(base + extras)))

def carregar():
    conn = conectar()
    df = pd.read_sql("SELECT * FROM clientes", conn)
    conn.close()
    return df

df = carregar()

# HEADER
st.markdown("""
<div class="header-container">
<img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao">
<img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv">
</div>
""", unsafe_allow_html=True)

# PROCESSAMENTO
if not df.empty:
    hoje = datetime.now().date()
    df["venc"] = pd.to_datetime(df["vencimento"], errors="coerce").dt.date
    df["dias"] = df["venc"].apply(lambda x: (x-hoje).days if pd.notnull(x) else 999)

# MÉTRICAS
if not df.empty:
    total = len(df)
    vencidos = len(df[df["dias"] < 0])
    hoje_v = len(df[df["dias"] == 0])
    ativos = total - vencidos
    custo = df["custo"].sum()
    bruto = df["mensalidade"].sum()
    liquido = bruto - custo

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f"<div class='metric-container'><div class='metric-label'>CLIENTES</div><div class='val-azul'>{total}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-container'><div class='metric-label'>ATIVOS</div><div class='val-verde'>{ativos}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-container'><div class='metric-label'>HOJE</div><div class='val-laranja'>{hoje_v}</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-container'><div class='metric-label'>VENCIDOS</div><div class='val-vermelho'>{vencidos}</div></div>", unsafe_allow_html=True)

    c5,c6,c7 = st.columns(3)
    c5.markdown(f"<div class='metric-container'><div class='metric-label'>CUSTO</div><div class='val-vermelho'>R$ {custo:.2f}</div></div>", unsafe_allow_html=True)
    c6.markdown(f"<div class='metric-container'><div class='metric-label'>BRUTO</div><div class='val-azul'>R$ {bruto:.2f}</div></div>", unsafe_allow_html=True)
    c7.markdown(f"<div class='metric-container'><div class='metric-label'>LÍQUIDO</div><div class='val-verde'>R$ {liquido:.2f}</div></div>", unsafe_allow_html=True)

# TABS
tab1, tab2, tab3, tab4 = st.tabs(["CLIENTES","CADASTRO","COBRANÇA","AJUSTES"])

# CLIENTES
with tab1:
    if not df.empty:
        busca = st.text_input("Buscar")
        df_f = df[df["nome"].str.contains(busca, case=False, na=False)] if busca else df

        for _, r in df_f.iterrows():
            status = "row-ok"
            if r["dias"] < 0: status = "row-vencido"
            elif r["dias"] == 0: status = "row-hoje"
            elif r["dias"] == 1: status = "row-amanha"

            img = f"data:image/png;base64,{r['logo_blob']}" if r["logo_blob"] else "https://i.imgur.com/vH9XvI0.png"

            col1,col2 = st.columns([1,8])
            col1.markdown(f"<img src='{img}' class='img-servidor'>", unsafe_allow_html=True)

            if col2.button(f"{r['nome']} | {r['usuario']} | {r['servidor']} | {r['vencimento']}", key=r["id"]):
                st.info("Editar em breve (mantido simples para estabilidade)")

# CADASTRO
with tab2:
    with st.form("novo"):
        nome = st.text_input("Nome")
        user = st.text_input("Usuário")
        senha = st.text_input("Senha")
        serv = st.selectbox("Servidor", get_servidores())
        venc = st.date_input("Vencimento", datetime.now()+timedelta(days=30))
        valor = st.number_input("Mensalidade", value=35.0)

        if st.form_submit_button("Salvar"):
            conn = conectar()
            conn.execute("""
            INSERT INTO clientes (nome,usuario,senha,servidor,sistema,vencimento,custo,mensalidade,inicio,whatsapp,observacao)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,(nome,user,senha,serv,"IPTV",venc.strftime("%Y-%m-%d"),0,valor,datetime.now().strftime("%Y-%m-%d"),"",""))
            conn.commit()
            conn.close()
            st.rerun()

# COBRANÇA
with tab3:
    if not df.empty:
        for _, c in df.iterrows():
            if c["whatsapp"]:
                msg = f"Olá {c['nome']}! Vence {c['vencimento']}"
                link = f"https://wa.me/55{c['whatsapp']}?text={urllib.parse.quote(msg)}"
                st.link_button(f"Cobrar {c['nome']}", link)

# AJUSTES
with tab4:
    file = st.file_uploader("Importar Excel", type=["xlsx"])
    if file and st.button("Importar"):
        pd.read_excel(file).to_sql("clientes", conectar(), if_exists="append", index=False)
        st.success("Importado com sucesso")
        st.rerun()

    if st.button("Backup"):
        conn = conectar()
        df_b = pd.read_sql("SELECT * FROM clientes", conn)
        conn.close()
        buf = io.BytesIO()
        df_b.to_excel(buf, index=False)
        st.download_button("Download", buf.getvalue(), "clientes.xlsx")
