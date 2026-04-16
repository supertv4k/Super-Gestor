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
    
    .metric-card { 
        background-color: #161b22; padding: 15px; border-radius: 12px; 
        text-align: center; border: 1px solid #30363d; margin-bottom: 10px; 
    }
    .metric-label { font-size: 11px; font-weight: bold; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 22px; font-weight: bold; color: #ff0000; margin-top: 5px; }

    div.stFormSubmitButton > button {
        background: linear-gradient(135deg, #0052D4 0%, #929ED1 50%, #E0EAFC 100%) !important;
        color: #1e1e1e !important; font-weight: 900 !important; border-radius: 10px !important;
        width: 100%; height: 50px;
    }
    
    .stExpander > details > summary { 
        background-color: #161b22 !important; 
        color: #ffffff !important; padding: 10px !important; border-radius: 10px !important; 
        border: 1px solid #30363d !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES AUXILIARES ---
def image_to_base64(image_file):
    if image_file is not None:
        try:
            return base64.b64encode(image_file.read()).decode()
        except:
            return None
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
    
    cursor = c.execute('PRAGMA table_info(clientes)')
    cols = [col[1] for col in cursor.fetchall()]
    if 'logo_blob' not in cols:
        c.execute('ALTER TABLE clientes ADD COLUMN logo_blob TEXT')
    conn.commit()
    conn.close()

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    try:
        lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    except: lista = []
    conn.close()
    return lista if lista else ["UNITV", "UNIPLAY", "P2BRAZ", "MUNDOGF", "PLAY TV"]

init_db()

# --- 4. CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

if 'selecionados' not in st.session_state: st.session_state.selecionados = []

# --- 5. HEADER ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

# --- 6. DASHBOARD ---
if not df.empty:
    hoje = datetime.now()
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce')
    df['dias_res'] = (df['dt_venc_calc'].dt.date - hoje.date()).apply(lambda x: x.days if pd.notnull(x) else 0)
    
    bruto = df['mensalidade'].sum()
    custos = df['custo'].sum()
    liquido = bruto - custos
    
    c1, c2, c3 = st.columns(3); c4, c5, c6 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL CLIENTES</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value">{len(df[df["dias_res"] < 0])}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">VENCEM EM 3 DIAS</div><div class="metric-value">{len(df[(df["dias_res"] >= 0) & (df["dias_res"] <= 3)])}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO BRUTO</div><div class="metric-value">R$ {bruto:,.2f}</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO LÍQUIDO</div><div class="metric-value">R$ {liquido:,.2f}</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="metric-card"><div class="metric-label">CUSTO CRÉDITOS</div><div class="metric-value">R$ {custos:,.2f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 7. ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADD CLIENTE", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔍 PESQUISAR POR NOME OU USUÁRIO")
    if not df.empty:
        for _, r in df.sort_values(by='nome').iterrows():
            if busca.lower() in r['nome'].lower() or busca.lower() in str(r['usuario']).lower():
                try:
                    dt_v = datetime.strptime(r['vencimento'], '%Y-%m-%d %H:%M:%S')
                    d_txt = f"{r['dias_res']} DIAS" if r['dias_res'] >= 0 else "VENCIDO"
                except: 
                    dt_v = datetime.now()
                    d_txt = "DATA INVÁLIDA"
                
                status_ico = "🟢" if r['dias_res'] >= 0 else "🔴"
                titulo = f"{status_ico} {r['servidor']} | {r['nome'].upper()} | {d_txt}"

                with st.expander(titulo):
                    c_logo, c_info = st.columns([1, 3])
                    with c_logo:
                        img_data = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
                        st.image(img_data, width=100)
                    with c_info:
                        st.markdown(f"""
                        **CLIENTE:** {r['nome'].upper()} | **VENCE EM:** {d_txt}  
                        **USUÁRIO:** `{r['usuario']}` | **SENHA:** `{r['senha']}`  
                        **SERVIDOR:** {r['servidor']} | **SISTEMA:** {r['sistema']}
                        """)
                    st.divider()
                    with st.form(key=f"ed_{r['id']}"):
                        en = st.text_input("NOME", value=r['nome'])
                        eu = st.text_input("USUÁRIO", value=r['usuario'])
                        es = st.text_input("SENHA", value=r['senha'])
                        esrv = st.selectbox("SERVIDOR", get_servidores(), key=f"srv_{r['id']}")
                        esis = st.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if r['sistema']=="P2P" else 1)
                        cv1, cv2 = st.columns(2)
                        evd = cv1.date_input("DATA VENC.", value=dt_v.date(), format="DD/MM/YYYY", key=f"dv_{r['id']}")
                        evh = cv2.time_input("HORA VENC.", value=dt_v.time(), key=f"hv_{r['id']}")
                        ew = st.text_input("WHATSAPP", value=r['whatsapp'])
                        e_img = st.file_uploader("TROCAR LOGO", type=['png','jpg','jpeg'], key=f"img_ed_{r['id']}")
                        cb1, cb2 = st.columns(2)
                        if cb1.form_submit_button("💾 SALVAR"):
                            vf = datetime.combine(evd, evh).strftime('%Y-%m-%d %H:%M:%S')
                            l_f = image_to_base64(e_img) if e_img else r['logo_blob']
                            conn_ed = sqlite3.connect('supertv_gestao.db')
                            conn_ed.execute("UPDATE clientes SET nome=?, usuario=?, senha=?, servidor=?, sistema=?, vencimento=?, whatsapp=?, logo_blob=? WHERE id=?", 
                                         (en, eu, es, esrv, esis, vf, ew, l_f, r['id']))
                            conn_ed.commit(); st.rerun()
                        if cb2.form_submit_button("🗑️ EXCLUIR"):
                            conn_del = sqlite3.connect('supertv_gestao.db')
                            conn_del.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                            conn_del.commit(); st.rerun()

with tab2:
    st.subheader("🚀 Cadastrar Novo Cliente")
    with st.form("add_cliente", clear_on_submit=True):
        n_nome = st.text_input("NOME DO CLIENTE")
        n_user = st.text_input("USUÁRIO")
        n_pass = st.text_input("SENHA")
        n_serv = st.selectbox("SERVIDOR", get_servidores())
        n_sist = st.selectbox("SISTEMA", ["P2P", "IPTV"])
        c1, c2 = st.columns(2)
        n_dv = c1.date_input("DIA VENCIMENTO", value=datetime.now()+timedelta(days=30), format="DD/MM/YYYY")
        n_hv = c2.time_input("HORA VENCIMENTO", value=time(12,0))
        n_custo = st.number_input("CUSTO", value=10.0)
        n_mensal = st.number_input("VALOR COBRADO", value=35.0)
        n_whats = st.text_input("WHATSAPP")
        n_logo = st.file_uploader("LOGOMARCA DO SERVIDOR", type=['png','jpg','jpeg'])
        if st.form_submit_button("🚀 CADASTRAR AGORA"):
            if n_nome and n_user:
                venc_f = datetime.combine(n_dv, n_hv).strftime('%Y-%m-%d %H:%M:%S')
                l_b64 = image_to_base64(n_logo)
                conn_add = sqlite3.connect('supertv_gestao.db')
                conn_add.execute("INSERT INTO clientes (nome, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, whatsapp, logo_blob) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                (n_nome, n_user, n_pass, n_serv, n_sist, venc_f, n_custo, n_mensal, n_whats, l_b64))
                conn_add.commit(); st.success("Cliente Cadastrado!"); st.rerun()

with tab3:
    st.subheader("🚨 CENTRAL DE COBRANÇA")
    pix = "62.326.879/0001-13"
    if not df.empty:
        # Pega clientes que vencem em 3 dias ou que já estão vencidos
        df_cob = df[df['dias_res'] <= 3].copy()
        for _, c in df_cob.iterrows():
            # CORREÇÃO DA MENSAGEM:
            texto_vencimento = "venceu" if c['dias_res'] < 0 else "vence"
            data_formatada = pd.to_datetime(c['vencimento']).strftime('%d/%m/%Y')
            
            msg = f"Olá {c['nome']}, sua assinatura {texto_vencimento} em {data_formatada}. Chave Pix: {pix}"
            
            st.link_button(f"📲 COBRAR {c['nome']} ({'VENCIDO' if c['dias_res'] < 0 else f'Faltam {c['dias_res']} dias'})", 
                           f"https://wa.me/55{c['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ AJUSTES")
    st.markdown("### 🖥️ Gerenciar Servidores")
    new_s = st.text_input("NOME DO NOVO SERVIDOR")
    if st.button("SALVAR SERVIDOR"):
        if new_s:
            conn_s = sqlite3.connect('supertv_gestao.db')
            conn_s.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (new_s.upper(),))
            conn_s.commit(); st.rerun()
    st.divider()
    st.markdown("### 📥 Importar Dados")
    f_up = st.file_uploader("Selecione um arquivo Excel para importar clientes", type=["xlsx"])
    if f_up:
        if st.button("🚀 PROCESSAR IMPORTAÇÃO"):
            try:
                df_imp = pd.read_excel(f_up)
                conn_imp = sqlite3.connect('supertv_gestao.db')
                df_imp.to_sql('clientes', conn_imp, if_exists='append', index=False)
                st.success("Dados importados com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao importar: {e}")
    st.divider()
    st.markdown("### 📤 Backup")
    if not df.empty:
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        st.download_button("📥 EXPORTAR EXCEL (BACKUP)", data=buf.getvalue(), file_name="clientes_supertv.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
