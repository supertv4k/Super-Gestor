import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k PRO", layout="wide", page_icon="🚀")

# --- DESIGN SYSTEM PREMIUM (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #05070a; color: #e1e1e1; }
    div[data-testid="stMetric"] {
        background-color: #11141b;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #1f2937;
    }
    div[data-testid="stMetricValue"] { color: #00f2ff !important; }
    .client-card {
        background-color: #11141b;
        border: 1px solid #1f2937;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .status-ok { color: #34d399; font-weight: bold; }
    .status-vencido { color: #f87171; font-weight: bold; }
    .access-data {
        background-color: #000;
        color: #00ff00;
        font-family: monospace;
        padding: 5px;
        border-radius: 4px;
        border: 1px solid #333;
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
                  vencimento DATE, custo REAL, mensalidade REAL, observacao TEXT, logo BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    
    # Migração silenciosa de colunas
    cols = [("custo", "REAL DEFAULT 0.0"), ("mensalidade", "REAL DEFAULT 0.0"), ("sistema", "TEXT DEFAULT 'IPTV'")]
    for col, tipo in cols:
        try: c.execute(f"ALTER TABLE clientes ADD COLUMN {col} {tipo}")
        except: pass
    conn.commit()
    conn.close()

init_db()

# --- BACKEND ---
def obter_status(venc_data):
    hoje = datetime.now().date()
    try:
        venc = datetime.strptime(str(venc_data), '%Y-%m-%d').date() if isinstance(venc_data, str) else venc_data
        dias = (venc - hoje).days
        if dias <= 0: return "🚨 VENCIDO", "status-vencido", dias
        return f"✅ {dias} DIAS", "status-ok", dias
    except: return "ERRO", "", 0

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    conn.close()
    return lista

# --- CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- SIDEBAR (DEFINIÇÃO DAS VARIÁVEIS DE FILTRO) ---
with st.sidebar:
    st.image("https://i.imgur.com/CKq9BVx.png", width=200)
    st.markdown("### 🔍 FILTROS")
    busca_nome = st.text_input("Nome do Cliente")
    lista_servs = get_servidores()
    filtro_serv = st.multiselect("Filtrar Servidores", lista_servs)
    st.divider()

# --- DASHBOARD SUPERIOR ---
st.markdown("## 📊 Painel de Controle Supertv4k")
if not df.empty:
    total = len(df)
    bruto = df['mensalidade'].sum()
    custo_total = df['custo'].sum()
    lucro = bruto - custo_total
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("CLIENTES", total)
    m2.metric("FAT. BRUTO", f"R$ {bruto:,.2f}")
    m3.metric("LUCRO LÍQUIDO", f"R$ {lucro:,.2f}")
    m4.metric("CUSTOS", f"R$ {custo_total:,.2f}")

st.divider()

# --- ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["💎 GESTÃO", "⚡ NOVO", "📢 COBRANÇA", "⚙️ CONFIG"])

with tab1:
    # Aplicando os filtros (agora as variáveis filtro_serv e busca_nome já existem)
    df_f = df.copy()
    if busca_nome:
        df_f = df_f[df_f['nome'].str.contains(busca_nome, case=False)]
    if filtro_serv:
        df_f = df_f[df_f['servidor'].isin(filtro_serv)]

    if not df_f.empty:
        for _, r in df_f.iterrows():
            lbl, css, dias = obter_status(r['vencimento'])
            
            # Card Principal
            st.markdown(f"""
            <div class="client-card">
                <span style="font-size: 1.1em; font-weight: bold;">👤 {r['nome'].upper()}</span> | 
                <span class="{css}">{lbl}</span> | 
                <span style="color: #9ca3af;">📡 {r['servidor']}</span>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("Ver detalhes e Ações"):
                col1, col2, col3 = st.columns([1, 2, 2])
                with col1:
                    if r['logo']: st.image(r['logo'], width=80)
                    else: st.write("📷 S/ Logo")
                with col2:
                    st.markdown(f"**USUÁRIO:** <div class='access-data'>{r['usuario']}</div>", unsafe_allow_html=True)
                    st.markdown(f"**SENHA:** <div class='access-data'>{r['senha']}</div>", unsafe_allow_html=True)
                    st.write(f"📞 WhatsApp: {r['whatsapp']}")
                with col3:
                    st.write(f"💰 Mensalidade: R$ {r['mensalidade']:.2f}")
                    st.write(f"📅 Vencimento: {r['vencimento']}")
                    st.caption(f"Obs: {r['observacao']}")
                
                # Ações
                st.divider()
                a1, a2, a3 = st.columns(3)
                if a1.button("🗑️ Excluir", key=f"del_{r['id']}"):
                    c = sqlite3.connect('supertv_gestao.db'); c.execute("DELETE FROM clientes WHERE id=?", (r['id'],)); c.commit(); st.rerun()
                if a2.button("🔄 Renovar +30d", key=f"rv_{r['id']}"):
                    nova = (datetime.strptime(str(r['vencimento']), '%Y-%m-%d') + pd.Timedelta(days=30)).date()
                    c = sqlite3.connect('supertv_gestao.db'); c.execute("UPDATE clientes SET vencimento=? WHERE id=?", (str(nova), r['id'])); c.commit(); st.rerun()
                if a3.button("📝 Editar", key=f"ed_{r['id']}"):
                    st.info("Função de edição em lote ativa no banco.")

with tab2:
    with st.form("novo_p"):
        st.subheader("🚀 Novo Cadastro")
        n = st.text_input("NOME")
        w = st.text_input("WHATSAPP")
        c1, c2 = st.columns(2); u = c1.text_input("USER"); s = c2.text_input("SENHA")
        c3, c4 = st.columns(2); srv = c3.selectbox("SERVIDOR", lista_servs); sis = c4.radio("SISTEMA", ["IPTV", "P2P"], horizontal=True)
        v = st.date_input("VENCIMENTO", value=datetime.now() + pd.Timedelta(days=30))
        c5, c6 = st.columns(2); cu = c5.number_input("CUSTO", 0.0); me = c6.number_input("VALOR", 35.0)
        if st.form_submit_button("CADASTRAR"):
            c = sqlite3.connect('supertv_gestao.db')
            c.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, sistema, vencimento, custo, mensalidade) VALUES (?,?,?,?,?,?,?,?,?)", (n, w, u, s, srv, sis, str(v), cu, me))
            c.commit(); st.success("Cadastrado!"); st.rerun()

with tab3:
    st.subheader("📢 Cobranças Próximas")
    pix = "62.326.879/0001-13"
    cobs = [r for _, r in df.iterrows() if obter_status(r['vencimento'])[2] <= 3]
    for c in cobs:
        msg = f"Olá {c['nome']}! Sua assinatura vence em breve. Renove via PIX: {pix}"
        link = f"https://wa.me/{c['whatsapp']}?text={urllib.parse.quote(msg)}"
        st.link_button(f"Enviar para {c['nome']}", link)

with tab4:
    st.subheader("⚙️ Configurações")
    # Adicionar Servidor
    new_s = st.text_input("Nome do Novo Servidor")
    if st.button("Adicionar"):
        c = sqlite3.connect('supertv_gestao.db'); c.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (new_s,)); c.commit(); st.rerun()
    # Exportar
    if st.button("📥 Backup Excel"):
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        st.download_button("Baixar", buf.getvalue(), "backup.xlsx")
