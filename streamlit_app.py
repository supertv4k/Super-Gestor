import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k PRO", layout="wide", page_icon="🚀")

# --- DESIGN SYSTEM PREMIUM ---
st.markdown("""
    <style>
    .main { background-color: #05070a; color: #e1e1e1; }
    div[data-testid="stMetric"] { background-color: #11141b; padding: 15px; border-radius: 12px; border: 1px solid #1f2937; }
    div[data-testid="stMetricValue"] { color: #00f2ff !important; }
    .client-card { background-color: #11141b; border: 1px solid #1f2937; border-radius: 15px; padding: 15px; margin-bottom: 10px; }
    .access-data { background-color: #000; color: #00ff00; font-family: monospace; padding: 5px; border-radius: 4px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento DATE, custo REAL, mensalidade REAL, observacao TEXT, logo BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    conn.commit()
    conn.close()

init_db()

# --- FUNÇÕES ---
def obter_status(venc_data):
    hoje = datetime.now().date()
    try:
        venc = datetime.strptime(str(venc_data), '%Y-%m-%d').date() if isinstance(venc_data, str) else venc_data
        dias = (venc - hoje).days
        if dias <= 0: return "🚨 VENCIDO", "color: #f87171;", dias
        return f"✅ {dias} DIAS", "color: #34d399;", dias
    except: return "ERRO", "", 0

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    conn.close()
    return lista if lista else ["PADRÃO"]

# --- CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://i.imgur.com/CKq9BVx.png", width=200)
    st.markdown("### 🔍 FILTROS")
    busca_nome = st.text_input("Nome do Cliente")
    lista_servs = get_servidores()
    filtro_serv = st.multiselect("Filtrar Servidores", lista_servs)

# --- HEADER ---
st.markdown("## 📊 Painel Administrativo Supertv4k")
if not df.empty:
    m1, m2, m3 = st.columns(3)
    m1.metric("CLIENTES", len(df))
    m2.metric("LUCRO LÍQUIDO", f"R$ {(df['mensalidade'].sum() - df['custo'].sum()):,.2f}")
    m3.metric("VENCIDOS", len(df[df['vencimento'].apply(lambda x: (datetime.strptime(str(x), '%Y-%m-%d').date() - datetime.now().date()).days <= 0)]))

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["💎 GESTÃO", "⚡ NOVO", "📢 COBRANÇA", "⚙️ CONFIG"])

with tab1:
    df_f = df.copy()
    if busca_nome: df_f = df_f[df_f['nome'].str.contains(busca_nome, case=False)]
    if filtro_serv: df_f = df_f[df_f['servidor'].isin(filtro_serv)]

    if not df_f.empty:
        for _, r in df_f.iterrows():
            lbl, style, dias = obter_status(r['vencimento'])
            
            st.markdown(f"""
            <div class="client-card">
                <span style="font-size: 1.1em; font-weight: bold;">👤 {r['nome'].upper()}</span> | 
                <span style="{style}">{lbl}</span> | 
                <span style="color: #9ca3af;">📡 {r['servidor']}</span>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("📝 Visualizar / Editar Dados"):
                # --- FORMULÁRIO DE EDIÇÃO ---
                with st.form(key=f"form_ed_{r['id']}"):
                    c1, c2 = st.columns(2)
                    new_nome = c1.text_input("Nome", value=r['nome'])
                    new_zap = c2.text_input("WhatsApp", value=r['whatsapp'])
                    
                    c3, c4 = st.columns(2)
                    new_user = c3.text_input("Usuário", value=r['usuario'])
                    new_pass = c4.text_input("Senha", value=r['senha'])
                    
                    c5, c6, c7 = st.columns(3)
                    new_srv = c5.selectbox("Servidor", lista_servs, index=lista_servs.index(r['servidor']) if r['servidor'] in lista_servs else 0)
                    new_venc = c6.date_input("Vencimento", value=datetime.strptime(str(r['vencimento']), '%Y-%m-%d').date())
                    new_sis = c7.radio("Sistema", ["IPTV", "P2P"], index=0 if r['sistema'] == "IPTV" else 1, horizontal=True)
                    
                    c8, c9 = st.columns(2)
                    new_mens = c8.number_input("Mensalidade (R$)", value=float(r['mensalidade']))
                    new_custo = c9.number_input("Custo Crédito (R$)", value=float(r['custo']))
                    
                    new_obs = st.text_area("Observação", value=r['observacao'])
                    
                    # Botão de Salvar dentro do formulário
                    col_btn1, col_btn2 = st.columns(2)
                    if col_btn1.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                        conn = sqlite3.connect('supertv_gestao.db')
                        conn.execute("""UPDATE clientes SET 
                                     nome=?, whatsapp=?, usuario=?, senha=?, servidor=?, 
                                     sistema=?, vencimento=?, mensalidade=?, custo=?, observacao=? 
                                     WHERE id=?""", 
                                     (new_nome, new_zap, new_user, new_pass, new_srv, new_sis, str(new_venc), new_mens, new_custo, new_obs, r['id']))
                        conn.commit()
                        st.success("Dados atualizados!")
                        st.rerun()
                    
                    if col_btn2.form_submit_button("🗑️ EXCLUIR CLIENTE"):
                        conn = sqlite3.connect('supertv_gestao.db')
                        conn.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                        conn.commit()
                        st.rerun()

with tab2:
    # (O formulário de cadastro segue a mesma lógica segura)
    with st.form("novo_p"):
        st.subheader("🚀 Novo Cadastro")
        n = st.text_input("NOME")
        w = st.text_input("WHATSAPP")
        c1, c2 = st.columns(2); u = c1.text_input("USER"); s = c2.text_input("SENHA")
        c3, c4 = st.columns(2); srv = c3.selectbox("SERVIDOR", lista_servs); sis = c4.radio("SISTEMA", ["IPTV", "P2P"], horizontal=True)
        v = st.date_input("VENCIMENTO", value=datetime.now())
        c5, c6 = st.columns(2); cu = c5.number_input("CUSTO", 0.0); me = c6.number_input("VALOR", 35.0)
        if st.form_submit_button("CADASTRAR"):
            c = sqlite3.connect('supertv_gestao.db')
            c.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, sistema, vencimento, custo, mensalidade) VALUES (?,?,?,?,?,?,?,?,?)", (n, w, u, s, srv, sis, str(v), cu, me))
            c.commit(); st.success("Cadastrado!"); st.rerun()

with tab3:
    st.subheader("📢 Central de Cobrança")
    pix = "62.326.879/0001-13"
    cobs = [r for _, r in df.iterrows() if obter_status(r['vencimento'])[2] <= 3]
    for c in cobs:
        msg = f"Olá {c['nome']}! Sua assinatura vence em breve. Renove via PIX: {pix}"
        st.link_button(f"Enviar para {c['nome']}", f"https://wa.me/{c['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Configurações")
    new_s = st.text_input("Novo Nome de Servidor")
    if st.button("Adicionar Servidor"):
        c = sqlite3.connect('supertv_gestao.db'); c.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (new_s,)); c.commit(); st.rerun()
