import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io
import base64

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# -----------------------------
# CSS
# -----------------------------
st.markdown("""
<style>
.main { background-color: #0e1117; color: white; }

.header-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 30px;
}

.logo-gestao { width: 450px; margin-bottom: -20px; }
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

.row-vencido { background-color: #331111; border-left: 8px solid #ff4b4b; }
.row-hoje { background-color: #3d2b11; border-left: 8px solid #ffa500; }
.row-amanha { background-color: #333311; border-left: 8px solid #ffff00; }
.row-em-dia { background-color: #112233; border-left: 8px solid #00d4ff; }

.img-servidor {
    width: 55px;
    height: 55px;
    border-radius: 8px;
    object-fit: cover;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# CONEXÃO SEGURA
# -----------------------------
def get_conn():
    return sqlite3.connect("supertv_gestao.db")

# -----------------------------
# BANCO
# -----------------------------
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

    c.execute("""
    CREATE TABLE IF NOT EXISTS lista_servidores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE
    )
    """)

    conn.commit()
    conn.close()

# -----------------------------
# SERVIDORES
# -----------------------------
def get_servidores():
    fixos = ["UNIPLAY", "MUNDOGF", "P2BRAZ", "BLADETV", "UNITV"]

    conn = get_conn()
    try:
        extras = pd.read_sql_query("SELECT nome FROM lista_servidores", conn)["nome"].tolist()
    except:
        extras = []
    conn.close()

    return sorted(list(set(fixos + extras)))

# -----------------------------
# DATA
# -----------------------------
def format_data_br(data_str):
    try:
        return datetime.strptime(data_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return data_str

# -----------------------------
# INIT
# -----------------------------
init_db()

# -----------------------------
# LOAD CLIENTES
# -----------------------------
try:
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
except:
    df = pd.DataFrame()

# -----------------------------
# DIAS
# -----------------------------
if not df.empty:
    hoje = datetime.now().date()
    df["dt_venc_calc"] = pd.to_datetime(df["vencimento"], errors="coerce").dt.date
    df["dias_res"] = df["dt_venc_calc"].apply(
        lambda x: (x - hoje).days if pd.notnull(x) else 999
    )

# -----------------------------
# HEADER
# -----------------------------
st.markdown("""
<div class="header-container">
<img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao">
<img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv">
</div>
""", unsafe_allow_html=True)

# -----------------------------
# MÉTRICAS
# -----------------------------
if not df.empty:
    total = len(df)
    vencidos = len(df[df["dias_res"] < 0])
    hoje_venc = len(df[df["dias_res"] == 0])
    ativos = total - vencidos

    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(f"<div class='metric-container'><div class='metric-label'>TOTAL</div><div class='val-azul'>{total}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-container'><div class='metric-label'>ATIVOS</div><div class='val-verde'>{ativos}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-container'><div class='metric-label'>HOJE</div><div class='val-laranja'>{hoje_venc}</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-container'><div class='metric-label'>VENCIDOS</div><div class='val-vermelho'>{vencidos}</div></div>", unsafe_allow_html=True)

# -----------------------------
# ABAS
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs(["CLIENTES", "NOVO", "COBRANÇA", "AJUSTES"])

# =============================
# CLIENTES
# =============================
with tab1:
    busca = st.text_input("Buscar cliente")

    if not df.empty:
        df_f = df[df["nome"].str.contains(busca, case=False, na=False)] if busca else df

        for _, r in df_f.iterrows():
            status = (
                "row-vencido" if r["dias_res"] < 0 else
                "row-hoje" if r["dias_res"] == 0 else
                "row-amanha" if r["dias_res"] == 1 else
                "row-em-dia"
            )

            st.markdown(f"""
            <div class="cliente-row {status}">
                <b>{r['nome']}</b> | {r['usuario']} | {r['servidor']} | {format_data_br(r['vencimento'])}
            </div>
            """, unsafe_allow_html=True)

# =============================
# NOVO CLIENTE
# =============================
with tab2:
    st.subheader("Novo Cadastro")

    with st.form("form"):
        c1, c2, c3 = st.columns(3)

        nome = c1.text_input("Nome")
        usuario = c2.text_input("Usuário")
        senha = c3.text_input("Senha")

        servidor = c1.selectbox("Servidor", get_servidores())
        sistema = c2.selectbox("Sistema", ["IPTV", "P2P"])
        venc = c3.date_input("Vencimento", datetime.now() + timedelta(days=30))

        custo = c1.number_input("Custo", value=10.0)
        valor = c2.number_input("Valor", value=35.0)
        inicio = c3.date_input("Início", datetime.now())

        whatsapp = c1.text_input("WhatsApp")
        obs = st.text_area("Observação")

        img = st.file_uploader("Imagem", type=["png", "jpg", "jpeg"])

        if st.form_submit_button("Salvar"):
            logo = base64.b64encode(img.read()).decode() if img else None

            conn = get_conn()
            conn.execute("""
            INSERT INTO clientes (
                nome, usuario, senha, servidor, sistema,
                vencimento, custo, mensalidade, inicio,
                whatsapp, observacao, logo_blob
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                nome, usuario, senha, servidor, sistema,
                venc.strftime("%Y-%m-%d"), custo, valor,
                inicio.strftime("%Y-%m-%d"), whatsapp, obs, logo
            ))
            conn.commit()
            conn.close()

            st.success("Cliente salvo!")
            st.rerun()

# =============================
# COBRANÇA
# =============================
with tab3:
    st.subheader("Cobrança")

    if not df.empty:
        selecionados = []

        for _, c in df.iterrows():
            if st.checkbox(c["nome"]):
                selecionados.append(c)

        if st.button("Enviar WhatsApp"):
            for i in selecionados:
                msg = f"Olá {i['nome']}, vence em {format_data_br(i['vencimento'])}"
                st.link_button(
                    "Enviar",
                    f"https://wa.me/55{i['whatsapp']}?text={urllib.parse.quote(msg)}"
                )

# =============================
# AJUSTES (BACKUP BLINDADO)
# =============================
with tab4:
    st.subheader("Backup Blindado")

    if st.button("📦 GERAR BACKUP SEGURO"):

        try:
            conn = get_conn()
            df_b = pd.read_sql_query("SELECT * FROM clientes", conn)
            conn.close()

            # ---------------- CSV (PRINCIPAL) ----------------
            csv_data = df_b.to_csv(index=False).encode("utf-8")

            st.download_button(
                "⬇️ Baixar CSV (100% seguro)",
                data=csv_data,
                file_name="backup_clientes.csv",
                mime="text/csv"
            )

            # ---------------- EXCEL (OPCIONAL) ----------------
            try:
                import openpyxl

                excel_buffer = io.BytesIO()

                with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                    df_b.to_excel(writer, index=False, sheet_name="clientes")

                excel_buffer.seek(0)

                st.download_button(
                    "⬇️ Baixar Excel (opcional)",
                    data=excel_buffer.getvalue(),
                    file_name="backup_clientes.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except:
                st.info("Excel indisponível no ambiente — use o CSV")

        except Exception as e:
            st.error(f"Erro no backup: {e}")
