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
    
    .img-servidor { width: 60px; height: 60px; border-radius: 8px; object-fit: cover; border: 1px solid #444; }
    
    /* Botões da Lista */
    .stButton > button { 
        text-align: left !important; 
        background-color: #161b22 !important; 
        border: 1px solid #30363d !important; 
        color: white !important; 
        border-radius: 12px !important; 
        padding: 12px !important; 
        min-height: 70px;
    }
    
    /* Botão Salvar (Verde) e Excluir (Vermelho) */
    .btn-salvar { background-color: #28a745 !important; color: white !important; font-weight: bold !important; }
    .btn-excluir { background-color: #dc3545 !important; color: white !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BANCO DE DADOS ---
def get_db_connection():
    return sqlite3.connect('supertv_gestao.db', check_same_thread=False)

def init_db():
    conn = get_db_connection()
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
    conn = get_db_connection()
    extras = pd.read_sql_query("SELECT nome FROM lista_servidores", conn)['nome'].tolist()
    conn.close()
    return sorted(list(set(fixos + extras)))

def format_data_br(data_str):
    try: return datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except: return data_str

init_db()

# --- 4. CARREGAR DADOS ---
conn = get_db_connection()
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

if not df.empty:
    hoje = datetime.now().date()
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)

# Inicialização de Estado de Edição
if 'edit_id' not in st.session_state: st.session_state.edit_id = None

# --- 5. HEADER ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ NOVO CADASTRO", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔎 Pesquisar...", placeholder="Nome ou Usuário")
    if not df.empty:
        df_f = df[df['nome'].str.contains(busca, case=False, na=False) | df['usuario'].str.contains(busca, case=False, na=False)] if busca else df
        
        for _, r in df_f.sort_values(by='nome').iterrows():
            img_tag = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            
            # Container do Cliente (Estilo Foto)
            col_img, col_btn = st.columns([1, 8])
            with col_img:
                st.markdown(f'<img src="{img_tag}" class="img-servidor">', unsafe_allow_html=True)
            with col_btn:
                label = f"👤 {str(r['nome']).upper()} | 🔑 {r['usuario']} | 📶 {r['servidor']} | 📅 {format_data_br(r['vencimento'])}"
                if st.button(label, key=f"clie_{r['id']}", use_container_width=True):
                    st.session_state.edit_id = r['id'] if st.session_state.edit_id != r['id'] else None

            # Área de Edição (Só aparece se clicado)
            if st.session_state.edit_id == r['id']:
                with st.container():
                    st.markdown(f"### 📝 Editando: {r['nome']}")
                    
                    c1, c2, c3 = st.columns(3)
                    new_nome = c1.text_input("NOME", value=r['nome'], key=f"n_{r['id']}")
                    new_user = c2.text_input("USUÁRIO", value=r['usuario'], key=f"u_{r['id']}")
                    new_senha = c3.text_input("SENHA", value=r['senha'], key=f"s_{r['id']}")
                    
                    servs = get_servidores()
                    new_serv = c1.selectbox("SERVIDOR", servs, index=servs.index(r['servidor']) if r['servidor'] in servs else 0, key=f"sv_{r['id']}")
                    new_sist = c2.selectbox("SISTEMA", ["IPTV", "P2P"], index=0 if r['sistema'] == "IPTV" else 1, key=f"st_{r['id']}")
                    new_venc = c3.date_input("VENCIMENTO", value=datetime.strptime(r['vencimento'], '%Y-%m-%d'), key=f"v_{r['id']}")
                    
                    new_custo = c1.number_input("CUSTO", value=float(r['custo']), key=f"c_{r['id']}")
                    new_valor = c2.number_input("VALOR", value=float(r['mensalidade']), key=f"m_{r['id']}")
                    new_ini = c3.date_input("INÍCIO", value=datetime.strptime(r['inicio'], '%Y-%m-%d'), key=f"i_{r['id']}")
                    
                    new_whats = c1.text_input("WHATSAPP", value=r['whatsapp'], key=f"w_{r['id']}")
                    new_obs = st.text_area("OBSERVAÇÃO", value=r['observacao'], key=f"o_{r['id']}")
                    
                    # BOTÕES DE AÇÃO REAIS
                    b_col1, b_col2, b_col3 = st.columns(3)
                    
                    if b_col1.button("💾 GRAVAR ALTERAÇÕES", key=f"save_btn_{r['id']}", use_container_width=True):
                        conn = get_db_connection()
                        conn.execute("""UPDATE clientes SET nome=?, usuario=?, senha=?, servidor=?, sistema=?, 
                                     vencimento=?, custo=?, mensalidade=?, inicio=?, whatsapp=?, observacao=? WHERE id=?""",
                                     (new_nome, new_user, new_senha, new_serv, new_sist, new_venc.strftime('%Y-%m-%d'), 
                                      new_custo, new_valor, new_ini.strftime('%Y-%m-%d'), new_whats, new_obs, r['id']))
                        conn.commit(); conn.close()
                        st.success("Salvo!")
                        st.session_state.edit_id = None
                        st.rerun()

                    if b_col2.button("🗑️ EXCLUIR CLIENTE", key=f"del_btn_{r['id']}", type="primary", use_container_width=True):
                        conn = get_db_connection()
                        conn.execute("DELETE FROM clientes WHERE id = ?", (r['id'],))
                        conn.commit(); conn.close()
                        st.session_state.edit_id = None
                        st.rerun()
                        
                    if b_col3.button("✖️ CANCELAR", key=f"can_btn_{r['id']}", use_container_width=True):
                        st.session_state.edit_id = None
                        st.rerun()
                st.markdown("---")

with tab2:
    st.subheader("🚀 Novo Cadastro")
    with st.form("form_novo"):
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("CLIENTE")
        user = c2.text_input("USUÁRIO")
        senha = c3.text_input("SENHA")
        serv = c1.selectbox("SERVIDOR", get_servidores())
        sist = c2.selectbox("SISTEMA", ["IPTV", "P2P"])
        venc = c3.date_input("VENCIMENTO", value=datetime.now() + timedelta(days=30))
        custo = c1.number_input("CUSTO", value=10.0)
        valor = c2.number_input("VALOR COBRADO", value=35.0)
        ini = c3.date_input("INÍCIOU DIA", value=datetime.now())
        whats = c1.text_input("WHATSAPP (DDD+NÚMERO)")
        img_serv = st.file_uploader("UPLOAD DA IMAGEM DO SERVIDOR", type=['png', 'jpg', 'jpeg'])
        obs = st.text_area("OBSERVAÇÃO")
        
        if st.form_submit_button("🚀 SALVAR CADASTRO"):
            l_b = base64.b64encode(img_serv.read()).decode() if img_serv else None
            conn = get_db_connection()
            conn.execute("INSERT INTO clientes (nome, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, inicio, whatsapp, observacao, logo_blob) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (nome, user, senha, serv, sist, venc.strftime('%Y-%m-%d'), custo, valor, ini.strftime('%Y-%m-%d'), whats, obs, l_b))
            conn.commit(); conn.close()
            st.rerun() # Volta para clientes

# (As abas 3 e 4 continuam iguais ao seu original para não mudar as outras funções)
with tab3:
    st.subheader("🚨 Central de Cobrança")
    pix = "62.326.879/0001-13"
    if not df.empty:
        df_c = df.sort_values(by='dias_res')
        for _, c in df_c.iterrows():
            cls = "row-vencido" if c['dias_res'] < 0 else "row-hoje" if c['dias_res'] == 0 else "row-amanha" if c['dias_res'] == 1 else "row-em-dia"
            st.markdown(f'<div class="cliente-row {cls}"><b>{c["nome"].upper()}</b> | Vence: {format_data_br(c["vencimento"])}</div>', unsafe_allow_html=True)
            if st.button(f"📲 Cobrar {c['nome']}", key=f"cob_{c['id']}"):
                msg = f"Olá {c['nome']}! Sua assinatura {c['servidor']} vence dia {format_data_br(c['vencimento'])}. Pix: {pix}"
                st.link_button("Abrir WhatsApp", f"https://wa.me/55{c['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Ajustes")
    if st.button("📦 GERAR BACKUP EXCEL"):
        out = io.BytesIO()
        df.to_excel(out, index=False)
        st.download_button("⬇️ Baixar", out.getvalue(), "backup.xlsx")
