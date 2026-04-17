import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
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
    
    /* Cores das linhas de cliente na cobrança */
    .cliente-row { border-radius: 12px; padding: 12px; margin-bottom: 10px; display: flex; align-items: center; gap: 20px; border: 1px solid #30363d; }
    .row-vencido { background-color: #331111; border-left: 8px solid #ff4b4b; }
    .row-hoje { background-color: #3d2b11; border-left: 8px solid #ffa500; }
    .row-breve { background-color: #333311; border-left: 8px solid #ffff00; }
    .row-em-dia { background-color: #112233; border-left: 8px solid #00d4ff; }
    
    .logo-externa { width: 85px; height: 85px; border-radius: 10px; object-fit: contain; background: #21262d; border: 1px solid #444; }
    .info-container { flex-grow: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .info-txt { font-size: 14px; color: #ffffff; }
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 12px; text-align: center; border: 1px solid #30363d; margin-bottom: 10px; }
    .metric-label { font-size: 11px; font-weight: bold; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 20px; font-weight: bold; color: #ffffff; margin-top: 5px; }
    div.stFormSubmitButton > button { background: linear-gradient(135deg, #0052D4 0%, #929ED1 50%, #E0EAFC 100%) !important; color: #1e1e1e !important; font-weight: 900 !important; border-radius: 10px !important; width: 100%; height: 50px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES AUXILIARES ---
def image_to_base64(image_file):
    if image_file is not None:
        try: return base64.b64encode(image_file.read()).decode()
        except: return None
    return None

def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento TEXT, custo REAL, mensalidade REAL, 
                  inicio TEXT, observacao TEXT, logo_blob TEXT)''')
    conn.commit(); conn.close()

def get_servidores():
    return ["UNITV", "UNIPLAY", "P2BRAZ", "MUNDOGF", "PLAY TV", "TV EXPRESS", "REDPLAY"]

init_db()

# --- 4. CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- 5. HEADER ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

# --- 6. DASHBOARD ---
if not df.empty:
    hoje = datetime.now().date()
    df['mensalidade'] = pd.to_numeric(df['mensalidade'], errors='coerce').fillna(0)
    df['custo'] = pd.to_numeric(df['custo'], errors='coerce').fillna(0)
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 0)
    
    bruto = df['mensalidade'].sum()
    custos = df['custo'].sum()
    liquido = bruto - custos
    
    vencidos = len(df[df["dias_res"] < 0])
    vencendo_3 = len(df[(df["dias_res"] >= 0) & (df["dias_res"] <= 3)])

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">CLIENTES</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value" style="color:#ff4b4b;">{vencidos}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">3 DIAS</div><div class="metric-value" style="color:#ffff00;">{vencendo_3}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">BRUTO</div><div class="metric-value" style="color:#00ff00;">R${bruto:,.0f}</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-label">LÍQUIDO</div><div class="metric-value" style="color:#00d4ff;">R${liquido:,.0f}</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="metric-card"><div class="metric-label">CUSTOS</div><div class="metric-value">R${custos:,.0f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 7. ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADD CLIENTE", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔎 Pesquisar cliente...", placeholder="Digite nome ou usuário...")
    if not df.empty:
        df_f = df[df['nome'].notnull() & (df['nome'].astype(str).str.strip() != '')].copy()
        if busca:
            df_f = df_f[df_f['nome'].str.contains(busca, case=False, na=False) | df_f['usuario'].str.contains(busca, case=False, na=False)]

        for _, r in df_f.sort_values(by='nome').iterrows():
            img_data = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            st.markdown(f"""
            <div class="cliente-row" style="background-color: #161b22;">
                <img src="{img_data}" class="logo-externa">
                <div class="info-container">
                    <div class="info-txt">👤 <b>NOME:</b> {str(r['nome']).upper()}</div>
                    <div class="info-txt">🔑 <b>USUÁRIO:</b> {r['usuario']}</div>
                    <div class="info-txt">📶 <b>SISTEMA:</b> {r['servidor']}</div>
                    <div class="info-txt">📅 <b>VENCIMENTO:</b> {r['vencimento']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    st.subheader("🚀 Cadastro Manual")
    with st.form("add"):
        c1, c2 = st.columns(2)
        n_n = c1.text_input("NOME DO CLIENTE")
        n_u = c2.text_input("USUÁRIO")
        n_srv = c1.selectbox("SERVIDOR", get_servidores())
        n_v = c2.date_input("VENCIMENTO", value=datetime.now().date()+timedelta(days=30))
        n_c = c1.number_input("CUSTO (R$)", value=10.0)
        n_m = c2.number_input("MENSALIDADE (R$)", value=35.0)
        n_w = st.text_input("WHATSAPP (Ex: 62999999999)")
        n_l = st.file_uploader("LOGOMARCA", type=['png','jpg'])
        if st.form_submit_button("🚀 SALVAR CLIENTE"):
            if n_n.strip() == "": st.error("O nome é obrigatório!")
            else:
                l_b = image_to_base64(n_l)
                c_in = sqlite3.connect('supertv_gestao.db')
                c_in.execute("INSERT INTO clientes (nome, usuario, servidor, vencimento, custo, mensalidade, whatsapp, logo_blob) VALUES (?,?,?,?,?,?,?,?)",
                            (n_n, n_u, n_srv, n_v.strftime('%Y-%m-%d'), n_c, n_m, n_w, l_b))
                c_in.commit(); st.rerun()

with tab3:
    st.subheader("🚨 Lista de Cobrança Colorida")
    pix = "62.326.879/0001-13"
    if not df.empty:
        df_cob = df[df['nome'].notnull() & (df['nome'].astype(str).str.strip() != '')].copy()
        
        sel_todos = st.toggle("✅ Selecionar Todos os Clientes")
        clientes_selecionados = []
        
        for idx, c in df_cob.sort_values(by='dias_res').iterrows():
            # Define a classe de cor
            if c['dias_res'] < 0:
                cls, status = "row-vencido", "🔴 VENCIDO"
            elif c['dias_res'] == 0:
                cls, status = "row-hoje", "🟠 VENCE HOJE"
            elif 1 <= c['dias_res'] <= 3:
                cls, status = "row-breve", "🟡 VENCE EM 1-3 DIAS"
            else:
                cls, status = "row-em-dia", "🔵 EM DIA"
            
            col_check, col_card = st.columns([0.1, 0.9])
            with col_check:
                if st.checkbox("", value=sel_todos, key=f"cb_{idx}"):
                    clientes_selecionados.append(c)
            
            with col_card:
                img_data = f"data:image/png;base64,{c['logo_blob']}" if c['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
                st.markdown(f"""
                <div class="cliente-row {cls}">
                    <img src="{img_data}" class="logo-externa">
                    <div class="info-container">
                        <div class="info-txt">👤 <b>{str(c['nome']).upper()}</b></div>
                        <div class="info-txt"><b>STATUS:</b> {status}</div>
                        <div class="info-txt">📶 {c['servidor']} | 🔑 {c['usuario']}</div>
                        <div class="info-txt">📅 Vence em: {c['vencimento']} ({c['dias_res']} dias)</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        if st.button(f"📲 GERAR LINKS PARA {len(clientes_selecionados)} SELECIONADOS", use_container_width=True):
            if not clientes_selecionados:
                st.warning("Selecione alguém na lista acima!")
            else:
                for item in clientes_selecionados:
                    txt_v = "venceu" if item['dias_res'] < 0 else "vence hoje" if item['dias_res'] == 0 else f"vence em {item['dias_res']} dias"
                    msg = f"Olá {str(item['nome']).split()[0]}! 👋 Sua assinatura {item['servidor']} {txt_v}. Valor: R$ {item['mensalidade']:.2f}. Pix: {pix}"
                    st.link_button(f"Enviar para {item['nome']}", f"https://wa.me/55{item['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Manutenção")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ LIMPAR CLIENTES INVÁLIDOS"):
            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("DELETE FROM clientes WHERE nome IS NULL OR nome = '' OR nome = 'None'")
            conn.commit(); conn.close(); st.success("Limpeza feita!"); st.rerun()
    with c2:
        f_up = st.file_uploader("Importar Excel", type=["xlsx"])
        if f_up and st.button("🚀 IMPORTAR"):
            try:
                imp = pd.read_excel(f_up, engine='openpyxl')
                imp.columns = [str(c).strip().upper() for c in imp.columns]
                mapa = {'CLIENTE': 'nome', 'USUÁRIO': 'usuario', 'SERVIDOR': 'servidor', 'VENCIMENTO': 'vencimento', 'CUSTO': 'custo', 'VALOR COBRADO': 'mensalidade', 'WHATSAPP': 'whatsapp'}
                imp = imp.rename(columns=mapa)
                if 'nome' in imp.columns:
                    imp['nome'] = imp['nome'].astype(str).str.strip()
                    imp = imp[(imp['nome'].notnull()) & (imp['nome'].str.lower() != 'none') & (imp['nome'] != '')]
                conn = sqlite3.connect('supertv_gestao.db')
                imp.to_sql('clientes', conn, if_exists='append', index=False)
                conn.close(); st.success("Lista importada!"); st.rerun()
            except Exception as e: st.error(f"Erro: {e}")
