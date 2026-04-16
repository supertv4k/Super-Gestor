import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta, time
import urllib.parse
import io
import base64

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS (INTERFACE COMPLETA) ---
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
    
    .btn-container { display: flex; align-items: center; gap: 20px; width: 100%; }
    .srv-logo { width: 70px; height: 70px; border-radius: 12px; object-fit: contain; background: #21262d; border: 1px solid #444; }
    .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2px 30px; flex-grow: 1; }
    .info-item { font-size: 14px; color: #c9d1d9; }
    .label-red { color: #ff4b4b; font-weight: 800; }
    .label-white { color: #ffffff; font-weight: 700; }

    .stExpander > details > summary { 
        background: #161b22 !important; 
        color: #ffffff !important; padding: 12px !important; border-radius: 10px !important; 
        border: 1px solid #30363d !important;
    }
    .stExpander > details > summary:hover { border-color: #ff0000 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES AUXILIARES ---
def image_to_base64(image_file):
    if image_file is not None:
        return base64.b64encode(image_file.read()).decode()
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
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'])
    df['dias_res'] = (df['dt_venc_calc'].dt.date - hoje.date()).apply(lambda x: x.days)
    bruto, custos = df['mensalidade'].sum(), df['custo'].sum()
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
    busca = st.text_input("🔍 PESQUISAR")
    if not df.empty:
        for _, r in df.sort_values(by='nome').iterrows():
            if busca.lower() in r['nome'].lower() or busca.lower() in str(r['usuario']).lower():
                try:
                    dt_v = datetime.strptime(r['vencimento'], '%Y-%m-%d %H:%M:%S')
                    d_txt = f"{r['dias_res']} DIAS" if r['dias_res'] >= 0 else "VENCIDO"
                except: 
                    dt_v = datetime.now()
                    d_txt = "Erro Data"
                
                img_src = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
                status_ico = "🟢" if r['dias_res'] >= 0 else "🔴"

                html_exp = f"""
                <div class="btn-container">
                    <img src="{img_src}" class="srv-logo">
                    <div class="info-grid">
                        <div class="info-item">{status_ico} CLIENTE: <span class="label-red">{r['nome'].upper()}</span></div>
                        <div class="info-item">VENCE EM: <span class="label-red">{d_txt}</span></div>
                        <div class="info-item">USUÁRIO: <span class="label-white">{r['usuario']}</span></div>
                        <div class="info-item">SENHA: <span class="label-white">{r['senha']}</span></div>
                        <div class="info-item">SERVIDOR: {r['servidor']}</div>
                        <div class="info-item">SISTEMA: {r['sistema']}</div>
                    </div>
                </div>
                """
                with st.expander(html_exp):
                    with st.form(key=f"ed_{r['id']}"):
                        en = st.text_input("CLIENTE", value=r['nome'])
                        eu = st.text_input("USUÁRIO", value=r['usuario'])
                        es = st.text_input("SENHA", value=r['senha'])
                        esrv = st.selectbox("SERVIDOR", get_servidores(), index=0)
                        esis = st.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if r['sistema']=="P2P" else 1)
                        c_vd, c_vh = st.columns(2)
                        ev_d = c_vd.date_input("DATA VENC.", value=dt_v.date(), format="DD/MM/YYYY", key=f"d_{r['id']}")
                        ev_h = c_vh.time_input("HORA VENC.", value=dt_v.time(), key=f"t_{r['id']}")
                        ec = st.number_input("CUSTO", value=float(r['custo'] or 0.0))
                        em = st.number_input("VALOR COBRADO", value=float(r['mensalidade'] or 0.0))
                        try: dt_i = datetime.strptime(r['inicio'], '%Y-%m-%d %H:%M:%S')
                        except: dt_i = datetime.now()
                        c_id, c_ih = st.columns(2)
                        ei_d = c_id.date_input("DATA INÍCIO", value=dt_i.date(), format="DD/MM/YYYY", key=f"id_{r['id']}")
                        ei_h = c_ih.time_input("HORA INÍCIO", value=dt_i.time(), key=f"ih_{r['id']}")
                        ew = st.text_input("WHATSAPP", value=r['whatsapp'])
                        e_img = st.file_uploader("TROCAR LOGO", type=['png','jpg','jpeg'], key=f"img_{r['id']}")
                        eobs = st.text_area("OBSERVAÇÃO", value=r['observacao'] or "")
                        col_b1, col_b2 = st.columns(2)
                        if col_b1.form_submit_button("💾 SALVAR"):
                            vf = datetime.combine(ev_d, ev_h).strftime('%Y-%m-%d %H:%M:%S')
                            ini_f = datetime.combine(ei_d, ei_h).strftime('%Y-%m-%d %H:%M:%S')
                            l_f = image_to_base64(e_img) if e_img else r['logo_blob']
                            c = sqlite3.connect('supertv_gestao.db')
                            c.execute("UPDATE clientes SET nome=?, usuario=?, senha=?, servidor=?, sistema=?, vencimento=?, custo=?, mensalidade=?, inicio=?, whatsapp=?, observacao=?, logo_blob=? WHERE id=?", 
                                     (en, eu, es, esrv, esis, vf, ec, em, ini_f, ew, eobs, l_f, r['id']))
                            c.commit(); st.rerun()
                        if col_b2.form_submit_button("🗑️ EXCLUIR"):
                            c = sqlite3.connect('supertv_gestao.db')
                            c.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                            c.commit(); st.rerun()

with tab2:
    st.subheader("🚀 Cadastro de Novo Assinante")
    with st.form("form_novo", clear_on_submit=True):
        n_cliente = st.text_input("CLIENTE")
        n_usuario = st.text_input("USUÁRIO")
        n_senha = st.text_input("SENHA")
        n_servidor = st.selectbox("SERVIDOR", get_servidores())
        n_sistema = st.selectbox("SISTEMA", ["P2P", "IPTV"])
        st.write("📅 **VENCIMENTO**")
        cv1, cv2 = st.columns(2)
        n_vd = cv1.date_input("DATA VENCIMENTO", value=datetime.now() + timedelta(days=30), format="DD/MM/YYYY")
        n_vh = cv2.time_input("HORA VENCIMENTO", value=time(12, 0))
        n_custo = st.number_input("CUSTO", value=10.0)
        n_valor = st.number_input("VALOR COBRADO", value=35.0)
        st.write("📅 **INÍCIO**")
        ci1, ci2 = st.columns(2)
        n_id = ci1.date_input("DATA INÍCIO", value=datetime.now().date(), format="DD/MM/YYYY")
        n_ih = ci2.time_input("HORA INÍCIO", value=datetime.now().time())
        n_whatsapp = st.text_input("WHATSAPP")
        n_logo_file = st.file_uploader("Logo do Servidor (Imagem)", type=['png', 'jpg', 'jpeg'])
        n_obs = st.text_area("OBSERVAÇÃO")
        if st.form_submit_button("🚀 CADASTRAR AGORA"):
            if n_cliente and n_usuario:
                v_s = datetime.combine(n_vd, n_vh).strftime('%Y-%m-%d %H:%M:%S')
                i_s = datetime.combine(n_id, n_ih).strftime('%Y-%m-%d %H:%M:%S')
                l_b = image_to_base64(n_logo_file)
                conn = sqlite3.connect('supertv_gestao.db')
                conn.execute("INSERT INTO clientes (nome, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, inicio, whatsapp, observacao, logo_blob) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", 
                            (n_cliente, n_usuario, n_senha, n_servidor, n_sistema, v_s, n_custo, n_valor, i_s, n_whatsapp, n_obs, l_b))
                conn.commit(); conn.close(); st.success("Cadastrado!"); st.rerun()

with tab3:
    st.subheader("🚨 CENTRAL DE COBRANÇA")
    pix = "62.326.879/0001-13"
    if not df.empty:
        df_av = df[df['dias_res'] <= 3].copy()
        col_s1, col_s2 = st.columns(2)
        if col_s1.button("✅ SELECIONAR TODOS"): st.session_state.selecionados = df_av['id'].tolist(); st.rerun()
        if col_s2.button("❌ LIMPAR SELEÇÃO"): st.session_state.selecionados = []; st.rerun()
        for _, cl in df_av.iterrows():
            check = st.checkbox(f"🔔 {cl['nome']} | {cl['dias_res']} DIAS", value=(cl['id'] in st.session_state.selecionados), key=f"cob_{cl['id']}")
            if check and cl['id'] not in st.session_state.selecionados: st.session_state.selecionados.append(cl['id'])
            elif not check and cl['id'] in st.session_state.selecionados: st.session_state.selecionados.remove(cl['id'])
        if st.session_state.selecionados:
            st.divider()
            for sid in st.session_state.selecionados:
                c_dt = df[df['id'] == sid].iloc[0]
                msg = f"Olá {c_dt['nome']}! Sua assinatura Supertv4k vence em {pd.to_datetime(c_dt['vencimento']).strftime('%d/%m/%Y')}. Renove via Pix: {pix}"
                st.link_button(f"ENVIAR PARA {c_dt['nome']}", f"https://wa.me/55{c_dt['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ AJUSTES")
    ns = st.text_input("NOVO SERVIDOR")
    if st.button("SALVAR SERVIDOR"):
        if ns:
            c = sqlite3.connect('supertv_gestao.db'); c.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (ns.upper(),)); c.commit(); st.rerun()
    st.divider()
    f_up = st.file_uploader("IMPORTAR EXCEL", type=["xlsx"])
    if f_up and st.button("PROCESSAR IMPORTAÇÃO"):
        try:
            pd.read_excel(f_up).to_sql('clientes', sqlite3.connect('supertv_gestao.db'), if_exists='append', index=False)
            st.success("Sucesso!"); st.rerun()
        except Exception as e: st.error(f"Erro: {e}")
    st.divider()
    if not df.empty:
        tow = io.BytesIO(); df.to_excel(tow, index=False)
        st.download_button("📥 BACKUP EXCEL", data=tow.getvalue(), file_name="backup_supertv.xlsx")
