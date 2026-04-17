import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io
import base64

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    
    /* Cores das linhas na cobrança */
    .cliente-row { border-radius: 12px; padding: 12px; margin-bottom: 10px; border: 1px solid #30363d; display: flex; align-items: center; gap: 15px; }
    .row-vencido { background-color: #331111; border-left: 8px solid #ff4b4b; }
    .row-hoje { background-color: #3d2b11; border-left: 8px solid #ffa500; }
    .row-amanha { background-color: #333311; border-left: 8px solid #ffff00; }
    .row-em-dia { background-color: #112233; border-left: 8px solid #00d4ff; }
    
    .img-servidor { width: 60px; height: 60px; border-radius: 8px; object-fit: cover; border: 1px solid #444; }

    /* Estilo dos Botões de Filtro */
    .stButton > button { width: 100%; border-radius: 8px; }

    /* Botões de Cliente (Lista Principal) */
    .btn-cliente > div > button {
        text-align: left !important;
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 15px !important;
        display: flex !important;
        align-items: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, usuario TEXT, senha TEXT, 
                  servidor TEXT, sistema TEXT, vencimento TEXT, custo REAL, 
                  mensalidade REAL, inicio TEXT, whatsapp TEXT, observacao TEXT, logo_blob TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    conn.commit(); conn.close()

def get_servidores():
    fixos = ["UNIPLAY", "MUNDOGF", "P2BRAZ", "BLADETV", "UNITV", "P2CINETV", 
             "SPEEDTV", "PLAYTV", "MEGATV", "BOB PLAYER", "IBO PLAYER", "IBOPLAYER PRO"]
    conn = sqlite3.connect('supertv_gestao.db')
    try:
        extras = pd.read_sql_query("SELECT nome FROM lista_servidores", conn)['nome'].tolist()
    except: extras = []
    conn.close()
    return sorted(list(set(fixos + extras)))

def image_to_base64(image_file):
    if image_file is not None:
        return base64.b64encode(image_file.read()).decode()
    return None

init_db()

# --- 4. CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- 5. DASHBOARD CALCULOS ---
if not df.empty:
    hoje = datetime.now().date()
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 0)

# --- 6. HEADER ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ NOVO CADASTRO", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔎 Pesquisar...", placeholder="Nome ou Usuário")
    if not df.empty:
        df_f = df[df['nome'].str.contains(busca, case=False, na=False) | df['usuario'].str.contains(busca, case=False, na=False)] if busca else df
        for _, r in df_f.sort_values(by='nome').iterrows():
            img_tag = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            col_img, col_btn = st.columns([0.1, 0.9])
            with col_img:
                st.markdown(f'<img src="{img_tag}" class="img-servidor">', unsafe_allow_html=True)
            with col_btn:
                st.markdown('<div class="btn-cliente">', unsafe_allow_html=True)
                label = f"{str(r['nome']).upper()} | User: {r['usuario']} | Senha: {r['senha']} | Servidor: {r['servidor']} | Sis: {r['sistema']} | Venc: {r['vencimento']}"
                if st.button(label, key=f"clie_{r['id']}"):
                    with st.expander("📄 DADOS COMPLETOS", expanded=True):
                        st.write(f"**WhatsApp:** {r['whatsapp']} | **Início:** {r['inicio']} | **Custo:** R${r['custo']} | **Mensalidade:** R${r['mensalidade']}")
                        st.info(f"**Observação:** {r['observacao']}")
                st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.subheader("🚀 Novo Cadastro")
    with st.form("form_add"):
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("CLIENTE")
        user = c2.text_input("USUÁRIO")
        senha = c3.text_input("SENHA")
        serv = c1.selectbox("SERVIDOR", get_servidores())
        sist = c2.selectbox("SISTEMA", ["IPTV", "P2P"])
        venc = c3.date_input("VENCIMENTO", value=datetime.now() + timedelta(days=30))
        custo = c1.number_input("CUSTO", value=10.0)
        valor = c2.number_input("VALOR COBRADO", value=35.0)
        ini = c3.date_input("INÍCIOU DIA", value=datetime.now())
        whats = c1.text_input("WHATSAPP (Ex: 62999999999)")
        img_serv = st.file_uploader("UPLOAD DA IMAGEM DO SERVIDOR", type=['png', 'jpg', 'jpeg'])
        obs = st.text_area("OBSERVAÇÃO")
        if st.form_submit_button("🚀 SALVAR CADASTRO"):
            l_b = image_to_base64(img_serv)
            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("INSERT INTO clientes (nome, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, inicio, whatsapp, observacao, logo_blob) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (nome, user, senha, serv, sist, venc.strftime('%Y-%m-%d'), custo, valor, ini.strftime('%Y-%m-%d'), whats, obs, l_b))
            conn.commit(); conn.close(); st.success("Salvo!"); st.rerun()

with tab3:
    st.subheader("🚨 Central de Cobrança")
    pix = "62.326.879/0001-13"
    if not df.empty:
        st.write("📂 **Filtros Exclusivos:**")
        f_cols = st.columns(7)
        if 'f_cob' not in st.session_state: st.session_state.f_cob = "Todos"
        if f_cols[0].button("TODOS"): st.session_state.f_cob = "Todos"
        if f_cols[1].button("VENCIDOS"): st.session_state.f_cob = "Vencidos"
        if f_cols[2].button("HOJE"): st.session_state.f_cob = "Hoje"
        if f_cols[3].button("AMANHÃ"): st.session_state.f_cob = "Amanha"
        if f_cols[4].button("2 DIAS"): st.session_state.f_cob = "2 Dias"
        if f_cols[5].button("3 DIAS"): st.session_state.f_cob = "3 Dias"
        if f_cols[6].button("4 DIAS+"): st.session_state.f_cob = "4 Mais"

        df_c = df.copy()
        if st.session_state.f_cob == "Vencidos": df_c = df[df['dias_res'] < 0]
        elif st.session_state.f_cob == "Hoje": df_c = df[df['dias_res'] == 0]
        elif st.session_state.f_cob == "Amanha": df_c = df[df['dias_res'] == 1]
        elif st.session_state.f_cob == "2 Dias": df_c = df[df['dias_res'] == 2]
        elif st.session_state.f_cob == "3 Dias": df_c = df[df['dias_res'] == 3]
        elif st.session_state.f_cob == "4 Mais": df_c = df[df['dias_res'] >= 4]

        st.info(f"Filtro: {st.session_state.f_cob} ({len(df_c)} clientes)")
        clientes_sel = []
        for _, c in df_c.sort_values(by='dias_res').iterrows():
            cls = "row-vencido" if c['dias_res'] < 0 else "row-hoje" if c['dias_res'] == 0 else "row-amanha" if c['dias_res'] == 1 else "row-em-dia"
            col_ch, col_ca = st.columns([0.1, 0.9])
            if col_ch.checkbox("", key=f"sel_{c['id']}"): clientes_sel.append(c)
            col_ca.markdown(f'<div class="cliente-row {cls}"><b>{str(c["nome"]).upper()}</b> | Vence: {c["vencimento"]} ({c["dias_res"]} dias)</div>', unsafe_allow_html=True)

        if st.button(f"📲 DISPARAR ({len(clientes_sel)})", use_container_width=True):
            for i in clientes_sel:
                msg = f"Olá {str(i['nome']).split()[0]}! 👋 Assinatura {i['servidor']} vence dia {i['vencimento']}. Pix: {pix}"
                st.link_button(f"Enviar para {i['nome']}", f"https://wa.me/55{i['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Ajustes")
    aj1, aj2, aj3 = st.columns(3)
    with aj1:
        st.markdown("### 📂 UPLOAD")
        up = st.file_uploader("Excel", type=["xlsx"])
        if up and st.button("🚀 Importar"):
            pd.read_excel(up).to_sql('clientes', sqlite3.connect('supertv_gestao.db'), if_exists='append', index=False)
            st.success("OK!"); st.rerun()
    with aj2:
        st.markdown("### 💾 BACKUP")
        if st.button("📦 Gerar Excel"):
            out = io.BytesIO()
            pd.read_sql_query("SELECT * FROM clientes", sqlite3.connect('supertv_gestao.db')).to_excel(out, index=False)
            st.download_button("⬇️ Baixar", out.getvalue(), "backup.xlsx")
    with aj3:
        st.markdown("### 🔌 SERVIDOR")
        ns = st.text_input("Novo Nome")
        if st.button("➕ Adicionar"):
            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("INSERT INTO lista_servidores (nome) VALUES (?)", (ns.upper(),))
            conn.commit(); st.success("OK!"); st.rerun()
