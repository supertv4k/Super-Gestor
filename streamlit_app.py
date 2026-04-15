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
    /* Fundo e Container Principal */
    .main { background-color: #05070a; color: #e1e1e1; }
    
    /* Metrics Styling */
    div[data-testid="stMetric"] {
        background-color: #11141b;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #1f2937;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetricValue"] { color: #00f2ff !important; font-size: 24px !important; }
    
    /* Cards de Clientes */
    .client-card {
        background-color: #11141b;
        border: 1px solid #1f2937;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        transition: transform 0.2s;
    }
    .client-card:hover { border-color: #3b82f6; transform: translateY(-2px); }
    
    /* Badges de Status */
    .badge {
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
    }
    .status-ok { background-color: #064e3b; color: #34d399; }
    .status-vencido { background-color: #7f1d1d; color: #f87171; }
    
    /* Dados de Acesso (Destaque) */
    .access-data {
        background-color: #000000;
        color: #00ff00;
        font-family: 'Consolas', monospace;
        padding: 8px;
        border-radius: 5px;
        border: 1px solid #333;
        display: block;
        margin-top: 5px;
    }
    
    /* Botões Customizados */
    .stButton>button {
        background-image: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        height: 45px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento DATE, custo REAL, mensalidade REAL, observacao TEXT, logo BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    
    cols = [("custo", "REAL DEFAULT 0.0"), ("mensalidade", "REAL DEFAULT 0.0"), ("logo", "BLOB")]
    for col, tipo in cols:
        try: c.execute(f"ALTER TABLE clientes ADD COLUMN {col} {tipo}")
        except: pass
    conn.commit()
    conn.close()

init_db()

# --- BACKEND LOGIC ---
def obter_status(venc_data):
    hoje = datetime.now().date()
    pix = "62.326.879/0001-13"
    try:
        venc = datetime.strptime(str(venc_data), '%Y-%m-%d').date() if isinstance(venc_data, str) else venc_data
        dias = (venc - hoje).days
        if dias <= 0: return "🚨 VENCIDO", f"Seu sinal expirou! Renove via PIX: {pix}", "status-vencido", dias
        if dias <= 3: return f"⏳ {dias} DIAS", f"Atenção! Faltam {dias} dias para vencer. PIX: {pix}", "status-vencido", dias
        return f"✅ {dias} DIAS", "", "status-ok", dias
    except: return "ERRO", "", "", 0

# --- CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- SIDEBAR NAV ---
with st.sidebar:
    st.image("https://i.imgur.com/CKq9BVx.png", width=220)
    st.markdown("### 🔍 FILTROS PRO")
    busca = st.text_input("Nome do Cliente")
    
    conn = sqlite3.connect('supertv_gestao.db')
    servs = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    conn.close()
    
    filtro_srv = st.multiselect("Filtrar Servidores", servs)
    st.divider()
    st.caption("Supertv4k Gestão v3.0 Premium")

# --- DASHBOARD HEADER ---
st.markdown("## 📊 Dashboard de Operações")
if not df.empty:
    df['status_label'] = df['vencimento'].apply(lambda x: obter_status(x)[0])
    total = len(df)
    vencidos = len(df[df['status_label'].str.contains("VENCIDO")])
    lucro = df['mensalidade'].sum() - df['custo'].sum()
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("CLIENTES ATIVOS", total)
    m2.metric("PENDENTES", vencidos)
    m3.metric("LUCRO ESTIMADO", f"R$ {lucro:,.2f}")
    m4.metric("ROI", f"{(lucro/df['custo'].sum()*100 if df['custo'].sum()>0 else 0):.1f}%")

st.divider()

# --- ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["💎 GESTÃO", "⚡ NOVO", "📣 COBRANÇA", "⚙️ CONFIG"])

with tab1:
    df_f = df.copy()
    if busca: df_f = df_f[df_f['nome'].str.contains(busca, case=False)]
    if filtro_serv: df_f = df_f[df_f['servidor'].isin(filtro_serv)]

    if not df_f.empty:
        for _, r in df_f.iterrows():
            lbl, msg, css, dias = obter_status(r['vencimento'])
            
            # Card do Cliente
            with st.container():
                st.markdown(f"""
                <div class="client-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.2em; font-weight: bold; color: #fff;">👤 {r['nome'].upper()}</span>
                        <span class="badge {css}">{lbl}</span>
                    </div>
                    <div style="margin-top: 10px; color: #9ca3af; font-size: 0.9em;">📡 {r['servidor']} | {r['sistema']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("Expandir Detalhes"):
                    c1, c2, c3 = st.columns([1, 2, 2])
                    with c1:
                        if r['logo']: st.image(r['logo'], width=100)
                        else: st.markdown("🖼️ **S/ LOGO**")
                    with c2:
                        st.markdown(f"**USUÁRIO:** <div class='access-data'>{r['usuario']}</div>", unsafe_allow_html=True)
                        st.markdown(f"**SENHA:** <div class='access-data'>{r['senha']}</div>", unsafe_allow_html=True)
                        st.write(f"📞 {r['whatsapp']}")
                    with c3:
                        st.write(f"📅 **Vencimento:** {r['vencimento']}")
                        st.info(f"💰 Mensalidade: R$ {r['mensalidade']:.2f}")
                        st.caption(f"Custo: R$ {r['custo']:.2f}")
                    
                    st.divider()
                    a1, a2, a3 = st.columns(3)
                    if a1.button("📝 Editar", key=f"ed_{r['id']}"):
                        st.session_state[f"editing_{r['id']}"] = True
                    if a2.button("🗑️ Remover", key=f"del_{r['id']}"):
                        c = sqlite3.connect('supertv_gestao.db'); c.execute("DELETE FROM clientes WHERE id=?", (r['id'],)); c.commit(); st.rerun()
                    if a3.button("🔄 Renovar +30d", key=f"rv_{r['id']}"):
                        nova = (datetime.strptime(str(r['vencimento']), '%Y-%m-%d') + pd.Timedelta(days=30)).date()
                        c = sqlite3.connect('supertv_gestao.db'); c.execute("UPDATE clientes SET vencimento=? WHERE id=?", (str(nova), r['id'])); c.commit(); st.rerun()

with tab2:
    with st.form("new_premium"):
        st.subheader("🚀 Cadastro de Elite")
        n = st.text_input("NOME COMPLETO")
        w = st.text_input("WHATSAPP (DDD + NÚMERO)")
        cc1, cc2 = st.columns(2); u = cc1.text_input("USUÁRIO"); s = cc2.text_input("SENHA")
        cc3, cc4 = st.columns(2); srv = cc3.selectbox("SERVIDOR", servs); sis = cc4.radio("SISTEMA", ["IPTV", "P2P"], horizontal=True)
        v = st.date_input("VENCIMENTO", value=datetime.now() + pd.Timedelta(days=30))
        cc5, cc6 = st.columns(2); cu = cc5.number_input("CUSTO", 0.0); me = cc6.number_input("VALOR", 35.0)
        obs = st.text_area("OBSERVAÇÕES")
        if st.form_submit_button("CADASTRAR CLIENTE"):
            c = sqlite3.connect('supertv_gestao.db')
            c.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, observacao) VALUES (?,?,?,?,?,?,?,?,?,?)", (n, w, u, s, srv, sis, str(v), cu, me, obs))
            c.commit(); st.success("Cliente Cadastrado com Sucesso!"); st.rerun()

with tab3:
    st.subheader("📢 Central de Avisos")
    cobs = [r for _, r in df.iterrows() if obter_status(r['vencimento'])[3] <= 3]
    if cobs:
        for c in cobs:
            l, m, _, _ = obter_status(c['vencimento'])
            st.markdown(f"🚩 **{c['nome']}** | Status: `{l}`")
            link = f"https://wa.me/{c['whatsapp']}?text={urllib.parse.quote(m)}"
            st.link_button(f"Enviar WhatsApp para {c['nome']}", link)
    else:
        st.success("Tudo em dia! Sem cobranças para hoje.")

with tab4:
    st.subheader("⚙️ Sistema e Servidores")
    # Backup
    if st.button("📥 Gerar Backup Excel"):
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        st.download_button("Baixar Arquivo", buf.getvalue(), "backup_supertv.xlsx")


