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
    .cliente-row { border-radius: 12px; padding: 12px; margin-bottom: 10px; border: 1px solid #30363d; }
    .row-vencido { background-color: #331111; border-left: 8px solid #ff4b4b; }
    .row-hoje { background-color: #3d2b11; border-left: 8px solid #ffa500; }
    .row-breve { background-color: #333311; border-left: 8px solid #ffff00; }
    .row-em-dia { background-color: #112233; border-left: 8px solid #00d4ff; }
    
    /* Botões de Cliente (Lista Principal) */
    div.stButton > button {
        width: 100%;
        text-align: left !important;
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }
    div.stButton > button:hover { border-color: #00d4ff !important; background-color: #1c2128 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    # Tabela de Clientes com todos os 11 campos + logo
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, usuario TEXT, senha TEXT, 
                  servidor TEXT, sistema TEXT, vencimento TEXT, custo REAL, 
                  mensalidade REAL, inicio TEXT, whatsapp TEXT, observacao TEXT, logo_blob TEXT)''')
    # Tabela de Servidores
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    conn.commit(); conn.close()

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    try:
        lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    except:
        lista = []
    conn.close()
    return lista if lista else ["UNITV", "UNIPLAY", "P2BRAZ", "MUNDOGF", "PLAY TV"]

init_db()

# --- 4. CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- 5. HEADER ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

if not df.empty:
    hoje = datetime.now().date()
    df['mensalidade'] = pd.to_numeric(df['mensalidade'], errors='coerce').fillna(0)
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 0)

# --- 6. ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ NOVO CADASTRO", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔎 Pesquisar...", placeholder="Nome ou Usuário")
    if not df.empty:
        df_f = df[df['nome'].str.contains(busca, case=False, na=False) | df['usuario'].str.contains(busca, case=False, na=False)] if busca else df
        
        for _, r in df_f.sort_values(by='nome').iterrows():
            # INFORMAÇÕES EXTERNAS NO BOTÃO
            label = f"👤 {str(r['nome']).upper()} | 🔑 {r['usuario']} | 🔓 {r['senha']} | 📶 {r['servidor']} | 🖥️ {r['sistema']} | 📅 {r['vencimento']}"
            
            if st.button(label, key=f"clie_{r['id']}"):
                with st.expander(f"📄 DETALHES DE {str(r['nome']).upper()}", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**USUÁRIO:** {r['usuario']}\n\n**SENHA:** {r['senha']}\n\n**WHATSAPP:** {r['whatsapp']}")
                    c2.markdown(f"**SERVIDOR:** {r['servidor']}\n\n**SISTEMA:** {r['sistema']}\n\n**VENCIMENTO:** {r['vencimento']}")
                    c3.markdown(f"**CUSTO:** R$ {r['custo']:.2f}\n\n**VALOR:** R$ {r['mensalidade']:.2f}\n\n**INÍCIO:** {r['inicio']}")
                    st.warning(f"**OBSERVAÇÃO:** {r['observacao']}")

with tab2:
    st.subheader("📝 Cadastrar Novo Cliente")
    with st.form("form_add"):
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("CLIENTE")
        user = c2.text_input("USUÁRIO")
        senha = c3.text_input("SENHA")
        serv = c1.selectbox("SERVIDOR", get_servidores())
        sist = c2.text_input("SISTEMA")
        venc = c3.date_input("VENCIMENTO", value=datetime.now() + timedelta(days=30))
        custo = c1.number_input("CUSTO", value=10.0)
        valor = c2.number_input("VALOR COBRADO", value=35.0)
        ini = c3.date_input("INÍCIOU DIA", value=datetime.now())
        whats = c1.text_input("WHATSAPP (DDD+Número)")
        obs = st.text_area("OBSERVAÇÃO")
        if st.form_submit_button("🚀 SALVAR CADASTRO"):
            if nome:
                conn = sqlite3.connect('supertv_gestao.db')
                conn.execute("INSERT INTO clientes (nome, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, inicio, whatsapp, observacao) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (nome, user, senha, serv, sist, venc.strftime('%Y-%m-%d'), custo, valor, ini.strftime('%Y-%m-%d'), whats, obs))
                conn.commit(); conn.close(); st.success("Cadastrado!"); st.rerun()

with tab3:
    st.subheader("🚨 Central de Cobrança")
    pix = "62.326.879/0001-13"
    if not df.empty:
        sel_todos = st.toggle("Selecionar Todos Manualmente")
        st.write("🎯 **Filtros Rápidos:**")
        f1, f2, f3, f4, f5 = st.columns(5)
        
        # Lógica de filtros
        st.session_state.filtro = st.session_state.get('filtro', 'Nenhum')
        if f1.button("❌ VENCIDOS"): st.session_state.filtro = "Vencidos"
        if f2.button("🟠 HOJE"): st.session_state.filtro = "Hoje"
        if f3.button("🟡 2 DIAS"): st.session_state.filtro = "2 Dias"
        if f4.button("🟡 3 DIAS"): st.session_state.filtro = "3 Dias"
        if f5.button("🔵 4+ DIAS"): st.session_state.filtro = "4 Mais"

        clientes_selecionados = []
        for idx, c in df.sort_values(by='dias_res').iterrows():
            auto = False
            if c['dias_res'] < 0: cls, st_t, auto = "row-vencido", "🔴 VENCIDO", (st.session_state.filtro == "Vencidos")
            elif c['dias_res'] == 0: cls, st_t, auto = "row-hoje", "🟠 HOJE", (st.session_state.filtro == "Hoje")
            elif c['dias_res'] == 2: cls, st_t, auto = "row-breve", "🟡 2 DIAS", (st.session_state.filtro == "2 Dias")
            elif c['dias_res'] == 3: cls, st_t, auto = "row-breve", "🟡 3 DIAS", (st.session_state.filtro == "3 Dias")
            elif c['dias_res'] >= 4: cls, st_t, auto = "row-em-dia", "🔵 EM DIA", (st.session_state.filtro == "4 Mais")
            else: cls, st_t, auto = "row-em-dia", "🟢 OK", False

            col_ch, col_ca = st.columns([0.1, 0.9])
            with col_ch:
                if st.checkbox("", value=(sel_todos or auto), key=f"cob_{c['id']}"):
                    clientes_selecionados.append(c)
            with col_ca:
                st.markdown(f'<div class="cliente-row {cls}"><b>{str(c["nome"]).upper()}</b> | {st_t} | Vence: {c["vencimento"]}</div>', unsafe_allow_html=True)

        if st.button(f"📲 DISPARAR COBRANÇA ({len(clientes_selecionados)})", use_container_width=True):
            for item in clientes_selecionados:
                msg = f"Olá {str(item['nome']).split()[0]}! 👋 Sua assinatura {item['servidor']} vence dia {item['vencimento']}. Pix: {pix}"
                st.link_button(f"WhatsApp {item['nome']}", f"https://wa.me/55{item['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Ajustes e Gerenciamento")
    
    # --- GERENCIAR SERVIDORES ---
    with st.expander("🔌 Adicionar / Gerenciar Servidores"):
        novo_serv = st.text_input("Nome do Servidor")
        if st.button("➕ Adicionar Servidor"):
            try:
                conn = sqlite3.connect('supertv_gestao.db')
                conn.execute("INSERT INTO lista_servidores (nome) VALUES (?)", (novo_serv.upper(),))
                conn.commit(); conn.close(); st.success("Servidor Adicionado!"); st.rerun()
            except: st.error("Servidor já existe.")
    
    # --- UPLOAD E BACKUP ---
    with st.expander("📥 Importar Listas (UPLOAD)"):
        file = st.file_uploader("Selecione o arquivo Excel", type=["xlsx"])
        if file and st.button("🚀 Iniciar Importação"):
            imp = pd.read_excel(file)
            conn = sqlite3.connect('supertv_gestao.db')
            imp.to_sql('clientes', conn, if_exists='append', index=False)
            conn.close(); st.success("Dados Importados!"); st.rerun()

    with st.expander("💾 Backup de Dados"):
        if st.button("📦 Gerar Backup em Excel"):
            df_back = pd.read_sql_query("SELECT * FROM clientes", sqlite3.connect('supertv_gestao.db'))
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_back.to_excel(writer, index=False)
            st.download_button("⬇️ Baixar Backup", output.getvalue(), "backup_supertv.xlsx")

    with st.expander("🔄 Reiniciar Sistema"):
        st.warning("Isso limpa a tela, mas NÃO apaga seus clientes.")
        if st.button("Reiniciar Agora"): st.rerun()

    if st.button("🗑️ APAGAR TUDO (CUIDADO!)", type="primary"):
        conn = sqlite3.connect('supertv_gestao.db')
        conn.execute("DELETE FROM clientes"); conn.commit(); conn.close(); st.rerun()
