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
    
    .cliente-row { border-radius: 12px; padding: 12px; margin-bottom: 10px; border: 1px solid #30363d; display: flex; align-items: center; gap: 15px; }
    .row-vencido { background-color: #331111; border-left: 8px solid #ff4b4b; }
    .row-hoje { background-color: #3d2b11; border-left: 8px solid #ffa500; }
    .row-amanha { background-color: #333311; border-left: 8px solid #ffff00; }
    .row-em-dia { background-color: #112233; border-left: 8px solid #00d4ff; }
    
    .img-servidor { width: 55px; height: 55px; border-radius: 8px; object-fit: cover; border: 1px solid #444; }
    div[data-testid="column"] button { text-align: left !important; background-color: #161b22 !important; border: 1px solid #30363d !important; color: white !important; border-radius: 12px !important; padding: 12px !important; min-height: 70px; }
    
    .stButton > button[kind="primary"] { background-color: #ff4b4b !important; color: white !important; text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, usuario TEXT, senha TEXT, 
                  servidor TEXT, sistema TEXT, vencimento TEXT, custo REAL, 
                  mensalidade REAL, inicio TEXT, whatsapp TEXT, observacao TEXT, logo_blob TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    conn.commit(); conn.close()

def get_servidores():
    fixos = ["UNIPLAY", "MUNDOGF", "P2BRAZ", "BLADETV", "UNITV", "P2CINETV", "SPEEDTV", "PLAYTV", "MEGATV", "BOB PLAYER", "IBO PLAYER", "IBOPLAYER PRO"]
    conn = sqlite3.connect('supertv_gestao.db')
    extras = pd.read_sql_query("SELECT nome FROM lista_servidores", conn)['nome'].tolist()
    conn.close()
    return sorted(list(set(fixos + extras)))

def format_data_br(data_str):
    try: return datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except: return data_str

init_db()
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

if not df.empty:
    hoje = datetime.now().date()
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)

# --- 4. HEADER ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

# --- 5. MÉTRICAS ---
if not df.empty:
    m1, m2, m3, m4 = st.columns(4)
    total_clie = len(df)
    vencidos = len(df[df['dias_res'] < 0])
    hoje_venc = len(df[df['dias_res'] == 0])
    lucro = df['mensalidade'].sum() - df['custo'].sum()
    
    m1.metric("TOTAL CLIENTES", total_clie)
    m2.metric("VENCIDOS", vencidos, delta_color="inverse")
    m3.metric("VENCEM HOJE", hoje_venc)
    m4.metric("LUCRO ESTIMADO", f"R$ {lucro:,.2f}")

# --- 6. ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ NOVO CADASTRO", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔎 Pesquisar...", placeholder="Nome ou Usuário")
    if not df.empty:
        df_f = df[df['nome'].str.contains(busca, case=False, na=False) | df['usuario'].str.contains(busca, case=False, na=False)] if busca else df
        for _, r in df_f.sort_values(by='nome').iterrows():
            img_tag = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            col_img, col_btn = st.columns([1, 9])
            with col_img: st.markdown(f'<img src="{img_tag}" class="img-servidor">', unsafe_allow_html=True)
            with col_btn:
                label = f"👤 {str(r['nome']).upper()} | 🔑 {r['usuario']} | 📶 {r['servidor']} | 📅 {format_data_br(r['vencimento'])}"
                if st.button(label, key=f"clie_{r['id']}"):
                    with st.expander(f"📝 EDITAR: {str(r['nome']).upper()}", expanded=True):
                        with st.form(key=f"edit_form_{r['id']}"):
                            ce1, ce2, ce3 = st.columns(3)
                            ed_nome = ce1.text_input("CLIENTE", value=r['nome'])
                            ed_user = ce2.text_input("USUÁRIO", value=r['usuario'])
                            ed_senha = ce3.text_input("SENHA", value=r['senha'])
                            
                            ed_serv = ce1.selectbox("SERVIDOR", get_servidores(), index=get_servidores().index(r['servidor']) if r['servidor'] in get_servidores() else 0)
                            ed_sist = ce2.selectbox("SISTEMA", ["IPTV", "P2P"], index=0 if r['sistema'] == "IPTV" else 1)
                            ed_venc = ce3.date_input("VENCIMENTO", value=datetime.strptime(r['vencimento'], '%Y-%m-%d'), format="DD/MM/YYYY")
                            
                            ed_custo = ce1.number_input("CUSTO", value=float(r['custo']))
                            ed_valor = ce2.number_input("VALOR COBRADO", value=float(r['mensalidade']))
                            ed_ini = ce3.date_input("INÍCIOU DIA", value=datetime.strptime(r['inicio'], '%Y-%m-%d'), format="DD/MM/YYYY")
                            
                            ed_whats = ce1.text_input("WHATSAPP", value=r['whatsapp'])
                            ed_obs = st.text_area("OBSERVAÇÃO", value=r['observacao'])
                            
                            # Botão de salvar dentro do form
                            if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                                conn = sqlite3.connect('supertv_gestao.db')
                                conn.execute("""UPDATE clientes SET nome=?, usuario=?, senha=?, servidor=?, sistema=?, 
                                             vencimento=?, custo=?, mensalidade=?, inicio=?, whatsapp=?, observacao=? WHERE id=?""",
                                             (ed_nome, ed_user, ed_senha, ed_serv, ed_sist, ed_venc.strftime('%Y-%m-%d'), 
                                              ed_custo, ed_valor, ed_ini.strftime('%Y-%m-%d'), ed_whats, ed_obs, r['id']))
                                conn.commit(); conn.close()
                                st.success("Atualizado com sucesso!")
                                st.rerun()

                        # Botões de Renovação e Exclusão fora do Form de edição
                        st.divider()
                        br1, br2 = st.columns([2, 1])
                        dias_add = br1.number_input("Adicionar dias na renovação", value=30, key=f"days_{r['id']}")
                        if br1.button(f"➕ RENOVAR +{dias_add} DIAS", key=f"renov_{r['id']}"):
                            nova_data = (datetime.strptime(r['vencimento'], '%Y-%m-%d') + timedelta(days=dias_add)).strftime('%Y-%m-%d')
                            conn = sqlite3.connect('supertv_gestao.db')
                            conn.execute("UPDATE clientes SET vencimento = ? WHERE id = ?", (nova_data, r['id']))
                            conn.commit(); conn.close(); st.rerun()
                        
                        if br2.button("🗑️ EXCLUIR CLIENTE", key=f"del_{r['id']}", type="primary", use_container_width=True):
                            conn = sqlite3.connect('supertv_gestao.db')
                            conn.execute("DELETE FROM clientes WHERE id = ?", (r['id'],))
                            conn.commit(); conn.close()
                            st.rerun()

with tab2:
    st.subheader("🚀 Novo Cadastro")
    with st.form("form_add", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("CLIENTE")
        user = c2.text_input("USUÁRIO")
        senha = c3.text_input("SENHA")
        serv = c1.selectbox("SERVIDOR", get_servidores())
        sist = c2.selectbox("SISTEMA", ["IPTV", "P2P"])
        venc = c3.date_input("VENCIMENTO", value=datetime.now() + timedelta(days=30), format="DD/MM/YYYY")
        custo = c1.number_input("CUSTO", value=10.0)
        valor = c2.number_input("VALOR COBRADO", value=35.0)
        ini = c3.date_input("INÍCIOU DIA", value=datetime.now(), format="DD/MM/YYYY")
        whats = c1.text_input("WHATSAPP (DDD+NÚMERO)")
        img_serv = st.file_uploader("UPLOAD DA IMAGEM DO SERVIDOR", type=['png', 'jpg', 'jpeg'])
        obs = st.text_area("OBSERVAÇÃO")
        
        if st.form_submit_button("🚀 SALVAR CADASTRO"):
            if not nome or not user or not whats:
                st.error("⚠️ Preencha Nome, Usuário e WhatsApp!")
            else:
                l_b = base64.b64encode(img_serv.read()).decode() if img_serv else None
                conn = sqlite3.connect('supertv_gestao.db')
                conn.execute("INSERT INTO clientes (nome, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, inicio, whatsapp, observacao, logo_blob) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                            (nome, user, senha, serv, sist, venc.strftime('%Y-%m-%d'), custo, valor, ini.strftime('%Y-%m-%d'), whats, obs, l_b))
                conn.commit(); conn.close()
                st.success("Salvo!")
                st.rerun()

with tab3:
    st.subheader("🚨 Central de Cobrança")
    pix = "62.326.879/0001-13"
    if not df.empty:
        f_cols = st.columns(7)
        if 'f_cob' not in st.session_state: st.session_state.f_cob = "Todos"
        if f_cols[0].button("TODOS"): st.session_state.f_cob = "Todos"
        if f_cols[1].button("VENCIDOS"): st.session_state.f_cob = "Vencidos"
        if f_cols[2].button("HOJE"): st.session_state.f_cob = "Hoje"
        if f_cols[3].button("AMANHÃ"): st.session_state.f_cob = "Amanha"
        if f_cols[4].button("2 DIAS"): st.session_state.f_cob = "2 Dias"
        if f_cols[5].button("3 DIAS"): st.session_state.f_cob = "3 Dias"
        if f_cols[6].button("4 DIAS+"): st.session_state.f_cob = "4 Mais"

        df_c = df.copy()
        if st.session_state.f_cob == "Vencidos": df_c = df[df['dias_res'] < 0]
        elif st.session_state.f_cob == "Hoje": df_c = df[df['dias_res'] == 0]
        elif st.session_state.f_cob == "Amanha": df_c = df[df['dias_res'] == 1]
        elif st.session_state.f_cob == "2 Dias": df_c = df[df['dias_res'] == 2]
        elif st.session_state.f_cob == "3 Dias": df_c = df[df['dias_res'] == 3]
        elif st.session_state.f_cob == "4 Mais": df_c = df[df['dias_res'] >= 4]

        clientes_sel = []
        for _, c in df_c.sort_values(by='dias_res').iterrows():
            cls = "row-vencido" if c['dias_res'] < 0 else "row-hoje" if c['dias_res'] == 0 else "row-amanha" if c['dias_res'] == 1 else "row-em-dia"
            col_ch, col_ca = st.columns([1, 15])
            if col_ch.checkbox("", key=f"sel_{c['id']}"): clientes_sel.append(c)
            col_ca.markdown(f'<div class="cliente-row {cls}"><b>{str(c["nome"]).upper()}</b> | Vence: {format_data_br(c["vencimento"])}</div>', unsafe_allow_html=True)

        if st.button(f"📲 DISPARAR ({len(clientes_sel)})", use_container_width=True):
            for i in clientes_sel:
                msg = f"Olá {str(i['nome']).split()[0]}! 👋 Sua assinatura {i['servidor']} vence dia {format_data_br(i['vencimento'])}. Pix: {pix}"
                st.link_button(f"Enviar para {i['nome']}", f"https://wa.me/55{i['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Ajustes")
    aj1, aj2, aj3 = st.columns(3)
    with aj1:
        up = st.file_uploader("UPLOAD EXCEL", type=["xlsx"])
        if up and st.button("🚀 Importar"):
            pd.read_excel(up).to_sql('clientes', sqlite3.connect('supertv_gestao.db'), if_exists='append', index=False)
            st.rerun()
    with aj2:
        if st.button("📦 GERAR BACKUP"):
            out = io.BytesIO()
            pd.read_sql_query("SELECT * FROM clientes", sqlite3.connect('supertv_gestao.db')).to_excel(out, index=False)
            st.download_button("⬇️ Baixar Arquivo", out.getvalue(), "backup_supertv.xlsx")
    with aj3:
        ns = st.text_input("NOVO SERVIDOR")
        if st.button("➕ ADICIONAR"):
            conn = sqlite3.connect('supertv_gestao.db'); conn.execute("INSERT INTO lista_servidores (nome) VALUES (?)", (ns.upper(),)); conn.commit(); conn.close(); st.rerun()
