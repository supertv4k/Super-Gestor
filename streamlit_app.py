import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io

st.set_page_config(page_title="SUPERTV4K GESTÃO PRO", layout="wide")

st.markdown("""
<style>
.main { background-color: #0e1117; color: white; }
.metric-box {background:#161b22;padding:15px;border-radius:10px;border:1px solid #30363d;text-align:center;}
.metric-title {font-size:13px;color:#aaa;}
.metric-value {font-size:26px;font-weight:bold;}
.row {padding:10px;margin-bottom:8px;border-radius:10px;border:1px solid #30363d;}
.vencido {background:#331111;border-left:6px solid red;}
.hoje {background:#3d2b11;border-left:6px solid orange;}
.ok {background:#112233;border-left:6px solid #00d4ff;}
</style>
""", unsafe_allow_html=True)

def conectar():
    return sqlite3.connect("supertv.db")

def criar_db():
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
        observacao TEXT
    )
    """)
    conn.commit()
    conn.close()

criar_db()

def carregar():
    conn = conectar()
    df = pd.read_sql("SELECT * FROM clientes", conn)
    conn.close()
    return df

def salvar(d):
    conn = conectar()
    conn.execute("""
    INSERT OR IGNORE INTO clientes
    (nome,usuario,senha,servidor,sistema,vencimento,custo,mensalidade,inicio,whatsapp,observacao)
    VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, d)
    conn.commit()
    conn.close()

def atualizar(id, d):
    conn = conectar()
    conn.execute("""
    UPDATE clientes SET
    nome=?,usuario=?,senha=?,servidor=?,sistema=?,vencimento=?,custo=?,mensalidade=?,inicio=?,whatsapp=?,observacao=?
    WHERE id=?
    """, (*d, id))
    conn.commit()
    conn.close()

def excluir(id):
    conn = conectar()
    conn.execute("DELETE FROM clientes WHERE id=?", (id,))
    conn.commit()
    conn.close()

def importar(file):
    df = pd.read_excel(file)
    df.columns = [c.lower().strip() for c in df.columns]

    mapa = {"cliente":"nome","user":"usuario","valor":"mensalidade","obs":"observacao"}
    df = df.rename(columns=mapa)

    if "vencimento" in df:
        df["vencimento"] = pd.to_datetime(df["vencimento"], errors="coerce").dt.strftime('%Y-%m-%d')
    if "inicio" in df:
        df["inicio"] = pd.to_datetime(df["inicio"], errors="coerce").dt.strftime('%Y-%m-%d')

    cols = ["nome","usuario","senha","servidor","sistema","vencimento","custo","mensalidade","inicio","whatsapp","observacao"]

    for c in cols:
        if c not in df:
            df[c] = None

    df = df[cols]

    conn = conectar()
    existentes = pd.read_sql("SELECT usuario FROM clientes", conn)
    df = df[~df["usuario"].isin(existentes["usuario"])]
    df.to_sql("clientes", conn, if_exists="append", index=False)
    conn.close()

    return len(df)

df = carregar()

if df.empty:
    st.warning("⚠️ Nenhum cliente cadastrado ainda")
else:
    hoje = datetime.now().date()
    df["venc"] = pd.to_datetime(df["vencimento"], errors="coerce").dt.date
    df["dias"] = df["venc"].apply(lambda x: (x-hoje).days if pd.notnull(x) else 999)

    total = len(df)
    vencidos = len(df[df["dias"] < 0])
    hoje_v = len(df[df["dias"] == 0])
    ativos = total - vencidos

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f"<div class='metric-box'><div class='metric-title'>CLIENTES</div><div class='metric-value'>{total}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-box'><div class='metric-title'>ATIVOS</div><div class='metric-value'>{ativos}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-box'><div class='metric-title'>HOJE</div><div class='metric-value'>{hoje_v}</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-box'><div class='metric-title'>VENCIDOS</div><div class='metric-value'>{vencidos}</div></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Clientes","Cadastro","Cobrança","Importar/Backup"])

with tab1:
    if not df.empty:
        busca = st.text_input("Buscar cliente")
        df_f = df[df["nome"].str.contains(busca, case=False, na=False)] if busca else df

        for _, r in df_f.iterrows():
            status = "ok"
            if r["dias"] < 0: status = "vencido"
            elif r["dias"] == 0: status = "hoje"

            with st.expander(f"{r['nome']} | {r['usuario']}"):
                st.markdown(f"<div class='row {status}'>Vencimento: {r['vencimento']}</div>", unsafe_allow_html=True)

                with st.form(f"edit{r['id']}"):
                    nome = st.text_input("Nome", r["nome"])
                    user = st.text_input("Usuário", r["usuario"])
                    senha = st.text_input("Senha", r["senha"])
                    serv = st.text_input("Servidor", r["servidor"])
                    venc = st.date_input("Vencimento", datetime.strptime(r["vencimento"], "%Y-%m-%d"))

                    if st.form_submit_button("Salvar"):
                        atualizar(r["id"], (nome,user,senha,serv,r["sistema"],venc.strftime("%Y-%m-%d"),r["custo"],r["mensalidade"],r["inicio"],r["whatsapp"],r["observacao"]))
                        st.rerun()

                if st.button("Excluir", key=f"del{r['id']}"):
                    excluir(r["id"])
                    st.rerun()

with tab2:
    with st.form("novo"):
        nome = st.text_input("Nome")
        user = st.text_input("Usuário")
        senha = st.text_input("Senha")
        serv = st.text_input("Servidor")
        venc = st.date_input("Vencimento", datetime.now()+timedelta(days=30))
        valor = st.number_input("Mensalidade", value=35.0)

        if st.form_submit_button("Salvar"):
            salvar((nome,user,senha,serv,"IPTV",venc.strftime("%Y-%m-%d"),0,valor,datetime.now().strftime("%Y-%m-%d"),"", ""))
            st.rerun()

with tab3:
    if not df.empty:
        for _, c in df.iterrows():
            if c["whatsapp"]:
                msg = f"Olá {c['nome']}! Seu vencimento é {c['vencimento']}"
                link = f"https://wa.me/55{c['whatsapp']}?text={urllib.parse.quote(msg)}"
                st.link_button(f"Cobrar {c['nome']}", link)

with tab4:
    file = st.file_uploader("Importar Excel", type=["xlsx"])
    if file and st.button("Importar"):
        total = importar(file)
        st.success(f"{total} clientes importados")

    if st.button("Baixar Backup"):
        conn = conectar()
        df_b = pd.read_sql("SELECT * FROM clientes", conn)
        conn.close()

        buffer = io.BytesIO()
        df_b.to_excel(buffer, index=False)

        st.download_button("Download", buffer.getvalue(), "clientes.xlsx"
