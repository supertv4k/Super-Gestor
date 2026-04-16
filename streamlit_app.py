import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta, time
import urllib.parse
import io
import base64

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    .cliente-row { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 12px; margin-bottom: 10px; display: flex; align-items: center; gap: 20px; }
    .logo-externa { width: 85px; height: 85px; border-radius: 10px; object-fit: contain; background: #21262d; border: 1px solid #444; }
    .info-container { flex-grow: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .info-txt { font-size: 14px; color: #c9d1d9; }
    .destaque-vermelho { color: #ff4b4b; font-weight: bold; }
    .destaque-verde { color: #00ff00; font-weight: bold; }
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 12px; text-align: center; border: 1px solid #30363d; margin-bottom: 10px; }
    .metric-label { font-size: 11px; font-weight: bold; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 20px; font-weight: bold; margin-top: 5px; }
    div.stFormSubmitButton > button { background: linear-gradient(135deg, #0052D4 0%, #929ED1 50%, #E0EAFC 100%) !important; color: #1e1e1e !important; font-weight: 900 !important; border-radius: 10px !important; width: 100%; height: 50px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES E BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento TEXT, custo REAL, mensalidade REAL, 
                  inicio TEXT, observacao TEXT, logo_blob TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    conn.commit(); conn.close()

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    try: lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    except: lista = []
    conn.close()
    return lista if lista else ["UNITV", "UNIPLAY", "P2BRAZ", "MUNDOGF", "PLAY TV"]

def image_to_base64(image_file):
    if image_file is not None:
        try: return base64.b64encode(image_file.read()).decode()
        except: return None
    return None

# Inicializa e Carrega os Dados (CRÍTICO)
init_db()
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- 4. HEADER ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

# --- 5. DASHBOARD (CÁLCULOS SEGUROS) ---
if not df.empty:
    hoje = datetime.now().date()
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 0)
    
    bruto, custos = df['mensalidade'].sum(), df['custo'].sum()
    liquido = bruto - custos
    vencidos = len(df[df["dias_res"] < 0])
    vencendo_3 = len(df[(df["dias_res"] >= 0) & (df["dias_res"] <= 3)])

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">CLIENTES</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value" style="color:#ff4b4b;">{vencidos}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">3 DIAS</div><div class="metric-value" style="color:#ffff00;">{vencendo_3}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">BRUTO</div><div class="metric-value" style="color:#00ff00;">R${bruto:.0f}</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-label">LÍQUIDO</div><div class="metric-value" style="color:#00d4ff;">R${liquido:.0f}</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="metric-card"><div class="metric-label">CUSTO</div><div class="metric-value">R${custos:.0f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 6. ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADD", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔎 Pesquisar...", placeholder="Nome ou Usuário")
    if not df.empty:
        df_f = df.copy()
        if busca:
            df_f = df_f[df_f['nome'].str.contains(busca, case=False, na=False) | df_f['usuario'].str.contains(busca, case=False, na=False)]
        
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            status_cor = "destaque-verde" if r['dias_res'] >= 0 else "destaque-vermelho"
            dias_txt = f"{r['dias_res']} DIAS" if r['dias_res'] >= 0 else "VENCIDO"
            img_data = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            st.markdown(f'<div class="cliente-row"><img src="{img_data}" class="logo-externa"><div class="info-container"><div class="info-txt">👤 <b>{r["nome"].upper()}</b></div><div class="info-txt">📅 <b>STATUS:</b> <span class="{status_cor}">{dias_txt}</span></div><div class="info-txt">🔑 {r["usuario"]}</div><div class="info-txt">📶 {r["servidor"]}</div></div></div>', unsafe_allow_html=True)

with tab2:
    with st.form("add_cliente"):
        c1, c2 = st.columns(2)
        n_n = c1.text_input("NOME")
        n_u = c2.text_input("USUÁRIO")
        n_srv = c1.selectbox("SERVIDOR", get_servidores())
        n_v = c2.date_input("VENCIMENTO", value=datetime.now()+timedelta(days=30))
        n_w = c1.text_input("WHATSAPP (Ex: 62999999999)")
        n_m = c2.number_input("MENSALIDADE", value=35.0)
        n_l = st.file_uploader("LOGOMARCA", type=['png','jpg'])
        if st.form_submit_button("🚀 CADASTRAR"):
            v_f = datetime.combine(n_v, time(12,0)).strftime('%Y-%m-%d %H:%M:%S')
            l_b = image_to_base64(n_l)
            c_in = sqlite3.connect('supertv_gestao.db')
            c_in.execute("INSERT INTO clientes (nome, usuario, vencimento, mensalidade, whatsapp, servidor, logo_blob) VALUES (?,?,?,?,?,?,?)", (n_n, n_u, v_f, n_m, n_w, n_srv, l_b))
            c_in.commit(); st.rerun()

with tab3:
    st.subheader("🚨 COBRANÇA")
    pix = "62.326.879/0001-13"
    if not df.empty:
        df_cob = df.copy()
        df_cob['STATUS'] = df_cob['dias_res'].apply(lambda d: "🔴 VENCIDO" if d < 0 else "🟢 ATIVO")
        sel = st.data_editor(df_cob[['id', 'nome', 'STATUS', 'servidor']], hide_index=True)
        if st.button("🔗 GERAR LINKS"):
            st.info("Links gerados com a chave Pix: " + pix)

with tab4:
    st.subheader("⚙️ AJUSTES")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**📥 Importar Excel**")
        f_up = st.file_uploader("Arquivo .xlsx", type=["xlsx"])
        if f_up and st.button("PROCESSAR"):
            try:
                df_imp = pd.read_excel(f_up, engine='openpyxl')
                df_imp.to_sql('clientes', sqlite3.connect('supertv_gestao.db'), if_exists='append', index=False)
                st.success("Sucesso!"); st.rerun()
            except Exception as e: st.error(e)
    with col2:
        st.write("**📤 Backup**")
        if not df.empty:
            out = io.BytesIO()
            df.drop(columns=['logo_blob'], errors='ignore').to_excel(out, index=False, engine='xlsxwriter')
            st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "backup.xlsx", use_container_width=True)
