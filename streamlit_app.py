import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide", page_icon="🚀")

# --- 2. ESTILIZAÇÃO CSS (Otimizada) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 400px; margin-bottom: -10px !important; }
    
    .metric-card { 
        background-color: #161b22; padding: 20px; border-radius: 12px; 
        text-align: center; border: 1px solid #30363d;
    }
    .metric-label { font-size: 12px; font-weight: bold; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 26px; font-weight: bold; color: #ff0000; margin-top: 5px; }

    /* Estilo dos Expanders */
    .stExpander { border: 1px solid #30363d !important; background-color: #0d1117 !important; margin-bottom: 10px; }
    
    /* Botão Salvar Customizado */
    div.stFormSubmitButton > button:first-child {
        width: 100%;
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%) !important;
        color: white !important; border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE BANCO DE DADOS ---
DB_NAME = 'supertv_gestao.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                      usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                      vencimento DATE, custo REAL, mensalidade REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
        # Seed inicial de servidores se estiver vazio
        c.execute("SELECT count(*) FROM lista_servidores")
        if c.fetchone()[0] == 0:
            servidores = [("UNITV",), ("MUNDOGF",), ("P2BRAZ",), ("UNIPLAY",)]
            c.executemany("INSERT INTO lista_servidores (nome) VALUES (?)", servidores)
        conn.commit()

def get_servidores():
    with sqlite3.connect(DB_NAME) as conn:
        df_srv = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)
    return df_srv['nome'].tolist()

init_db()

# --- 4. LÓGICA DE DADOS ---
def carregar_dados():
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query("SELECT * FROM clientes", conn)

df = carregar_dados()
if not df.empty:
    df['vencimento'] = pd.to_datetime(df['vencimento'])
    hoje = datetime.now().date()
    df['dias_res'] = (df['vencimento'].dt.date - hoje).apply(lambda x: x.days)

# --- 5. HEADER ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"></div>""", unsafe_allow_html=True)

# --- 6. DASHBOARD DE MÉTRICAS ---
if not df.empty:
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">Clientes Ativos</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    
    vencidos = len(df[df["dias_res"] < 0])
    c2.markdown(f'<div class="metric-card"><div class="metric-label">Vencidos</div><div class="metric-value" style="color:#ff4b4b">{vencidos}</div></div>', unsafe_allow_html=True)
    
    alerta = len(df[(df["dias_res"] >= 0) & (df["dias_res"] <= 3)])
    c3.markdown(f'<div class="metric-card"><div class="metric-label">Vencem em 3 dias</div><div class="metric-value" style="color:#f1c40f">{alerta}</div></div>', unsafe_allow_html=True)
    
    lucro = df['mensalidade'].sum() - df['custo'].sum()
    c4.markdown(f'<div class="metric-card"><div class="metric-label">Lucro Líquido Est.</div><div class="metric-value" style="color:#2ecc71">R$ {lucro:,.2f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 7. ABAS PRINCIPAIS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 GESTÃO DE CLIENTES", "➕ NOVO CADASTRO", "🚨 CENTRAL DE COBRANÇA", "⚙️ CONFIGURAÇÕES"])

with tab1:
    col_busca, col_filtro = st.columns([3, 1])
    busca = col_busca.text_input("🔍 Buscar por nome ou usuário", placeholder="Ex: João Silva")
    filtro_status = col_filtro.selectbox("Filtro", ["Todos", "Vencidos", "Ativos"])

    if not df.empty:
        # Lógica de Filtro
        df_view = df.copy()
        if busca:
            df_view = df_view[df_view['nome'].str.contains(busca, case=False) | df_view['usuario'].str.contains(busca, case=False)]
        if filtro_status == "Vencidos":
            df_view = df_view[df_view['dias_res'] < 0]
        elif filtro_status == "Ativos":
            df_view = df_view[df_view['dias_res'] >= 0]

        for _, r in df_view.iterrows():
            cor_dias = "#ff4b4b" if r['dias_res'] < 0 else "#2ecc71"
            label = f"{r['nome'].upper()} | 📡 {r['servidor']} | 📅 {r['vencimento'].strftime('%d/%m/%Y')} ({r['dias_res']} dias)"
            
            with st.expander(label):
                with st.form(key=f"ed_{r['id']}"):
                    f_c1, f_c2, f_c3 = st.columns([2, 2, 1])
                    en = f_c1.text_input("Nome", value=r['nome'])
                    ew = f_c2.text_input("WhatsApp (com DDD)", value=r['whatsapp'])
                    eu = f_c1.text_input("Usuário", value=r['usuario'])
                    es = f_c2.text_input("Senha", value=r['senha'])
                    
                    srvs = get_servidores()
                    esrv = f_c3.selectbox("Servidor", srvs, index=srvs.index(r['servidor']) if r['servidor'] in srvs else 0)
                    
                    f_c4, f_c5, f_c6 = st.columns(3)
                    ev = f_c4.date_input("Vencimento", value=r['vencimento'].date())
                    ec = f_c5.number_input("Custo", value=float(r['custo']))
                    em = f_c6.number_input("Mensalidade", value=float(r['mensalidade']))
                    
                    col_btn1, col_btn2, col_btn3 = st.columns([1,1,2])
                    if col_btn1.form_submit_button("💾 Atualizar"):
                        with sqlite3.connect(DB_NAME) as conn:
                            conn.execute("UPDATE clientes SET nome=?, whatsapp=?, usuario=?, senha=?, servidor=?, vencimento=?, custo=?, mensalidade=? WHERE id=?", 
                                         (en, ew, eu, es, esrv, str(ev), ec, em, r['id']))
                        st.success("Dados atualizados!")
                        st.rerun()
                    
                    if col_btn2.form_submit_button("🗑️ Excluir"):
                        with sqlite3.connect(DB_NAME) as conn:
                            conn.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                        st.rerun()

with tab2:
    st.subheader("🚀 Novo Assinante")
    with st.form("form_novo", clear_on_submit=True):
        f1, f2 = st.columns(2)
        n_n = f1.text_input("Nome do Cliente*")
        w_n = f2.text_input("WhatsApp (Ex: 11999999999)")
        u_n = f1.text_input("Usuário/Login*")
        s_n = f2.text_input("Senha")
        
        srv_n = st.selectbox("Servidor Responsável", get_servidores())
        v_n = st.date_input("Data de Vencimento", value=datetime.now() + timedelta(days=30))
        
        f3, f4 = st.columns(2)
        c_n = f3.number_input("Preço de Custo (Crédito)", value=10.0)
        m_n = f4.number_input("Preço de Venda (Mensalidade)", value=35.0)
        
        if st.form_submit_button("🚀 CADASTRAR CLIENTE"):
            if n_n and u_n:
                with sqlite3.connect(DB_NAME) as conn:
                    conn.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, vencimento, custo, mensalidade) VALUES (?,?,?,?,?,?,?,?)", 
                                 (n_n, w_n, u_n, s_n, srv_n, str(v_n), c_n, m_n))
                st.success(f"Cliente {n_n} cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("Nome e Usuário são obrigatórios!")

with tab3:
    st.subheader("🚨 Central de Avisos")
    pix_chave = "62.326.879/0001-13" # Sua chave pix
    
    if not df.empty:
        # Filtra quem vence em breve ou já venceu
        df_cobranca = df[df['dias_res'] <= 5].sort_values(by='dias_res')
        
        if df_cobranca.empty:
            st.info("Nenhum cliente com vencimento próximo (5 dias).")
        else:
            for _, cli in df_cobranca.iterrows():
                col_info, col_btn = st.columns([3, 1])
                
                status_txt = "🔴 VENCIDO" if cli['dias_res'] < 0 else "🟡 VENCE EM BREVE"
                info = f"**{cli['nome']}** ({status_txt}) - Venceu/Vence em: {cli['vencimento'].strftime('%d/%m/%Y')}"
                col_info.write(info)
                
                # Gerador de link WhatsApp
                msg = f"Olá *{cli['nome']}*! 👋\n\nSua assinatura *Supertv4k* vence dia *{cli['vencimento'].strftime('%d/%m/%Y')}*.\n\nPara não ficar sem o sinal, realize o pagamento de *R$ {cli['mensalidade']:.2f}*.\n\n📌 *Chave PIX:* `{pix_chave}`\n\nApós o pagamento, envie o comprovante!"
                link_wa = f"https://wa.me/55{cli['whatsapp']}?text={urllib.parse.quote(msg)}"
                col_btn.link_button("📲 Enviar Cobrança", link_wa)

with tab4:
    st.subheader("⚙️ Configurações do Sistema")
    
    with st.expander("☁️ Backup e Dados"):
        c1, c2 = st.columns(2)
        tow = io.BytesIO()
        df.to_excel(tow, index=False)
        c1.download_button("📥 Baixar Backup Excel", data=tow.getvalue(), file_name=f"backup_supertv_{datetime.now().strftime('%d_%m_%Y')}.xlsx")
        
    with st.expander("📡 Gerenciar Servidores"):
        novo_srv = st.text_input("Nome do Novo Servidor")
        if st.button("Adicionar Servidor"):
            if novo_srv:
                with sqlite3.connect(DB_NAME) as conn:
                    conn.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (novo_srv.upper(),))
                st.rerun()
