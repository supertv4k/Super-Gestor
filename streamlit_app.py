import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS (DESIGN METALIZADO E SOMBRAS) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 25px;
    }

    .metric-card {
        background-color: #161b22;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #30363d;
        margin-bottom: 10px;
    }
    .metric-label { font-size: 11px; font-weight: bold; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 22px; font-weight: bold; color: #ff0000; margin-top: 5px; }
    
    /* BOTÕES GERAIS */
    div.stButton > button, 
    div.stDownloadButton > button, 
    div.stFormSubmitButton > button,
    [data-testid="stLinkButton"] > a {
        background: linear-gradient(135deg, #ff0000 0%, #c0c0c0 100%) !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        font-size: 16px !important;
        border-radius: 10px !important;
        border: 2px solid #ffffff44 !important;
        height: 50px !important;
        width: 100% !important;
        text-transform: uppercase !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.7) !important;
    }

    /* ESTILO DO BOTÃO DO CLIENTE (EXPANDER) */
    .stExpander { border: none !important; margin-bottom: 10px !important; }
    .stExpander > details > summary {
        background: linear-gradient(135deg, #ff0000 0%, #c0c0c0 100%) !important;
        color: #ffffff !important;
        padding: 15px !important;
        border-radius: 10px !important;
        border: 1px solid #ffffff44 !important;
        font-weight: 800 !important;
        font-size: 20px !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.6) !important;
    }

    .client-detail-card {
        background: #1c2128;
        padding: 20px;
        border-radius: 10px;
        border-left: 8px solid #ff0000;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento DATE, custo REAL, mensalidade REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    conn.commit()
    conn.close()

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    conn.close()
    return lista if lista else ["UNIPlAY", "MUNDOGF", "P2BRAZ"]

init_db()

# --- 4. HEADER ---
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 4, 1])
with c2:
    l1, l2 = st.columns(2)
    l1.image("https://i.imgur.com/CKq9BVx.png", use_container_width=True)
    l2.image("https://i.imgur.com/OkUAPQa.png", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 5. CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- 6. PAINEL DE MÉTRICAS COMPLETO ---
if not df.empty:
    hoje = datetime.now().date()
    df['venc_dt'] = pd.to_datetime(df['vencimento']).dt.date
    df['dias_res'] = (df['venc_dt'] - hoje).apply(lambda x: x.days)
    
    total = len(df)
    bruto = df['mensalidade'].sum()
    custos = df['custo'].sum()
    liquido = bruto - custos
    vencidos = len(df[df['dias_res'] < 0])
    vence_3d = len(df[(df['dias_res'] >= 0) & (df['dias_res'] <= 3)])
    em_dia = len(df[df['dias_res'] >= 0])

    m1, m2 = st.columns(2)
    m1.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL DE CLIENTES</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">CLIENTES EM DIA</div><div class="metric-value">{em_dia}</div></div>', unsafe_allow_html=True)
    
    m3, m4 = st.columns(2)
    m3.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value">{vencidos}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-label">VENCE EM 3 DIAS</div><div class="metric-value">{vence_3d}</div></div>', unsafe_allow_html=True)
    
    m5, m6 = st.columns(2)
    m5.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO BRUTO</div><div class="metric-value">R$ {bruto:,.2f}</div></div>', unsafe_allow_html=True)
    m6.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO LÍQUIDO</div><div class="metric-value">R$ {liquido:,.2f}</div></div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="metric-card"><div class="metric-label">CUSTOS COM CRÉDITOS</div><div class="metric-value">R$ {custos:,.2f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 7. ABAS ---
t1, t2, t3, t4 = st.tabs(["👤 GESTÃO", "➕ NOVO", "📢 COBRANÇA", "⚙️ AJUSTES"])

with t1:
    busca = st.text_input("🔍 PESQUISAR NOME OU USUÁRIO")
    if not df.empty:
        for _, r in df.iterrows():
            if busca.lower() in r['nome'].lower() or busca.lower() in str(r['usuario']).lower():
                titulo_botoes = f"👤 {r['nome'].upper()} / {r['usuario']} / {r['senha']}"
                with st.expander(titulo_botoes):
                    st.markdown(f"""
                        <div class="client-detail-card">
                            <div style="font-size: 28px; font-weight: 900; color: white; text-shadow: 2px 2px 4px black;">
                                {r['nome'].upper()} <br>
                                <span style="font-size: 22px;">{r['usuario']} / {r['senha']}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    with st.form(key=f"ed_{r['id']}"):
                        c1, c2 = st.columns(2)
                        en, ew = c1.text_input("Nome", value=r['nome']), c2.text_input("WhatsApp", value=r['whatsapp'])
                        c3, c4 = st.columns(2)
                        eu, es = c3.text_input("Usuário", value=r['usuario']), c4.text_input("Senha", value=r['senha'])
                        srvs = get_servidores()
                        esrv = st.selectbox("Servidor", srvs, index=srvs.index(r['servidor']) if r['servidor'] in srvs else 0)
                        c5, c6, c7 = st.columns(3)
                        ev = c5.date_input("Vencimento", value=pd.to_datetime(r['vencimento']).date())
                        em = c6.number_input("Valor", value=float(r['mensalidade']))
                        esis = c7.radio("Sistema", ["IPTV", "P2P"], index=0 if r.get('sistema') == "IPTV" else 1, horizontal=True)
                        st.divider()
                        b1, b2, b3 = st.columns(3)
                        if b1.form_submit_button("💾 SALVAR"):
                            c = sqlite3.connect('supertv_gestao.db'); c.execute("UPDATE clientes SET nome=?, whatsapp=?, usuario=?, senha=?, servidor=?, vencimento=?, mensalidade=?, sistema=? WHERE id=?", (en, ew, eu, es, esrv, str(ev), em, esis, r['id'])); c.commit(); st.rerun()
                        if b2.form_submit_button("🔄 +30 DIAS"):
                            nova = pd.to_datetime(r['vencimento']).date() + timedelta(days=30)
                            c = sqlite3.connect('supertv_gestao.db'); c.execute("UPDATE clientes SET vencimento=? WHERE id=?", (str(nova), r['id'])); c.commit(); st.rerun()
                        if b3.form_submit_button("🗑️ EXCLUIR"):
                            c = sqlite3.connect('supertv_gestao.db'); c.execute("DELETE FROM clientes WHERE id=?", (r['id'],)); c.commit(); st.rerun()

with t2:
    with st.form("new"):
        st.subheader("🚀 Cadastro Individual")
        f1, f2 = st.columns(2); n = f1.text_input("NOME"); w = f2.text_input("WHATSAPP")
        f3, f4 = st.columns(2); u = f3.text_input("USER"); s = f4.text_input("SENHA")
        srv = st.selectbox("SERVIDOR", get_servidores())
        v = st.date_input("VENCIMENTO", value=datetime.now() + timedelta(days=30))
        f5, f6 = st.columns(2); cu = f5.number_input("CUSTO", 0.0); me = f6.number_input("VALOR", 35.0)
        si = st.radio("SISTEMA", ["IPTV", "P2P"], horizontal=True)
        if st.form_submit_button("🚀 CADASTRAR"):
            c = sqlite3.connect('supertv_gestao.db'); c.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, vencimento, custo, mensalidade, sistema) VALUES (?,?,?,?,?,?,?,?,?)", (n, w, u, s, srv, str(v), cu, me, si)); c.commit(); st.rerun()

with t3:
    st.subheader("📢 Central de Cobrança Inteligente")
    pix = "62.326.879/0001-13"
    
    if not df.empty:
        # Filtra quem vence em até 3 dias ou já venceu
        df_aviso = df[df['dias_res'] <= 3].copy()
        
        if not df_aviso.empty:
            # Botão Selecionar Todos
            col_sel, col_limp = st.columns(2)
            if col_sel.button("✅ SELECIONAR TODOS"):
                st.session_state.selecionados = df_aviso['id'].tolist()
            if col_limp.button("❌ LIMPAR SELEÇÃO"):
                st.session_state.selecionados = []

            if 'selecionados' not in st.session_state:
                st.session_state.selecionados = []

            st.write(f"Clientes pendentes: {len(df_aviso)}")
            
            # Lista de Checkboxes
            selecionados_atualizados = []
            for _, cl in df_aviso.iterrows():
                checked = cl['id'] in st.session_state.selecionados
                if st.checkbox(f"Pagar: {cl['nome']} (Vence: {cl['vencimento']})", value=checked, key=f"check_{cl['id']}"):
                    selecionados_atualizados.append(cl['id'])
            
            st.session_state.selecionados = selecionados_atualizados

            st.divider()
            
            # Gerar botões apenas para os selecionados
            if st.session_state.selecionados:
                st.write("### 📲 Enviar Avisos")
                for sel_id in st.session_state.selecionados:
                    cliente = df_aviso[df_aviso['id'] == sel_id].iloc[0]
                    msg = f"Olá {cliente['nome']}! Sua assinatura Supertv4k vence em breve. Renove via PIX: {pix}"
                    st.link_button(f"ENVIAR PARA {cliente['nome']}", f"https://wa.me/{cliente['whatsapp']}?text={urllib.parse.quote(msg)}")
        else:
            st.success("Nenhum cliente vencendo nos próximos 3 dias!")

with t4:
    st.subheader("⚙️ Configurações e Backup")
    
    st.markdown("### 📥 Importar Lista (Excel)")
    file_up = st.file_uploader("Selecione o arquivo Excel", type=["xlsx"])
    if file_up:
        if st.button("🚀 PROCESSAR UPLOAD"):
            data_up = pd.read_excel(file_up)
            conn = sqlite3.connect('supertv_gestao.db')
            data_up.to_sql('clientes', conn, if_exists='append', index=False)
            conn.close()
            st.success("Lista importada com sucesso!")
            st.rerun()

    st.divider()
    
    st.markdown("### 📤 Exportar Lista (Excel)")
    if not df.empty:
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False)
        st.download_button(label="📥 BAIXAR BACKUP AGORA", data=towrite.getvalue(), file_name="backup_supertv4k.xlsx")

    st.divider()
    
    ns = st.text_input("Novo Servidor")
    if st.button("➕ ADICIONAR SERVIDOR"):
        if ns:
            c = sqlite3.connect('supertv_gestao.db'); c.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (ns,)); c.commit(); st.rerun()
