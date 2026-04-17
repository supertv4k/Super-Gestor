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

# --- 6. DASHBOARD (CÁLCULO SEGURO) ---
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
    st.subheader("🔍 Filtros Rápidos")
    c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
    if 'filtro_atual' not in st.session_state: st.session_state.filtro_atual = "Todos"
    if c_btn1.button("👥 Todos", use_container_width=True): st.session_state.filtro_atual = "Todos"
    if c_btn2.button("🔴 Vencidos", use_container_width=True): st.session_state.filtro_atual = "Vencidos"
    if c_btn3.button("🟡 A Vencer (3d)", use_container_width=True): st.session_state.filtro_atual = "A Vencer"
    if c_btn4.button("🟢 Ativos", use_container_width=True): st.session_state.filtro_atual = "Ativos"

    busca = st.text_input("🔎 Pesquisar por Nome ou Usuário...", placeholder="Digite aqui...")

    if not df.empty:
        df_f = df.copy()
        if st.session_state.filtro_atual == "Vencidos": df_f = df_f[df_f['dias_res'] < 0]
        elif st.session_state.filtro_atual == "A Vencer": df_f = df_f[(df_f['dias_res'] >= 0) & (df_f['dias_res'] <= 3)]
        elif st.session_state.filtro_atual == "Ativos": df_f = df_f[df_f['dias_res'] >= 0]
        
        if busca:
            df_f = df_f[df_f['nome'].str.contains(busca, case=False, na=False) | df_f['usuario'].str.contains(busca, case=False, na=False)]

        for _, r in df_f.sort_values(by='dias_res').iterrows():
            nome_display = str(r['nome']).upper() if pd.notnull(r['nome']) else "CLIENTE SEM NOME"
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

            with st.expander("⚙️ EDITAR / EXCLUIR"):
                with st.form(key=f"ed_{r['id']}"):
                    c_ed1, c_ed2 = st.columns(2)
                    en = c_ed1.text_input("NOME", value=r['nome'])
                    eu = c_ed2.text_input("USUÁRIO", value=r['usuario'])
                    esrv = c_ed1.selectbox("SERVIDOR", get_servidores(), key=f"srv_{r['id']}")
                    evd = c_ed2.date_input("VENCIMENTO", value=pd.to_datetime(r['vencimento']).date() if pd.notnull(r['vencimento']) else hoje)
                    ew = c_ed1.text_input("WHATSAPP", value=r['whatsapp'])
                    
                    b_salvar, b_excluir = st.columns(2)
                    if b_salvar.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                        c_up = sqlite3.connect('supertv_gestao.db')
                        c_up.execute("UPDATE clientes SET nome=?, usuario=?, servidor=?, vencimento=?, whatsapp=? WHERE id=?", 
                                     (en, eu, esrv, evd.strftime('%Y-%m-%d %H:%M:%S'), ew, r['id']))
                        c_up.commit(); st.rerun()
                    
                    confirmar = st.checkbox("Confirmar exclusão?", key=f"check_{r['id']}")
                    if b_excluir.form_submit_button("🗑️ EXCLUIR CLIENTE", type="primary"):
                        if confirmar:
                            c_del = sqlite3.connect('supertv_gestao.db')
                            c_del.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                            c_del.commit(); st.rerun()
                        else:
                            st.warning("Marque a caixa acima para confirmar.")

with tab2:
    st.subheader("🚀 Novo Cliente")
    with st.form("add"):
        n_n = st.text_input("NOME DO CLIENTE")
        n_u = st.text_input("USUÁRIO")
        n_srv = st.selectbox("SERVIDOR", get_servidores())
        n_v = st.date_input("VENCIMENTO", value=datetime.now()+timedelta(days=30))
        n_c = st.number_input("CUSTO", value=10.0)
        n_m = st.number_input("VALOR COBRADO", value=35.0)
        n_w = st.text_input("WHATSAPP (Ex: 62999999999)")
        n_l = st.file_uploader("LOGOMARCA", type=['png','jpg'])
        if st.form_submit_button("🚀 CADASTRAR"):
            l_b = image_to_base64(n_l)
            c_in = sqlite3.connect('supertv_gestao.db')
            c_in.execute("INSERT INTO clientes (nome, usuario, servidor, vencimento, custo, mensalidade, whatsapp, logo_blob) VALUES (?,?,?,?,?,?,?,?)",
                        (n_n, n_u, n_srv, n_v.strftime('%Y-%m-%d %H:%M:%S'), n_c, n_m, n_w, l_b))
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
    st.subheader("⚙️ AJUSTES")
    col_aj1, col_aj2 = st.columns(2)
    with col_aj1:
        st.markdown("### 🖥️ Servidores")
        ns = st.text_input("NOVO SERVIDOR")
        if st.button("SALVAR SERVIDOR"):
            sqlite3.connect('supertv_gestao.db').execute("INSERT INTO lista_servidores (nome) VALUES (?)", (ns.upper(),)).connection.commit(); st.rerun()
        
        st.divider()
        st.markdown("### 🧹 Limpeza")
        if st.button("🗑️ REMOVER DUPLICADOS (NOME/USER)", use_container_width=True):
            conn_limpa = sqlite3.connect('supertv_gestao.db')
            conn_limpa.execute("DELETE FROM clientes WHERE id NOT IN (SELECT MAX(id) FROM clientes GROUP BY nome, usuario)")
            conn_limpa.commit(); conn_limpa.close(); st.success("Limpo!"); st.rerun()
    
    with col_aj2:
        st.markdown("### 📥 Importação sob Medida")
        f_up = st.file_uploader("Excel .xlsx", type=["xlsx"])
        if f_up and st.button("🚀 IMPORTAR E FILTRAR NOVO"):
            try:
                imp = pd.read_excel(f_up, engine='openpyxl').dropna(how='all')
                mapeamento = {
                    'CLIENTE': 'nome', 'USUÁRIO': 'usuario', 'SENHA': 'senha',
                    'SERVIDOR': 'servidor', 'SISTEMA': 'sistema', 'VENCIMENTO': 'vencimento',
                    'CUSTO': 'custo', 'VALOR COBRADO': 'mensalidade', 'INÍCIOU DIA': 'inicio',
                    'WHATSAPP': 'whatsapp', 'OBSERVAÇÃO': 'observacao'
                }
                imp = imp.rename(columns=mapeamento)
                cols_banco = ['nome', 'usuario', 'senha', 'servidor', 'sistema', 'vencimento', 'custo', 'mensalidade', 'inicio', 'whatsapp', 'observacao']
                for c in cols_banco:
                    if c not in imp.columns: imp[c] = None
                df_final = imp[cols_banco]
                
                conn = sqlite3.connect('supertv_gestao.db')
                atual = pd.read_sql_query("SELECT usuario FROM clientes", conn)
                df_filtrado = df_final[~df_final['usuario'].astype(str).isin(atual['usuario'].tolist())]
                
                if not df_filtrado.empty:
                    df_filtrado.to_sql('clientes', conn, if_exists='append', index=False)
                    st.success(f"✅ {len(df_filtrado)} Novos Adicionados!")
                else: st.warning("Nenhum dado novo encontrado.")
                conn.close(); st.rerun()
            except Exception as e: st.error(f"Erro: {e}")
    
    st.divider()
    if not df.empty:
        out = io.BytesIO()
        df.drop(columns=['logo_blob', 'dt_venc_calc', 'dias_res'], errors='ignore').to_excel(out, index=False, engine='xlsxwriter')
        st.download_button("📥 BAIXAR BACKUP EXCEL", out.getvalue(), "backup.xlsx", use_container_width=True)
