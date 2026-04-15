import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse
import io
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="PAINEL SUPERTV4K", layout="wide", page_icon="📊")

# --- ESTILIZAÇÃO CSS PREMIUM ---
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    [data-testid="stMetricValue"] { color: #00f2ff !important; font-family: 'Courier New', monospace; }
    .stExpander { border: 1px solid #1f2937 !important; border-radius: 10px !important; background-color: #111827 !important; }
    .stButton>button { border-radius: 5px; height: 3em; background-image: linear-gradient(to right, #1e3a8a, #3b82f6); color: white; border: none; }
    .stButton>button:hover { background-image: linear-gradient(to right, #3b82f6, #1e3a8a); }
    .info-box { padding: 15px; border-radius: 10px; background: #1f2937; border-left: 5px solid #3b82f6; margin-bottom: 10px; }
    .user-pass { background-color: #000; padding: 5px 10px; border-radius: 5px; color: #00ff00; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento DATE, custo REAL, mensalidade REAL, observacao TEXT, logo BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    
    colunas = [("custo", "REAL DEFAULT 0.0"), ("mensalidade", "REAL DEFAULT 0.0"), ("logo", "BLOB")]
    for col, tipo in colunas:
        try: c.execute(f"ALTER TABLE clientes ADD COLUMN {col} {tipo}")
        except: pass
    conn.commit()
    conn.close()

init_db()

# --- FUNÇÕES DE SUPORTE ---
def obter_regua(venc_data):
    hoje = datetime.now().date()
    pix = "62.326.879/0001-13"
    venc_data = datetime.strptime(str(venc_data), '%Y-%m-%d').date() if isinstance(venc_data, str) else venc_data
    dias = (venc_data - hoje).days
    if dias == 3: return "Vence em 3 dias", f"⚠️ Sua Assinatura Vence em 3 dias! PIX: {pix}", "🟨", dias
    elif dias == 1: return "Vence Amanhã", f"⏰ Vence Amanhã! Garanta sua renovação. PIX: {pix}", "🟧", dias
    elif dias == 0: return "Vence Hoje", f"🚨 Vence HOJE! Não fique sem sinal. PIX: {pix}", "🟥", dias
    elif dias < 0: return "VENCIDO", f"❌ Assinatura Vencida! Renove agora. PIX: {pix}", "🚨", dias
    return f"{dias} dias", "", "🟩", dias

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    conn.close()
    return lista

# --- CARREGAMENTO DE DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- BARRA LATERAL (FILTROS) ---
with st.sidebar:
    st.image("https://i.imgur.com/CKq9BVx.png", width=200)
    st.title("⚙️ Filtros")
    busca = st.text_input("🔍 Buscar por Nome:")
    servs_at = get_servidores()
    filtro_serv = st.multiselect("📡 Filtrar Servidor:", servs_at)
    st.divider()
    st.write("Versão Pro 2.0")

# --- CÁLCULOS ---
if not df.empty:
    df['status_regua'] = df['vencimento'].apply(obter_regua)
    total_clientes = len(df)
    vencidos = len(df[df['status_regua'].apply(lambda x: x[2] == "🚨")])
    em_dia = total_clientes - vencidos
    bruto = df['mensalidade'].sum()
    custos = df['custo'].sum()
    liquido = bruto - custos
else:
    total_clientes = vencidos = em_dia = bruto = custos = liquido = 0

# --- TELA PRINCIPAL ---
st.title("GESTÃO DE CLIENTES")

# Dash de Métricas com CSS
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total de Clientes", total_clientes)
c2.metric("Vencidos", vencidos, delta=f"{vencidos}", delta_color="inverse")
c3.metric("Faturamento Bruto", f"R$ {bruto:,.2f}")
c4.metric("Lucro Líquido", f"R$ {liquido:,.2f}")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["👥 LISTAGEM", "📈 SAÚDE DA BASE", "📢 COBRANÇA", "🛠️ CONFIG"])

with tab1:
    # Filtragem do DF
    df_display = df.copy()
    if busca:
        df_display = df_display[df_display['nome'].str.contains(busca, case=False)]
    if filtro_serv:
        df_display = df_display[df_display['servidor'].isin(filtro_serv)]

    if not df_display.empty:
        for _, r in df_display.iterrows():
            status, _, icon, _ = obter_regua(r['vencimento'])
            with st.expander(f"{icon} {r['nome']} | {r['servidor']} | {status}"):
                col_img, col_info, col_fin = st.columns([1, 2, 2])
                with col_img:
                    if r['logo']: st.image(r['logo'], width=100)
                    else: st.info("Sem Logo")
                with col_info:
                    st.markdown(f"**USUÁRIO:** <span class='user-pass'>{r['usuario']}</span>", unsafe_allow_html=True)
                    st.markdown(f"**SENHA:** <span class='user-pass'>{r['senha']}</span>", unsafe_allow_html=True)
                    st.write(f"📱 WhatsApp: {r['whatsapp']}")
                with col_fin:
                    st.write(f"📅 Vencimento: {r['vencimento']}")
                    st.write(f"💰 Mensalidade: R$ {r['mensalidade']:.2f}")
                    st.write(f"💳 Custo: R$ {r['custo']:.2f}")
                
                # Ações rápidas
                b1, b2, b3 = st.columns(3)
                if b1.button("📝 EDITAR", key=f"e_{r['id']}"):
                    st.session_state[f"edit_{r['id']}"] = True
                if b2.button("🗑️ EXCLUIR", key=f"d_{r['id']}"):
                    c = sqlite3.connect('supertv_gestao.db'); c.execute("DELETE FROM clientes WHERE id=?", (r['id'],)); c.commit(); st.rerun()
                if b3.button("🔄 RENOVAR 30D", key=f"r_{r['id']}"):
                    nova = (datetime.strptime(str(r['vencimento']), '%Y-%m-%d') + pd.Timedelta(days=30)).date()
                    c = sqlite3.connect('supertv_gestao.db'); c.execute("UPDATE clientes SET vencimento=? WHERE id=?", (str(nova), r['id'])); c.commit(); st.rerun()

with tab2:
    if total_clientes > 0:
        st.subheader("📊 GRÁFICO DE RENOVAÇÕES")
        fig = px.pie(values=[em_dia, vencidos], names=['Em Dia', 'Vencidos'], hole=.4, color_discrete_sequence=['#00ff00', '#ff0000'])
        st.plotly_chart(fig)
        
        st.subheader("💸 DETALHAMENTO FINANCEIRO")
        f1, f2 = st.columns(2)
        f1.info(f"CUSTO TOTAL : R$ {custos:,.2f}")
        f2.success(f"LUCRO ESTIMADO: R$ {liquido:,.2f}")
    else:
        st.warning("Sem dados para gerar gráficos.")

with tab3:
    st.subheader("🚀CENTRAL DE COBRANÇAS")
    # Lógica de cobrança simplificada e profissional
    cobrancas = [r for _, r in df.iterrows() if obter_regua(r['vencimento'])[3] <= 3]
    if cobrancas:
        for c in cobrancas:
            status, msg, icon, _ = obter_regua(c['vencimento'])
            st.write(f"{icon} **{c['nome']}** ({status})")
            link = f"https://wa.me/{c['whatsapp']}?text={urllib.parse.quote(msg)}"
            st.link_button(f"Enviar WhatsApp para {c['nome']}", link)
    else:
        st.success("Nenhuma cobrança pendente para os próximos 3 dias!")

with tab4:
    st.subheader("⚙️ CONFIGURAÇÕES")
    # Espaço para Backup e Gestão de Servidores (Como no seu script anterior)
    if st.button("📥 Exportar Backup Excel"):
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        st.download_button("Clique para Baixar", buf.getvalue(), "backup_supertv.xlsx")

