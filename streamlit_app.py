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
    
    /* Cores das linhas de cliente na cobrança */
    .cliente-row { border-radius: 12px; padding: 12px; margin-bottom: 10px; border: 1px solid #30363d; }
    .row-vencido { background-color: #331111; border-left: 8px solid #ff4b4b; }
    .row-hoje { background-color: #3d2b11; border-left: 8px solid #ffa500; }
    .row-breve { background-color: #333311; border-left: 8px solid #ffff00; }
    .row-em-dia { background-color: #112233; border-left: 8px solid #00d4ff; }
    
    .info-txt { font-size: 14px; color: #ffffff; margin-bottom: 2px; }
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 12px; text-align: center; border: 1px solid #30363d; }
    .metric-value { font-size: 20px; font-weight: bold; color: #ffffff; }
    
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
    div.stButton > button:hover { border-color: #00d4ff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    # Adicionando todos os campos solicitados
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, usuario TEXT, senha TEXT, 
                  servidor TEXT, sistema TEXT, vencimento TEXT, custo REAL, 
                  mensalidade REAL, inicio TEXT, whatsapp TEXT, observacao TEXT, logo_blob TEXT)''')
    conn.commit(); conn.close()

init_db()

# --- 4. CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- 5. DASHBOARD ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

if not df.empty:
    hoje = datetime.now().date()
    df['mensalidade'] = pd.to_numeric(df['mensalidade'], errors='coerce').fillna(0)
    df['custo'] = pd.to_numeric(df['custo'], errors='coerce').fillna(0)
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 0)

# --- 6. ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ NOVO CADASTRO", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔎 Pesquisar...", placeholder="Nome ou Usuário")
    if not df.empty:
        df_f = df[df['nome'].str.contains(busca, case=False, na=False) | df['usuario'].str.contains(busca, case=False, na=False)] if busca else df
        
        for _, r in df_f.sort_values(by='nome').iterrows():
            # BOTÃO COM AS INFORMAÇÕES QUE VOCÊ PEDIU
            label = f"👤 {str(r['nome']).upper()} | 🔑 {r['usuario']} | 🔓 {r['senha']} | 📶 {r['servidor']} | 🖥️ {r['sistema']} | 📅 {r['vencimento']}"
            
            if st.button(label, key=f"clie_{r['id']}"):
                with st.expander("📄 DADOS COMPLETOS DO CLIENTE", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Cliente:** {r['nome']}")
                    c1.write(f"**Usuário:** {r['usuario']}")
                    c1.write(f"**Senha:** {r['senha']}")
                    c2.write(f"**Servidor:** {r['servidor']}")
                    c2.write(f"**Sistema:** {r['sistema']}")
                    c2.write(f"**Vencimento:** {r['vencimento']}")
                    c3.write(f"**Custo:** R$ {r['custo']:.2f}")
                    c3.write(f"**Valor Cobrado:** R$ {r['mensalidade']:.2f}")
                    c3.write(f"**Início:** {r['inicio']}")
                    st.write(f"**WhatsApp:** {r['whatsapp']}")
                    st.info(f"**Observação:** {r['observacao']}")

with tab2:
    st.subheader("📝 Cadastrar Novo Cliente")
    with st.form("form_add"):
        col1, col2, col3 = st.columns(3)
        nome = col1.text_input("CLIENTE")
        user = col2.text_input("USUÁRIO")
        senha = col3.text_input("SENHA")
        
        serv = col1.text_input("SERVIDOR")
        sist = col2.text_input("SISTEMA")
        venc = col3.date_input("VENCIMENTO", value=datetime.now() + timedelta(days=30))
        
        custo = col1.number_input("CUSTO", value=10.0)
        valor = col2.number_input("VALOR COBRADO", value=35.0)
        ini = col3.date_input("INÍCIOU DIA", value=datetime.now())
        
        whats = col1.text_input("WHATSAPP (DDD+Número)")
        obs = st.text_area("OBSERVAÇÃO")
        
        if st.form_submit_button("🚀 SALVAR CADASTRO"):
            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("INSERT INTO clientes (nome, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, inicio, whatsapp, observacao) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (nome, user, senha, serv, sist, venc.strftime('%Y-%m-%d'), custo, valor, ini.strftime('%Y-%m-%d'), whats, obs))
            conn.commit(); conn.close(); st.success("Cliente cadastrado!"); st.rerun()

with tab3:
    st.subheader("🚨 Central de Cobrança")
    pix = "62.326.879/0001-13"
    
    if not df.empty:
        # BOTÕES DE FILTRO RÁPIDO
        st.write("🎯 **Filtros Rápidos de Seleção:**")
        f1, f2, f3, f4, f5 = st.columns(5)
        
        # Variáveis de controle de seleção
        sel_type = "Nenhum"
        if f1.button("❌ VENCIDOS"): sel_type = "Vencidos"
        if f2.button("🟠 HOJE"): sel_type = "Hoje"
        if f3.button("🟡 2 DIAS"): sel_type = "2 Dias"
        if f4.button("🟡 3 DIAS"): sel_type = "3 Dias"
        if f5.button("🔵 4+ DIAS"): sel_type = "4 Mais"
        
        sel_todos = st.toggle("Selecionar Todos Manualmente")
        
        clientes_selecionados = []
        
        for idx, c in df.sort_values(by='dias_res').iterrows():
            # Lógica das Cores
            if c['dias_res'] < 0: cls, status, auto_sel = "row-vencido", "🔴 VENCIDO", (sel_type == "Vencidos")
            elif c['dias_res'] == 0: cls, status, auto_sel = "row-hoje", "🟠 HOJE", (sel_type == "Hoje")
            elif c['dias_res'] == 2: cls, status, auto_sel = "row-breve", "🟡 2 DIAS", (sel_type == "2 Dias")
            elif c['dias_res'] == 3: cls, status, auto_sel = "row-breve", "🟡 3 DIAS", (sel_type == "3 Dias")
            elif c['dias_res'] >= 4: cls, status, auto_sel = "row-em-dia", "🔵 EM DIA", (sel_type == "4 Mais")
            else: cls, status, auto_sel = "row-em-dia", "🟢 OK", False

            col_ch, col_ca = st.columns([0.1, 0.9])
            with col_ch:
                # O checkbox marca se o toggle geral estiver on OU se o filtro rápido for clicado
                pode_marcar = sel_todos or auto_sel
                if st.checkbox("", value=pode_marcar, key=f"cb_cob_{idx}"):
                    clientes_selecionados.append(c)
            
            with col_ca:
                st.markdown(f'<div class="cliente-row {cls}"><b>{str(c["nome"]).upper()}</b> | {status} | Vence: {c["vencimento"]}</div>', unsafe_allow_html=True)

        if st.button(f"📲 ENVIAR COBRANÇA PARA {len(clientes_selecionados)} SELECIONADOS", use_container_width=True):
            for item in clientes_selecionados:
                msg = f"Olá {str(item['nome']).split()[0]}! 👋 Sua assinatura {item['servidor']} vence em {item['vencimento']}. Pix: {pix}"
                st.link_button(f"WhatsApp: {item['nome']}", f"https://wa.me/55{item['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Ajustes")
    if st.button("🗑️ LIMPAR BANCO (Cuidado!)"):
        conn = sqlite3.connect('supertv_gestao.db')
        conn.execute("DELETE FROM clientes"); conn.commit(); conn.close(); st.rerun()
