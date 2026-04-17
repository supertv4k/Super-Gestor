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
    .cliente-row { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 12px; margin-bottom: 10px; display: flex; align-items: center; gap: 20px; }
    .logo-externa { width: 85px; height: 85px; border-radius: 10px; object-fit: contain; background: #21262d; border: 1px solid #444; }
    .info-container { flex-grow: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .info-txt { font-size: 14px; color: #c9d1d9; }
    .destaque-vermelho { color: #ff4b4b; font-weight: bold; }
    .destaque-verde { color: #00ff00; font-weight: bold; }
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
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    conn.commit(); conn.close()

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    try: lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    except: lista = []
    conn.close()
    return lista if lista else ["UNITV", "UNIPLAY", "P2BRAZ", "MUNDOGF", "PLAY TV"]

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
    c4.markdown(f'<div class="metric-card"><div class="metric-label">BRUTO</div><div class="metric-value" style="color:#00ff00;">R${bruto:,.0f}</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-label">LÍQUIDO</div><div class="metric-value" style="color:#00d4ff;">R${liquido:,.0f}</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="metric-card"><div class="metric-label">CUSTOS</div><div class="metric-value">R${custos:,.0f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 7. ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADD CLIENTE", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔎 Pesquisar por Nome ou Usuário...", placeholder="Digite aqui...")
    if not df.empty:
        # Filtro de exibição: ignora quem não tem nome
        df_f = df[df['nome'].notnull() & (df['nome'].astype(str).str.lower() != 'none') & (df['nome'].astype(str).str.strip() != '')].copy()
        
        if busca:
            df_f = df_f[df_f['nome'].str.contains(busca, case=False, na=False) | df_f['usuario'].str.contains(busca, case=False, na=False)]

        for _, r in df_f.sort_values(by='dias_res').iterrows():
            nome_display = str(r['nome']).upper()
            status_cor = "destaque-verde" if r['dias_res'] >= 0 else "destaque-vermelho"
            dias_txt = f"{r['dias_res']} DIAS" if r['dias_res'] >= 0 else "VENCIDO"
            img_data = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"

            st.markdown(f"""
            <div class="cliente-row">
                <img src="{img_data}" class="logo-externa">
                <div class="info-container">
                    <div class="info-txt">👤 <b>CLIENTE:</b> {nome_display}</div>
                    <div class="info-txt">📅 <b>STATUS:</b> <span class="{status_cor}">{dias_txt}</span></div>
                    <div class="info-txt">🔑 <b>USER:</b> {r['usuario']}</div>
                    <div class="info-txt">📶 <b>SISTEMA:</b> {r['servidor']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    st.subheader("🚀 Novo Cliente")
    with st.form("add"):
        n_n = st.text_input("NOME DO CLIENTE")
        n_u = st.text_input("USUÁRIO")
        n_srv = st.selectbox("SERVIDOR", get_servidores())
        n_v = st.date_input("VENCIMENTO", value=datetime.now().date()+timedelta(days=30))
        n_c = st.number_input("CUSTO", value=10.0)
        n_m = st.number_input("VALOR COBRADO", value=35.0)
        n_w = st.text_input("WHATSAPP (Ex: 62999999999)")
        n_l = st.file_uploader("LOGOMARCA", type=['png','jpg'])
        if st.form_submit_button("🚀 CADASTRAR"):
            if n_n.strip() == "":
                st.error("Erro: O nome do cliente não pode estar vazio.")
            else:
                l_b = image_to_base64(n_l)
                c_in = sqlite3.connect('supertv_gestao.db')
                c_in.execute("INSERT INTO clientes (nome, usuario, servidor, vencimento, custo, mensalidade, whatsapp, logo_blob) VALUES (?,?,?,?,?,?,?,?)",
                            (n_n, n_u, n_srv, n_v.strftime('%Y-%m-%d'), n_c, n_m, n_w, l_b))
                c_in.commit(); st.rerun()

with tab3:
    st.subheader("🚨 COBRANÇA")
    pix = "62.326.879/0001-13"
    if not df.empty:
        df_cob = df[df['dias_res'] <= 3].copy()
        for _, c in df_cob.iterrows():
            t_v = "venceu" if c['dias_res'] < 0 else "vence hoje" if c['dias_res'] == 0 else f"vence em {c['dias_res']} dias"
            msg = f"Olá {str(c['nome']).split()[0]}! 👋 Sua assinatura {c['servidor']} {t_v}. Pix: {pix}"
            st.link_button(f"📲 COBRAR {c['nome']}", f"https://wa.me/55{c['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ AJUSTES E MANUTENÇÃO")
    c_limp1, c_limp2 = st.columns(2)
    
    with c_limp1:
        st.markdown("### 🧹 Limpeza Profunda")
        if st.button("🗑️ REMOVER REGISTROS INVÁLIDOS", use_container_width=True):
            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("DELETE FROM clientes WHERE nome IS NULL OR nome = '' OR nome = 'None' OR nome = 'nan'")
            conn.commit(); conn.close(); st.success("Registros fantasmas removidos!"); st.rerun()

        if st.button("🚨 RESET TOTAL DO BANCO", type="primary", use_container_width=True):
            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("DELETE FROM clientes")
            conn.commit(); conn.close(); st.success("Tudo apagado com sucesso!"); st.rerun()

    with c_limp2:
        st.markdown("### 📥 Importação Blindada")
        f_up = st.file_uploader("Subir Excel corrigido", type=["xlsx"])
        if f_up and st.button("🚀 IMPORTAR AGORA"):
            try:
                imp = pd.read_excel(f_up, engine='openpyxl')
                imp.columns = [str(c).strip().upper() for c in imp.columns]
                imp = imp.dropna(how='all')

                mapeamento = {
                    'CLIENTE': 'nome', 'USUÁRIO': 'usuario', 'SENHA': 'senha',
                    'SERVIDOR': 'servidor', 'VENCIMENTO': 'vencimento',
                    'CUSTO': 'custo', 'VALOR COBRADO': 'mensalidade', 'WHATSAPP': 'whatsapp'
                }
                imp = imp.rename(columns=mapeamento)
                
                # Tratamento correto da coluna 'nome' (USO DO .STR)
                if 'nome' in imp.columns:
                    imp['nome'] = imp['nome'].astype(str).str.strip()
                    imp = imp[
                        (imp['nome'].notnull()) & 
                        (imp['nome'].str.lower() != 'none') & 
                        (imp['nome'].str.lower() != 'nan') & 
                        (imp['nome'] != '')
                    ]
                
                cols_banco = ['nome', 'usuario', 'senha', 'servidor', 'vencimento', 'custo', 'mensalidade', 'whatsapp']
                for c in cols_banco:
                    if c not in imp.columns: imp[c] = None
                
                df_final = imp[cols_banco]
                if not df_final.empty:
                    conn = sqlite3.connect('supertv_gestao.db')
                    df_final.to_sql('clientes', conn, if_exists='append', index=False)
                    conn.close(); st.success(f"✅ {len(df_final)} Clientes importados!"); st.rerun()
                else:
                    st.warning("Nenhum dado válido com nome encontrado no Excel.")
            except Exception as e: st.error(f"Erro na Importação: {e}")
