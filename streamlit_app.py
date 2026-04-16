import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta, time
import urllib.parse
import io
import base64
import time as t_lib

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    
    .cliente-row {
        background-color: #161b22; border: 1px solid #30363d; border-radius: 12px;
        padding: 15px; margin-bottom: 0px; display: flex; align-items: center; gap: 20px;
    }
    .logo-externa {
        width: 85px; height: 85px; border-radius: 10px;
        object-fit: contain; background: #21262d; border: 1px solid #444;
    }
    .info-container { flex-grow: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .info-txt { font-size: 14px; color: #c9d1d9; }
    .destaque-vermelho { color: #ff4b4b; font-weight: bold; }
    .destaque-verde { color: #00ff00; font-weight: bold; }
    
    /* Estilo do botão de edição para parecer parte do card */
    .stExpander { border: none !important; background-color: #161b22 !important; margin-bottom: 15px !important; border-radius: 0 0 12px 12px !important; }
    
    .metric-card { 
        background-color: #161b22; padding: 15px; border-radius: 12px; 
        text-align: center; border: 1px solid #30363d; margin-bottom: 10px; 
    }
    .metric-label { font-size: 11px; font-weight: bold; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 20px; font-weight: bold; color: #ff0000; margin-top: 5px; }

    div.stFormSubmitButton > button {
        background: linear-gradient(135deg, #0052D4 0%, #929ED1 50%, #E0EAFC 100%) !important;
        color: #1e1e1e !important; font-weight: 900 !important; border-radius: 10px !important;
        width: 100%; height: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES ---
def image_to_base64(image_file):
    if image_file is not None:
        try:
            return base64.b64encode(image_file.read()).decode()
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

# --- 6. DASHBOARD (MÉTRICAS) ---
if not df.empty:
    hoje_dt = datetime.now()
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').fillna(hoje_dt)
    df['dias_res'] = (df['dt_venc_calc'].dt.date - hoje_dt.date()).apply(lambda x: x.days)
    
    bruto = pd.to_numeric(df['mensalidade'], errors='coerce').fillna(0).sum()
    custos = pd.to_numeric(df['custo'], errors='coerce').fillna(0).sum()
    liquido = bruto - custos

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value">{len(df[df["dias_res"] < 0])}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">VENCENDO</div><div class="metric-value">{len(df[(df["dias_res"] >= 0) & (df["dias_res"] <= 3)])}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">BRUTO</div><div class="metric-value">R${bruto:,.0f}</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-label">LÍQUIDO</div><div class="metric-value">R${liquido:,.0f}</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="metric-card"><div class="metric-label">CUSTO</div><div class="metric-value">R${custos:,.0f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 7. ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADD CLIENTE", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔎 Pesquisar...", placeholder="Digite nome ou usuário...")
    if not df.empty:
        df_f = df.copy()
        if busca:
            df_f = df_f[df_f['nome'].astype(str).str.contains(busca, case=False, na=False) | df_f['usuario'].astype(str).str.contains(busca, case=False, na=False)]

        for _, r in df_f.sort_values(by='dias_res').iterrows():
            status_cor = "destaque-verde" if r['dias_res'] >= 0 else "destaque-vermelho"
            dias_txt = f"{r['dias_res']} DIAS" if r['dias_res'] >= 0 else "VENCIDO"
            img_data = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
            
            # Card Visual
            st.markdown(f"""<div class="cliente-row"><img src="{img_data}" class="logo-externa"><div class="info-container">
                    <div class="info-txt">👤 <b>CLIENTE:</b> {str(r['nome']).upper()}</div>
                    <div class="info-txt">📅 <b>STATUS:</b> <span class="{status_cor}">{dias_txt}</span></div>
                    <div class="info-txt">🔑 <b>USER:</b> {r['usuario']}</div>
                    <div class="info-txt">📶 <b>SERVIDOR:</b> {r['servidor']} ({r['sistema']})</div>
                </div></div>""", unsafe_allow_html=True)
            
            # PAINEL DE EDIÇÃO CLICÁVEL
            with st.expander("⚙️ ABRIR PAINEL DE EDIÇÃO"):
                with st.form(key=f"edit_{r['id']}"):
                    c1, c2 = st.columns(2)
                    en = c1.text_input("NOME", value=r['nome'])
                    ew = c2.text_input("WHATSAPP", value=r['whatsapp'])
                    eu = c1.text_input("USUÁRIO", value=r['usuario'])
                    es = c2.text_input("SENHA", value=r['senha'])
                    
                    try: dv = pd.to_datetime(r['vencimento']).date()
                    except: dv = datetime.now().date()
                    
                    ev = c1.date_input("VENCIMENTO", value=dv)
                    esrv = c2.selectbox("SERVIDOR", get_servidores(), index=0)
                    esis = c1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if r['sistema']=="P2P" else 1)
                    ec = c2.number_input("CUSTO", value=float(r['custo'] if r['custo'] else 0))
                    evlr = c1.number_input("VALOR COBRADO", value=float(r['mensalidade'] if r['mensalidade'] else 0))
                    elogo = st.file_uploader("TROCAR LOGO", type=['png','jpg','jpeg'], key=f"l_{r['id']}")
                    
                    b1, b2 = st.columns(2)
                    if b1.form_submit_button("💾 SALVAR"):
                        l_final = image_to_base64(elogo) if elogo else r['logo_blob']
                        v_final = datetime.combine(ev, time(12,0)).strftime('%Y-%m-%d %H:%M:%S')
                        conn_up = sqlite3.connect('supertv_gestao.db')
                        conn_up.execute("UPDATE clientes SET nome=?, whatsapp=?, usuario=?, senha=?, servidor=?, sistema=?, vencimento=?, custo=?, mensalidade=?, logo_blob=? WHERE id=?", 
                                     (en, ew, eu, es, esrv, esis, v_final, ec, evlr, l_final, r['id']))
                        conn_up.commit(); conn_up.close(); st.rerun()
                    if b2.form_submit_button("🗑️ EXCLUIR"):
                        conn_del = sqlite3.connect('supertv_gestao.db')
                        conn_del.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                        conn_del.commit(); conn_del.close(); st.rerun()

with tab2:
    st.subheader("🚀 Novo Cadastro")
    with st.form("add"):
        c1, c2 = st.columns(2)
        n_nome = c1.text_input("CLIENTE")
        n_zap = c2.text_input("WHATSAPP")
        n_user = c1.text_input("USUÁRIO")
        n_senha = c2.text_input("SENHA")
        n_serv = c1.selectbox("SERVIDOR", get_servidores())
        n_venc = c2.date_input("VENCIMENTO", value=datetime.now()+timedelta(days=30))
        n_logo = st.file_uploader("LOGOMARCA", type=['png','jpg','jpeg'])
        if st.form_submit_button("🚀 CADASTRAR"):
            l_b = image_to_base64(n_logo)
            vf = datetime.combine(n_venc, time(12,0)).strftime('%Y-%m-%d %H:%M:%S')
            conn_in = sqlite3.connect('supertv_gestao.db')
            conn_in.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, vencimento, logo_blob) VALUES (?,?,?,?,?,?,?)", (n_nome, n_zap, n_user, n_senha, n_serv, vf, l_b))
            conn_in.commit(); conn_in.close(); st.rerun()

with tab4:
    st.subheader("⚙️ AJUSTES")
    # NOVO SERVIDOR
    ns = st.text_input("Novo Nome de Servidor")
    if st.button("Salvar Servidor"):
        if ns:
            conn_s = sqlite3.connect('supertv_gestao.db')
            conn_s.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (ns.upper(),))
            conn_s.commit(); conn_s.close(); st.rerun()

    st.divider()
    # BACKUP EXCEL
    if not df.empty:
        st.markdown("### 📤 Exportar Backup")
        output = io.BytesIO()
        df_export = df.drop(columns=['logo_blob', 'dt_venc_calc', 'dias_res'], errors='ignore')
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False)
        st.download_button("📥 BAIXAR EXCEL AGORA", data=output.getvalue(), file_name="backup_clientes.xlsx")

    st.divider()
    # IMPORTAÇÃO
    st.markdown("### 📥 Importar Planilha")
    f_up = st.file_uploader("Upload .xlsx", type=["xlsx"])
    if f_up and st.button("🚀 PROCESSAR"):
        try:
            df_imp = pd.read_excel(f_up)
            df_imp.columns = [str(c).strip().upper() for c in df_imp.columns]
            mapeamento = {'nome': 'CLIENTE', 'usuario': 'USUÁRIO', 'senha': 'SENHA', 'servidor': 'SERVIDOR', 'vencimento': 'VENCIMENTO', 'whatsapp': 'WHATSAPP'}
            df_final = pd.DataFrame()
            for col_db, col_excel in mapeamento.items():
                if col_excel in df_imp.columns: df_final[col_db] = df_imp[col_excel]
                else: df_final[col_db] = ""
            df_final['vencimento'] = pd.to_datetime(df_final['vencimento'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
            conn_imp = sqlite3.connect('supertv_gestao.db')
            df_final.to_sql('clientes', conn_imp, if_exists='append', index=False)
            conn_imp.close(); st.success("Importado!"); t_lib.sleep(1); st.rerun()
        except Exception as e: st.error(f"Erro: {e}")

    if st.button("🗑️ LIMPAR TUDO"):
        conn_c = sqlite3.connect('supertv_gestao.db')
        conn_c.execute("DELETE FROM clientes")
        conn_c.commit(); conn_c.close(); st.rerun()
