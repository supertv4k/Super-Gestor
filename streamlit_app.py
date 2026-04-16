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
    
    /* Card do Cliente na Lista */
    .cliente-row {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .logo-externa {
        width: 85px;
        height: 85px;
        border-radius: 10px;
        object-fit: contain;
        background: #21262d;
        border: 1px solid #444;
    }
    .info-container {
        flex-grow: 1;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
    }
    .info-txt { font-size: 14px; color: #c9d1d9; }
    .destaque-vermelho { color: #ff4b4b; font-weight: bold; }
    .destaque-verde { color: #00ff00; font-weight: bold; }
    
    /* Métricas */
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
    .stExpander { border: none !important; background: transparent !important; margin-top: -10px !important; }
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

# --- 6. DASHBOARD COMPLETO ---
if not df.empty:
    hoje = datetime.now()
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce')
    df['dias_res'] = (df['dt_venc_calc'].dt.date - hoje.date()).apply(lambda x: x.days if pd.notnull(x) else 0)
    
    bruto, custos = df['mensalidade'].sum(), df['custo'].sum()
    liquido = bruto - custos
    vencidos = len(df[df["dias_res"] < 0])
    vencendo_3 = len(df[(df["dias_res"] >= 0) & (df["dias_res"] <= 3)])

    c1, c2, c3 = st.columns(3); c4, c5, c6 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL CLIENTES</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value">{vencidos}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">VENCEM EM 3 DIAS</div><div class="metric-value">{vencendo_3}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO BRUTO</div><div class="metric-value">R$ {bruto:,.2f}</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO LÍQUIDO</div><div class="metric-value">R$ {liquido:,.2f}</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="metric-card"><div class="metric-label">CUSTO CRÉDITOS</div><div class="metric-value">R$ {custos:,.2f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 7. ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADD CLIENTE", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    st.subheader("🔍 Filtros Rápidos")
    
    # Botões de Filtro
    c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
    if 'filtro_atual' not in st.session_state: st.session_state.filtro_atual = "Todos"

    if c_btn1.button("👥 Todos", use_container_width=True): st.session_state.filtro_atual = "Todos"
    if c_btn2.button("🔴 Vencidos", use_container_width=True): st.session_state.filtro_atual = "Vencidos"
    if c_btn3.button("🟡 A Vencer (3d)", use_container_width=True): st.session_state.filtro_atual = "A Vencer"
    if c_btn4.button("🟢 Ativos", use_container_width=True): st.session_state.filtro_atual = "Ativos"

    st.markdown(f"**Filtro Ativo:** `{st.session_state.filtro_atual}`")
    busca = st.text_input("🔎 Pesquisar por Nome ou Usuário...", placeholder="Digite aqui...")

    if not df.empty:
        df_f = df.copy()
        if st.session_state.filtro_atual == "Vencidos": df_f = df_f[df_f['dias_res'] < 0]
        elif st.session_state.filtro_atual == "A Vencer": df_f = df_f[(df_f['dias_res'] >= 0) & (df_f['dias_res'] <= 3)]
        elif st.session_state.filtro_atual == "Ativos": df_f = df_f[df_f['dias_res'] >= 0]
        
        if busca:
            df_f = df_f[df_f['nome'].str.contains(busca, case=False, na=False) | df_f['usuario'].str.contains(busca, case=False, na=False)]

        for _, r in df_f.sort_values(by='dias_res').iterrows():
            dt_v = pd.to_datetime(r['vencimento'])
            status_cor = "destaque-verde" if r['dias_res'] >= 0 else "destaque-vermelho"
            dias_txt = f"{r['dias_res']} DIAS" if r['dias_res'] >= 0 else "VENCIDO"
            img_data = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"

            st.markdown(f"""
            <div class="cliente-row">
                <img src="{img_data}" class="logo-externa">
                <div class="info-container">
                    <div class="info-txt">👤 <b>CLIENTE:</b> {r['nome'].upper()}</div>
                    <div class="info-txt">📅 <b>STATUS:</b> <span class="{status_cor}">{dias_txt}</span></div>
                    <div class="info-txt">🔑 <b>USER:</b> {r['usuario']}</div>
                    <div class="info-txt">📶 <b>SISTEMA:</b> {r['servidor']} ({r['sistema']})</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("⚙️ CLIQUE PARA EDITAR"):
                with st.form(key=f"ed_{r['id']}"):
                    c_ed1, c_ed2 = st.columns(2)
                    en = c_ed1.text_input("NOME", value=r['nome'])
                    eu = c_ed2.text_input("USUÁRIO", value=r['usuario'])
                    es = c_ed1.text_input("SENHA", value=r['senha'])
                    esrv = c_ed2.selectbox("SERVIDOR", get_servidores(), key=f"srv_{r['id']}")
                    esis = c_ed1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if r['sistema']=="P2P" else 1)
                    evd = c_ed2.date_input("VENCIMENTO", value=dt_v.date(), format="DD/MM/YYYY", key=f"d_{r['id']}")
                    ew = c_ed1.text_input("WHATSAPP", value=r['whatsapp'])
                    e_img = c_ed2.file_uploader("TROCAR LOGO", type=['png','jpg','jpeg'], key=f"i_{r['id']}")
                    
                    b1, b2 = st.columns(2)
                    if b1.form_submit_button("💾 SALVAR"):
                        vf = datetime.combine(evd, dt_v.time()).strftime('%Y-%m-%d %H:%M:%S')
                        l_f = image_to_base64(e_img) if e_img else r['logo_blob']
                        c_up = sqlite3.connect('supertv_gestao.db')
                        c_up.execute("UPDATE clientes SET nome=?, usuario=?, senha=?, servidor=?, sistema=?, vencimento=?, whatsapp=?, logo_blob=? WHERE id=?", 
                                     (en, eu, es, esrv, esis, vf, ew, l_f, r['id']))
                        c_up.commit(); st.rerun()
                    if b2.form_submit_button("🗑️ EXCLUIR"):
                        c_del = sqlite3.connect('supertv_gestao.db')
                        c_del.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                        c_del.commit(); st.rerun()

with tab2:
    st.subheader("🚀 Novo Cliente")
    with st.form("add"):
        n_n = st.text_input("NOME DO CLIENTE")
        n_u = st.text_input("USUÁRIO")
        n_s = st.text_input("SENHA")
        n_srv = st.selectbox("SERVIDOR", get_servidores())
        n_sis = st.selectbox("SISTEMA", ["P2P", "IPTV"])
        n_v = st.date_input("VENCIMENTO", value=datetime.now()+timedelta(days=30), format="DD/MM/YYYY")
        n_c = st.number_input("CUSTO", value=10.0)
        n_m = st.number_input("VALOR COBRADO", value=35.0)
        n_w = st.text_input("WHATSAPP")
        n_l = st.file_uploader("LOGOMARCA", type=['png','jpg','jpeg'])
        if st.form_submit_button("🚀 CADASTRAR"):
            v_f = datetime.combine(n_v, time(12,0)).strftime('%Y-%m-%d %H:%M:%S')
            l_b = image_to_base64(n_l)
            c_in = sqlite3.connect('supertv_gestao.db')
            c_in.execute("INSERT INTO clientes (nome, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, whatsapp, logo_blob) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (n_n, n_u, n_s, n_srv, n_sis, v_f, n_c, n_m, n_w, l_b))
            c_in.commit(); st.success("Cadastrado!"); st.rerun()

with tab3:
    st.subheader("🚨 COBRANÇA")
    pix = "62.326.879/0001-13"
    if not df.empty:
        df_cob = df[df['dias_res'] <= 3].copy()
        for _, c in df_cob.iterrows():
            t_v = "venceu" if c['dias_res'] < 0 else "vence"
            msg = f"Olá {c['nome']}, sua assinatura {t_v} em {pd.to_datetime(c['vencimento']).strftime('%d/%m/%Y')}. Pix: {pix}"
            st.link_button(f"📲 COBRAR {c['nome']} ({'VENCIDO' if c['dias_res'] < 0 else f'{c['dias_res']} d'})", f"https://wa.me/55{c['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ AJUSTES")
    st.markdown("### 🖥️ Gerenciar Servidores")
    ns = st.text_input("NOME DO NOVO SERVIDOR")
    if st.button("SALVAR SERVIDOR"):
        if ns:
            c_s = sqlite3.connect('supertv_gestao.db')
            c_s.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (ns.upper(),))
            c_s.commit(); st.rerun()
    st.divider()
    st.markdown("### 📥 Importar Dados")
    f_up = st.file_uploader("Arquivo Excel", type=["xlsx"])
    if f_up and st.button("PROCESSAR"):
        pd.read_excel(f_up).to_sql('clientes', sqlite3.connect('supertv_gestao.db'), if_exists='append', index=False)
        st.success("Importado!"); st.rerun()
    st.divider()
    if not df.empty:
        buf = io.BytesIO(); df.to_excel(buf, index=False)
        st.download_button("📥 BACKUP EXCEL", data=buf.getvalue(), file_name="backup.xlsx")
