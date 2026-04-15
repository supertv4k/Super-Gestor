import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    
    /* Logos: Gestão em cima (maior) e Supertv4k embaixo (menor) */
    .header-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        margin-bottom: 30px;
    }
    .logo-gestao {
        width: 380px; 
        margin-bottom: -20px !important;
    }
    .logo-supertv {
        width: 160px;
    }

    /* Cartões de Métricas */
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
    
    /* Botões Metalizados */
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

    .client-detail-card { background: #1c2128; padding: 20px; border-radius: 10px; border-left: 8px solid #ff0000; margin-bottom: 20px; }
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

# --- 4. CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

if 'selecionados' not in st.session_state:
    st.session_state.selecionados = []

# --- 5. HEADER (CORRIGIDO: GESTÃO EM CIMA) ---
st.markdown("""
    <div class="header-container">
        <img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao">
        <img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv">
    </div>
""", unsafe_allow_html=True)

# --- 6. PAINEL DE MÉTRICAS COMPLETO ---
if not df.empty:
    hoje = datetime.now().date()
    df['venc_dt'] = pd.to_datetime(df['vencimento']).dt.date
    df['dias_res'] = (df['venc_dt'] - hoje).apply(lambda x: x.days)
    
    m1, m2, m3 = st.columns(3)
    m1.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL CLIENTES</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value">{len(df[df["dias_res"] < 0])}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-label">VENCEM EM 3 DIAS</div><div class="metric-value">{len(df[(df["dias_res"] >= 0) & (df["dias_res"] <= 3)])}</div></div>', unsafe_allow_html=True)
    
    m4, m5, m6 = st.columns(3)
    m4.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO BRUTO</div><div class="metric-value">R$ {df["mensalidade"].sum():,.2f}</div></div>', unsafe_allow_html=True)
    m5.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO LÍQUIDO</div><div class="metric-value">R$ {df["mensalidade"].sum() - df["custo"].sum():,.2f}</div></div>', unsafe_allow_html=True)
    m6.markdown(f'<div class="metric-card"><div class="metric-label">CUSTO CRÉDITOS</div><div class="metric-value">R$ {df["custo"].sum():,.2f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 7. ABAS ---
t1, t2, t3, t4 = st.tabs(["👤 GESTÃO", "➕ NOVO", "📢 COBRANÇA", "⚙️ AJUSTES"])

with t1:
    busca = st.text_input("🔍 PESQUISAR POR NOME OU USUÁRIO")
    if not df.empty:
        for _, r in df.iterrows():
            if busca.lower() in r['nome'].lower() or busca.lower() in str(r['usuario']).lower():
                titulo = f"👤 {r['nome'].upper()} / {r['usuario']} / {r['senha']}"
                with st.expander(titulo):
                    st.markdown(f'<div class="client-detail-card"><div style="font-size: 26px; font-weight: 900;">{r["nome"].upper()}</div><div style="font-size: 20px;">{r["usuario"]} / {r["senha"]}</div></div>', unsafe_allow_html=True)
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
                        if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                            c = sqlite3.connect('supertv_gestao.db'); c.execute("UPDATE clientes SET nome=?, whatsapp=?, usuario=?, senha=?, servidor=?, vencimento=?, mensalidade=?, sistema=? WHERE id=?", (en, ew, eu, es, esrv, str(ev), em, esis, r['id'])); c.commit(); st.rerun()

with t2:
    st.subheader("🚀 Cadastro de Novo Cliente")
    with st.form("novo_cliente_form"):
        f1, f2 = st.columns(2)
        nome_n = f1.text_input("NOME COMPLETO")
        whats_n = f2.text_input("WHATSAPP (COM DDD)")
        f3, f4 = st.columns(2)
        user_n = f3.text_input("USUÁRIO")
        pass_n = f4.text_input("SENHA")
        srv_n = st.selectbox("SERVIDOR", get_servidores())
        venc_n = st.date_input("DATA DE VENCIMENTO", value=datetime.now() + timedelta(days=30))
        f5, f6 = st.columns(2)
        custo_n = f5.number_input("CUSTO DO CRÉDITO", min_value=0.0, value=0.0)
        valor_n = f6.number_input("VALOR DA MENSALIDADE", min_value=0.0, value=35.0)
        sistema_n = st.radio("SISTEMA", ["IPTV", "P2P"], horizontal=True)
        
        if st.form_submit_button("🚀 CADASTRAR CLIENTE"):
            if nome_n and user_n:
                c = sqlite3.connect('supertv_gestao.db')
                c.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, vencimento, custo, mensalidade, sistema) VALUES (?,?,?,?,?,?,?,?,?)", 
                          (nome_n, whats_n, user_n, pass_n, srv_n, str(venc_n), custo_n, valor_n, sistema_n))
                c.commit()
                st.success(f"Cliente {nome_n} cadastrado!")
                st.rerun()
            else:
                st.error("Preencha Nome e Usuário!")

