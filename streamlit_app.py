import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- ESTILIZAÇÃO CSS AVANÇADA (SISTEMA DE DEGRADÊ TOTAL) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    
    /* Centralização das Logos */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 25px;
    }

    /* Cards de Métricas (Duplas) */
    .metric-card {
        background-color: #161b22;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #30363d;
        margin-bottom: 10px;
    }
    .metric-label { font-size: 11px; font-weight: bold; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 24px; font-weight: bold; color: #ff0000; margin-top: 5px; }
    
    /* 🔴 CORREÇÃO TOTAL: ESTILO DE TODOS OS BOTÕES E EXPANDERS 🔘 */
    /* Este bloco força o degradê em botões de formulário, botões normais e botões de download */
    div.stButton > button, 
    div.stDownloadButton > button, 
    div.stFormSubmitButton > button,
    [data-testid="stLinkButton"] > a {
        background: linear-gradient(135deg, #ff0000 0%, #e0e0e0 100%) !important;
        color: #000000 !important;
        font-weight: 800 !important;
        border-radius: 10px !important;
        border: 2px solid #ffffff44 !important;
        height: 50px !important;
        width: 100% !important;
        text-transform: uppercase !important;
        transition: 0.4s !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3) !important;
    }

    /* 🏷️ ESTILO DO NOME DO CLIENTE (EXPANDER) */
    .stExpander { border: none !important; margin-bottom: 12px !important; }
    .stExpander > details > summary {
        background: linear-gradient(135deg, #ff0000 0%, #e0e0e0 100%) !important;
        color: #000000 !important;
        font-weight: 800 !important;
        padding: 15px !important;
        border-radius: 12px !important;
        border: 2px solid #ffffff44 !important;
        list-style: none !important;
    }

    /* Efeito de Brilho ao passar o mouse */
    button:hover, summary:hover, a:hover {
        transform: scale(1.01) !important;
        filter: brightness(1.2) !important;
        box-shadow: 0px 0px 20px rgba(255, 0, 0, 0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento DATE, custo REAL, mensalidade REAL, observacao TEXT)''')
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

# --- HEADER (LOGOS CENTRALIZADAS) ---
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
col_a, col_b, col_c = st.columns([1, 4, 1])
with col_b:
    img_col1, img_col2 = st.columns(2)
    img_col1.image("https://i.imgur.com/CKq9BVx.png", use_container_width=True)
    img_col2.image("https://i.imgur.com/OkUAPQa.png", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- MÉTRICAS EM DUPLAS (LADO A LADO) ---
if not df.empty:
    hoje = datetime.now().date()
    df['venc_dt'] = pd.to_datetime(df['vencimento']).dt.date
    df['dias_res'] = (df['venc_dt'] - hoje).apply(lambda x: x.days)
    
    total, bruto, custos = len(df), df['mensalidade'].sum(), df['custo'].sum()
    em_dia = len(df[df['dias_res'] > 0])
    vencidos = len(df[df['dias_res'] < 0])
    vence_3d = len(df[(df['dias_res'] >= 0) & (df['dias_res'] <= 3)])

    m1, m2 = st.columns(2); m1.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL CLIENTES</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True); m2.markdown(f'<div class="metric-card"><div class="metric-label">EM DIA</div><div class="metric-value">{em_dia}</div></div>', unsafe_allow_html=True)
    m3, m4 = st.columns(2); m3.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value">{vencidos}</div></div>', unsafe_allow_html=True); m4.markdown(f'<div class="metric-card"><div class="metric-label">VENCE EM 3 DIAS</div><div class="metric-value">{vence_3d}</div></div>', unsafe_allow_html=True)
    m5, m6 = st.columns(2); m5.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO BRUTO</div><div class="metric-value">R$ {bruto:,.2f}</div></div>', unsafe_allow_html=True); m6.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO LÍQUIDO</div><div class="metric-value">R$ {bruto-custos:,.2f}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-card"><div class="metric-label">CUSTOS COM CRÉDITOS</div><div class="metric-value">R$ {custos:,.2f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- ABAS DE NAVEGAÇÃO ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 GESTÃO", "➕ CADASTRAR", "📢 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔍 FILTRAR POR NOME OU USER")
    if not df.empty:
        for _, r in df.iterrows():
            if busca.lower() in r['nome'].lower() or busca.lower() in str(r['usuario']).lower():
                # CABEÇALHO DO CLIENTE COM TODAS AS INFO NO BOTÃO DEGRADÊ
                info_header = f"👤 {r['nome'].upper()} | U: {r['usuario']} | S: {r['senha']} | ({r.get('sistema', 'IPTV')})"
                with st.expander(info_header):
                    with st.form(key=f"edit_{r['id']}"):
                        c1, c2 = st.columns(2)
                        n_nome = c1.text_input("Nome", value=r['nome'])
                        n_zap = c2.text_input("WhatsApp", value=r['whatsapp'])
                        
                        c3, c4 = st.columns(2)
                        n_user = c3.text_input("Usuário", value=r['usuario'])
                        n_pass = c4.text_input("Senha", value=r['senha'])
                        
                        srv_opcoes = get_servidores()
                        n_srv = st.selectbox("Servidor", srv_opcoes, index=srv_opcoes.index(r['servidor']) if r['servidor'] in srv_opcoes else 0)
                        
                        c5, c6, c7 = st.columns(3)
                        n_venc = c5.date_input("Vencimento", value=pd.to_datetime(r['vencimento']).date())
                        n_valor = c6.number_input("Valor R$", value=float(r['mensalidade']))
                        n_sis = c7.radio("Sistema", ["IPTV", "P2P"], index=0 if r.get('sistema') == "IPTV" else 1, horizontal=True)
                        
                        st.divider()
                        # BOTÕES DE AÇÃO INTERNA
                        b1, b2, b3 = st.columns(3)
                        if b1.form_submit_button("💾 SALVAR"):
                            c = sqlite3.connect('supertv_gestao.db'); c.execute("UPDATE clientes SET nome=?, whatsapp=?, usuario=?, senha=?, servidor=?, vencimento=?, mensalidade=?, sistema=? WHERE id=?", (n_nome, n_zap, n_user, n_pass, n_srv, str(n_venc), n_valor, n_sis, r['id'])); c.commit(); st.rerun()
                        if b2.form_submit_button("🔄 +30 DIAS"):
                            nova = pd.to_datetime(r['vencimento']).date() + timedelta(days=30)
                            c = sqlite3.connect('supertv_gestao.db'); c.execute("UPDATE clientes SET vencimento=? WHERE id=?", (str(nova), r['id'])); c.commit(); st.rerun()
                        if b3.form_submit_button("🗑️ EXCLUIR"):
                            c = sqlite3.connect('supertv_gestao.db'); c.execute("DELETE FROM clientes WHERE id=?", (r['id'],)); c.commit(); st.rerun()

with tab2:
    with st.form("novo_cadastro", clear_on_submit=True):
        st.subheader("🚀 Novo Cliente Supertv4k")
        f_nome = st.text_input("NOME COMPLETO")
        f_zap = st.text_input("WHATSAPP (DDD + NÚMERO)")
        c1, c2 = st.columns(2); f_user = c1.text_input("USUÁRIO"); f_pass = c2.text_input("SENHA")
        f_srv = st.selectbox("SELECIONE O SERVIDOR", get_servidores())
        f_venc = st.date_input("DATA DE VENCIMENTO", value=datetime.now() + timedelta(days=30))
        c3, c4, c5 = st.columns(3)
        f_custo = c3.number_input("CUSTO CRÉDITO", 0.0)
        f_valor = c4.number_input("VALOR COBRADO", 35.0)
        f_sis = c5.radio("SISTEMA", ["IPTV", "P2P"], horizontal=True)
        
        if st.form_submit_button("🚀 CADASTRAR AGORA"):
            c = sqlite3.connect('supertv_gestao.db')
            c.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, vencimento, custo, mensalidade, sistema) VALUES (?,?,?,?,?,?,?,?,?)", (f_nome, f_zap, f_user, f_pass, f_srv, str(f_venc), f_custo, f_valor, f_sis))
            c.commit(); st.success("Cliente Cadastrado com Sucesso!"); st.rerun()

with tab3:
    st.subheader("📢 Avisos de Cobrança")
    pix = "62.326.879/0001-13"
    if not df.empty:
        df_aviso = df[df['dias_res'] <= 3]
        for _, cl in df_aviso.iterrows():
            texto = f"Olá {cl['nome']}! 👋\nSua assinatura vence em breve. Renove para não ficar sem o sinal! 🚀\nValor: R$ {cl['mensalidade']}\nChave PIX: {pix}"
            st.link_button(f"📲 ENVIAR PARA: {cl['nome']}", f"https://wa.me/{cl['whatsapp']}?text={urllib.parse.quote(texto)}")

with tab4:
    st.subheader("⚙️ Painel de Configurações")
    add_s = st.text_input("Nome do Novo Servidor")
    if st.button("➕ ADICIONAR SERVIDOR"):
        if add_s:
            c = sqlite3.connect('supertv_gestao.db'); c.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (add_s,)); c.commit(); st.rerun()
    
    st.divider()
    if not df.empty:
        output = io.BytesIO()
        df.to_excel(output, index=False)
        st.download_button("📥 EXPORTAR BASE DE DADOS (EXCEL)", data=output.getvalue(), file_name="gestao_supertv_backup.xlsx")
