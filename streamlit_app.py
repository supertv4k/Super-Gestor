import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS (DESIGN METALIZADO) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 380px; margin-bottom: -20px !important; }
    .logo-supertv { width: 160px; }
    
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
    
    div.stButton > button, div.stDownloadButton > button, div.stFormSubmitButton > button, [data-testid="stLinkButton"] > a {
        background: linear-gradient(135deg, #ff0000 0%, #c0c0c0 100%) !important;
        color: #ffffff !important; font-weight: 900 !important; font-size: 16px !important;
        border-radius: 10px !important; border: 2px solid #ffffff44 !important;
        height: 50px !important; width: 100% !important; text-transform: uppercase !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.7) !important;
    }
    .stExpander > details > summary { 
        background: linear-gradient(135deg, #ff0000 0%, #c0c0c0 100%) !important; 
        color: #ffffff !important; padding: 15px !important; border-radius: 10px !important; 
        font-weight: 800 !important; font-size: 20px !important; 
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
    conn.commit(); conn.close()

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    conn.close()
    return lista if lista else ["UNIPlAY", "MUNDOGF", "P2BRAZ"]

init_db()

# --- 4. CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

if 'selecionados' not in st.session_state: st.session_state.selecionados = []

# --- 5. HEADER (LOGOS) ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

# --- 6. PAINEL DE MÉTRICAS COMPLETO ---
if not df.empty:
    hoje = datetime.now().date()
    df['venc_dt'] = pd.to_datetime(df['vencimento']).dt.date
    df['dias_res'] = (df['venc_dt'] - hoje).apply(lambda x: x.days)
    
    bruto = df['mensalidade'].sum()
    custos = df['custo'].sum()
    liquido = bruto - custos

    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL CLIENTES</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value">{len(df[df["dias_res"] < 0])}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">VENCEM EM 3 DIAS</div><div class="metric-value">{len(df[(df["dias_res"] >= 0) & (df["dias_res"] <= 3)])}</div></div>', unsafe_allow_html=True)
    
    c4, c5, c6 = st.columns(3)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO BRUTO</div><div class="metric-value">R$ {bruto:,.2f}</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO LÍQUIDO</div><div class="metric-value">R$ {liquido:,.2f}</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="metric-card"><div class="metric-label">CUSTO CRÉDITOS</div><div class="metric-value">R$ {custos:,.2f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 7. SISTEMA DE ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 GESTÃO", "➕ NOVO", "📢 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔍 PESQUISAR POR NOME OU USUÁRIO")
    if not df.empty:
        for _, r in df.iterrows():
            if busca.lower() in r['nome'].lower() or busca.lower() in str(r['usuario']).lower():
                with st.expander(f"👤 {r['nome'].upper()} / {r['usuario']}"):
                    with st.form(key=f"ed_{r['id']}"):
                        col1, col2 = st.columns(2)
                        en = col1.text_input("Nome", value=r['nome'])
                        ew = col2.text_input("WhatsApp", value=r['whatsapp'])
                        eu = col1.text_input("Usuário", value=r['usuario'])
                        es = col2.text_input("Senha", value=r['senha'])
                        srvs = get_servidores()
                        esrv = st.selectbox("Servidor", srvs, index=srvs.index(r['servidor']) if r['servidor'] in srvs else 0)
                        ev = st.date_input("Vencimento", value=pd.to_datetime(r['vencimento']).date())
                        em = st.number_input("Valor", value=float(r['mensalidade']))
                        if st.form_submit_button("💾 SALVAR"):
                            c = sqlite3.connect('supertv_gestao.db'); c.execute("UPDATE clientes SET nome=?, whatsapp=?, usuario=?, senha=?, servidor=?, vencimento=?, mensalidade=? WHERE id=?", (en, ew, eu, es, esrv, str(ev), em, r['id'])); c.commit(); st.rerun()

with tab2:
    st.subheader("🚀 Cadastro de Novo Cliente")
    with st.form("form_novo", clear_on_submit=True):
        f1, f2 = st.columns(2)
        n_n = f1.text_input("NOME COMPLETO")
        w_n = f2.text_input("WHATSAPP")
        u_n = f1.text_input("USUÁRIO")
        s_n = f2.text_input("SENHA")
        srv_n = st.selectbox("SERVIDOR", get_servidores())
        v_n = st.date_input("VENCIMENTO", value=datetime.now() + timedelta(days=30))
        f3, f4 = st.columns(2)
        c_n = f3.number_input("CUSTO", value=0.0)
        m_n = f4.number_input("VALOR MENSALIDADE", value=35.0)
        
        if st.form_submit_button("🚀 CADASTRAR CLIENTE"):
            if n_n and u_n:
                conn = sqlite3.connect('supertv_gestao.db')
                conn.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, vencimento, custo, mensalidade) VALUES (?,?,?,?,?,?,?,?)", (n_n, w_n, u_n, s_n, srv_n, str(v_n), c_n, m_n))
                conn.commit(); conn.close()
                st.success("Cadastrado! Voltando para Gestão...")
                st.rerun()
            else:
                st.error("Preencha Nome e Usuário!")

with tab3:
    st.subheader("📢 Central de Cobrança")
    pix_chave = "62.326.879/0001-13"
    if not df.empty:
        df_aviso = df[df['dias_res'] <= 3].copy()
        c_s, c_l = st.columns(2)
        if c_s.button("✅ SELECIONAR TODOS"): st.session_state.selecionados = df_aviso['id'].tolist(); st.rerun()
        if c_l.button("❌ LIMPAR SELEÇÃO"): st.session_state.selecionados = []; st.rerun()
        
        for _, cl in df_aviso.iterrows():
            dias = cl['dias_res']
            status = "VENCE HOJE" if dias == 0 else (f"VENCE EM {dias} DIAS" if dias > 0 else f"VENCIDO HÁ {abs(dias)} DIAS")
            data_formatada = pd.to_datetime(cl['vencimento']).strftime('%d/%m/%Y')
            
            # Label atualizado com Nome, Data e Status de dias
            label = f"🔔 {cl['nome']} | Vencimento: {data_formatada} ({status})"
            
            check = st.checkbox(label, value=(cl['id'] in st.session_state.selecionados), key=f"cob_{cl['id']}")
            if check and cl['id'] not in st.session_state.selecionados: st.session_state.selecionados.append(cl['id'])
            elif not check and cl['id'] in st.session_state.selecionados: st.session_state.selecionados.remove(cl['id'])
        
        if st.session_state.selecionados:
            st.divider()
            for sid in st.session_state.selecionados:
                cli = df[df['id'] == sid].iloc[0]
                msg = f"Olá {cli['nome']}! Sua assinatura Supertv4k vence em breve ({pd.to_datetime(cli['vencimento']).strftime('%d/%m/%Y')}). Renove via Pix: {pix_chave}"
                st.link_button(f"ENVIAR PARA {cli['nome']}", f"https://wa.me/{cli['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Ajustes e Backup")
    st.markdown("### ➕ Servidores")
    ns = st.text_input("Novo Servidor")
    if st.button("ADICIONAR SERVIDOR"):
        if ns:
            c = sqlite3.connect('supertv_gestao.db'); c.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (ns,)); c.commit(); st.rerun()
    st.divider()
    st.markdown("### 💾 Gerenciar Dados")
    col_up, col_down = st.columns(2)
    with col_up:
        st.write("📥 **Importar Excel**")
        f_up = st.file_uploader("Arquivo .xlsx", type=["xlsx"])
        if f_up and st.button("PROCESSAR UPLOAD"):
            pd.read_excel(f_up).to_sql('clientes', sqlite3.connect('supertv_gestao.db'), if_exists='append', index=False)
            st.success("Importado!"); st.rerun()
    with col_down:
        st.write("📤 **Baixar Backup**")
        if not df.empty:
            tow = io.BytesIO(); df.to_excel(tow, index=False)
            st.download_button(label="📥 DOWNLOAD EXCEL", data=tow.getvalue(), file_name="backup_supertv4k.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