with t3:
    st.subheader("📢 Central de Cobrança")
    pix_chave = "62.326.879/0001-13"
    if not df.empty:
        df_aviso = df[df['dias_res'] <= 3].copy()
        c_sel, c_limp = st.columns(2)
        if c_sel.button("✅ SELECIONAR TODOS"):
            st.session_state.selecionados = df_aviso['id'].tolist(); st.rerun()
        if c_limp.button("❌ LIMPAR SELEÇÃO"):
            st.session_state.selecionados = []; st.rerun()

        for _, cl in df_aviso.iterrows():
            check = st.checkbox(f"Pagar: {cl['nome']} (Vence: {cl['vencimento']})", value=(cl['id'] in st.session_state.selecionados), key=f"cobr_{cl['id']}")
            if check and cl['id'] not in st.session_state.selecionados: st.session_state.selecionados.append(cl['id'])
            elif not check and cl['id'] in st.session_state.selecionados: st.session_state.selecionados.remove(cl['id'])
        
        st.divider()
        if st.session_state.selecionados:
            for s_id in st.session_state.selecionados:
                cli = df[df['id'] == s_id].iloc[0]
                msg = f"Olá {cli['nome']}! Sua assinatura Supertv4k vence em breve. Renove via PIX: {pix_chave}"
                st.link_button(f"ENVIAR PARA {cli['nome']}", f"https://wa.me/{cli['whatsapp']}?text={urllib.parse.quote(msg)}")

with t4:
    st.subheader("⚙️ Configurações do Sistema")
    
    # Gerenciar Servidores
    st.markdown("### ➕ Servidores")
    novo_srv = st.text_input("Nome do Servidor")
    if st.button("ADICIONAR NOVO SERVIDOR"):
        if novo_srv:
            c = sqlite3.connect('supertv_gestao.db'); c.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (novo_srv,)); c.commit(); st.rerun()

    st.divider()
    
    # Importação e Exportação (CORRIGIDO)
    st.markdown("### 💾 Backup e Dados")
    col_up, col_down = st.columns(2)
    
    with col_up:
        st.write("📥 **IMPORTAR DADOS (EXCEL)**")
        file_up = st.file_uploader("Selecione o arquivo .xlsx", type=["xlsx"])
        if file_up and st.button("PROCESSAR IMPORTAÇÃO"):
            data_up = pd.read_excel(file_up)
            conn = sqlite3.connect('supertv_gestao.db')
            data_up.to_sql('clientes', conn, if_exists='append', index=False); conn.close()
            st.success("Dados importados!"); st.rerun()

    with col_down:
        st.write("📤 **EXPORTAR DADOS (DOWNLOAD)**")
        if not df.empty:
            tow = io.BytesIO()
            df.to_excel(tow, index=False)
            st.download_button(label="📥 BAIXAR BACKUP AGORA", data=tow.getvalue(), file_name="backup_supertv4k.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("Sem dados para exportar.")
