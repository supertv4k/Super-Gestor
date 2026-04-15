import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO", layout="wide")

# --- ESTILIZAÇÃO PARA COPIAR A IMAGEM (CSS CUSTOM) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    /* Estilo dos Cards de Métrica conforme a foto */
    .metric-card {
        background-color: #161b22;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 15px;
        border: 1px solid #30363d;
    }
    .metric-label { font-size: 14px; font-weight: bold; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 28px; font-weight: bold; color: #ff4b4b; margin-top: 10px; }
    
    /* Botão de Nome do Cliente */
    .stExpander { border: none !important; background-color: transparent !important; }
    .stExpander > details > summary {
        background-color: #21262d !important;
        padding: 15px !important;
        border-radius: 10px !important;
        color: #ff4b4b !important;
        font-weight: bold !important;
        font-size: 16px !important;
        border: 1px solid #30363d !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ---
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

init_db()

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    conn.close()
    return lista if lista else ["UNIPlAY", "MUNDOGF", "P2BRAZ"]

# --- HEADER (LOGOS) ---
col_l1, col_l2 = st.columns(2)
with col_l1: st.image("https://i.imgur.com/CKq9BVx.png", width=250) # Logo Supertv4k
with col_l2: st.image("https://i.imgur.com/OkUAPQa.png", width=250) # Logo Gestão

# --- CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- DASHBOARD (ESTILO IGUAL À IMAGEM) ---
if not df.empty:
    hoje = datetime.now().date()
    df['venc_dt'] = pd.to_datetime(df['vencimento']).dt.date
    df['dias_restantes'] = (df['venc_dt'] - hoje).apply(lambda x: x.days)
    
    total = len(df)
    em_dia = len(df[df['dias_restantes'] > 0])
    vencidos = len(df[df['dias_restantes'] < 0])
    vence_3d = len(df[(df['dias_restantes'] >= 0) & (df['dias_restantes'] <= 3)])
    bruto = df['mensalidade'].sum()
    custos = df['custo'].sum()
    liquido = bruto - custos

    # Layout de Grade conforme a imagem enviada
    c1, c2 = st.columns(2)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL DE CLIENTES</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-label">CLIENTES EM DIA</div><div class="metric-value">{em_dia}</div></div>', unsafe_allow_html=True)
    
    c3, c4 = st.columns(2)
    with c3: st.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value">{vencidos}</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card"><div class="metric-label">VENCE EM 3 DIAS</div><div class="metric-value">{vence_3d}</div></div>', unsafe_allow_html=True)
    
    c5, c6 = st.columns(2)
    with c5: st.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO BRUTO</div><div class="metric-value">R$ {bruto:,.2f}</div></div>', unsafe_allow_html=True)
    with c6: st.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO LÍQUIDO</div><div class="metric-value">R$ {liquido:,.2f}</div></div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="metric-card"><div class="metric-label">CUSTOS COM CRÉDITOS</div><div class="metric-value">R$ {custos:,.2f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👥 CLIENTES", "➕ ADD CLIENTE", "📢 COBRANÇA", "⚙️ CONFIG"])

with tab1:
    busca = st.text_input("🔍 PESQUISAR NOME...")
    if not df.empty:
        for _, r in df.iterrows():
            if busca.lower() in r['nome'].lower():
                # O NOME DO CLIENTE AGORA É O "BOTÃO" QUE ABRE A EDIÇÃO
                with st.expander(f"👤 {r['nome'].upper()} (Clique para ver/editar)"):
                    with st.form(key=f"ed_form_{r['id']}"):
                        col1, col2 = st.columns(2)
                        en = col1.text_input("Nome", value=r['nome'])
                        ew = col2.text_input("WhatsApp", value=r['whatsapp'])
                        
                        col3, col4 = st.columns(2)
                        eu = col3.text_input("Usuário", value=r['usuario'])
                        es = col4.text_input("Senha", value=r['senha'])
                        
                        col5, col6 = st.columns(2)
                        srv_list = get_servidores()
                        esrv = col5.selectbox("Servidor", srv_list, index=srv_list.index(r['servidor']) if r['servidor'] in srv_list else 0)
                        ev = col6.date_input("Vencimento", value=pd.to_datetime(r['vencimento']).date())
                        
                        col7, col8 = st.columns(2)
                        em = col7.number_input("Mensalidade R$", value=float(r['mensalidade']))
                        ec = col8.number_input("Custo R$", value=float(r['custo']))
                        
                        st.divider()
                        btn_save, btn_del = st.columns(2)
                        if btn_save.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                            conn = sqlite3.connect('supertv_gestao.db')
                            conn.execute("UPDATE clientes SET nome=?, whatsapp=?, usuario=?, senha=?, servidor=?, vencimento=?, mensalidade=?, custo=? WHERE id=?", (en, ew, eu, es, esrv, str(ev), em, ec, r['id']))
                            conn.commit(); st.success("Atualizado!"); st.rerun()
                        
                        if btn_del.form_submit_button("🗑️ EXCLUIR CLIENTE"):
                            conn = sqlite3.connect('supertv_gestao.db')
                            conn.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                            conn.commit(); st.rerun()

with tab2:
    with st.form("add_cli", clear_on_submit=True):
        st.subheader("CADASTRAR NOVO")
        n = st.text_input("NOME")
        w = st.text_input("WHATSAPP")
        c1, c2 = st.columns(2); u = c1.text_input("USER"); s = c2.text_input("SENHA")
        srv = st.selectbox("SERVIDOR", get_servidores())
        v = st.date_input("VENCIMENTO", value=datetime.now())
        c3, c4 = st.columns(2); cu = c3.number_input("CUSTO", 0.0); me = c4.number_input("MENSALIDADE", 35.0)
        if st.form_submit_button("🚀 CADASTRAR"):
            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, vencimento, custo, mensalidade) VALUES (?,?,?,?,?,?,?,?)", (n, w, u, s, srv, str(v), cu, me))
            conn.commit(); st.success("Cadastrado!"); st.rerun()

with tab3:
    st.subheader("📢 Filtro de Cobrança")
    pix = "62.326.879/0001-13"
    if not df.empty:
        # Filtra apenas quem vence em 3 dias ou já venceu
        df_cob = df[df['dias_restantes'] <= 3]
        for _, c in df_cob.iterrows():
            msg = f"Olá {c['nome']}! Sua assinatura vence em breve. Renove via PIX: {pix}"
            st.link_button(f"Enviar para {c['nome']}", f"https://wa.me/{c['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Configurações e Servidores")
    
    # Adicionar Servidor
    new_srv = st.text_input("Novo Nome de Servidor")
    if st.button("➕ ADICIONAR SERVIDOR"):
        if new_srv:
            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (new_srv,))
            conn.commit(); st.success("Servidor Adicionado!"); st.rerun()
    
    st.divider()
    
    # Exportar Excel (Retornou!)
    if not df.empty:
        st.write("📥 Exportar todos os dados dos clientes:")
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        st.download_button(label="📥 BAIXAR LISTA EXCEL", data=buf.getvalue(), file_name=f"clientes_supertv_{datetime.now().strftime('%d_%m')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
