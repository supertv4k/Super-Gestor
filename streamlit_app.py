import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse
import base64
import io
import time
import pytz 

# --- 1. CONFIGURAÇÃO DE FUSO HORÁRIO BRASIL ---
fuso_br = pytz.timezone('America/Sao_Paulo')
hoje = datetime.now(fuso_br).date()

st.set_page_config(page_title="SUPERTV4K GESTÃO PRO", layout="wide")

query_params = st.query_params
if "editar_id" in query_params:
    st.session_state.id_para_editar = query_params["editar_id"]

if 'filtro_f' not in st.session_state:
    st.session_state.filtro_f = "vencidos"

if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = [
        "MUNDO GF", "UNIPLAY", "P2BRAZ", "UNITV", "PLAYTV", 
        "P2CINE", "P2SPEED", "BLADE", "MEGATV", "BOB PLAYER", 
        "IBO PLAYER", "IBO PRO PLAYER"
    ]

# --- 2. ESTILIZAÇÃO CSS ATUALIZADA (CIRÚRGICA NO CARD) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; margin-bottom: 20px; }
    .logo-gestao { width: 380px; margin-bottom: -15px !important; }
    .logo-supertv { width: 320px; }
    
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; margin-bottom: 20px; }
    .metric-label { font-size: 12px; color: #8b949e; font-weight: bold; text-transform: uppercase; }
    .metric-value { font-size: 20px; color: #00d4ff; font-weight: 900; }

    /* CARD RETANGULAR ESTREITO COM LOGO AO LADO */
    .cliente-card-container {
        position: relative;
        display: flex;
        align-items: center;
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 8px 15px;
        margin-bottom: 10px;
        height: 70px; /* Altura fixa para ser estreito */
        transition: 0.2s;
        overflow: hidden;
    }
    .cliente-card-container:hover { border-color: #00d4ff; background-color: #1c2128; }
    
    .logo-fixa {
        width: 45px;
        height: 45px;
        border-radius: 8px;
        object-fit: cover;
        margin-right: 15px;
        border: 1px solid #444;
        flex-shrink: 0;
    }
    
    .info-box {
        display: flex;
        flex-direction: column;
        justify-content: center;
        flex-grow: 1;
        overflow: hidden;
    }
    
    .nome-texto {
        font-weight: 900;
        font-size: 15px;
        color: white;
        text-transform: uppercase;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin: 0;
    }
    
    .sub-texto {
        font-size: 12px;
        color: #8b949e;
        font-weight: 700;
        margin: 0;
    }

    .dias-badge {
        font-weight: 900;
        font-size: 14px;
        text-align: right;
        min-width: 70px;
    }

    /* BOTÃO INVISÍVEL POR CIMA DO CARD */
    .overlay-link {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        z-index: 10;
        cursor: pointer;
    }

    .cor-vencido { color: #FF4B4B; }
    .cor-alerta { color: #FFD700; }
    .cor-ok { color: #00FF00; }
    .cor-tranquilo { color: #00D4FF; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE DADOS ---
def conectar_gs():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return gspread.authorize(creds).open_by_key("1ntE8RpofySu5IFupuvOZxZnrnmHKzaYbyqAQ-Mzc8so").sheet1
    except: return None

def carregar_dados(sheet):
    if sheet:
        valores = sheet.get_all_values()
        if len(valores) < 2: return pd.DataFrame()
        colunas = ["id", "nome", "usuario", "senha", "servidor", "sistema", "vencimento", "custo", "mensalidade", "whatsapp", "observacao", "logo_blob"]
        df = pd.DataFrame(valores[1:], columns=colunas)
        for col in ['id', 'mensalidade', 'custo']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        return df[df['nome'].str.strip() != ""]
    return pd.DataFrame()

def get_cor_classe(dias):
    if dias < 0: return "cor-vencido"
    elif dias <= 2: return "cor-alerta"
    elif dias == 3: return "cor-ok"
    else: return "cor-tranquilo"

sheet = conectar_gs()
df = carregar_dados(sheet)

# --- LÓGICA DE SELEÇÃO ---
if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    if "id_para_editar" in st.session_state:
        sel = df[df['id'].astype(str) == str(st.session_state.id_para_editar)]
        if not sel.empty:
            st.session_state.cliente_selecionado = sel.iloc[0].to_dict()
            del st.session_state.id_para_editar

# --- 4. INTERFACE ---
if st.session_state.get('cliente_selecionado') is not None:
    c = st.session_state.cliente_selecionado
    st.markdown("### 📝 GERENCIANDO CLIENTE")
    with st.form("form_edit_full"):
        col1, col2 = st.columns(2)
        enome = col1.text_input("NOME", value=c['nome'])
        euser = col2.text_input("USUÁRIO", value=c['usuario'])
        esenha = col1.text_input("SENHA", value=c['senha'])
        eserv = col2.selectbox("SERVIDOR", st.session_state.lista_servidores, index=st.session_state.lista_servidores.index(c['servidor'].upper()) if c['servidor'].upper() in st.session_state.lista_servidores else 0)
        esist = col1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if c['sistema']=="P2P" else 1)
        evenc = col2.date_input("VENCIMENTO", value=pd.to_datetime(c['vencimento']).date())
        ecusto = col1.number_input("CUSTO", value=float(c['custo']))
        emensal = col2.number_input("MENSALIDADE", value=float(c['mensalidade']))
        ewhats = col1.text_input("WHATSAPP", value=c['whatsapp'])
        eobs = col2.text_area("OBSERVAÇÃO", value=c['observacao'])
        eimg = st.file_uploader("TROCAR LOGO", type=['png', 'jpg'])
        
        b1, b2, b3, b4 = st.columns(4)
        if b1.form_submit_button("💾 SALVAR"):
            idx = sheet.col_values(1).index(str(c['id'])) + 1
            blob = base64.b64encode(eimg.read()).decode() if eimg else c['logo_blob']
            sheet.update(f'A{idx}:L{idx}', [[c['id'], enome.upper(), euser, esenha, eserv.upper(), esist, evenc.strftime('%Y-%m-%d'), ecusto, emensal, ewhats, eobs, blob]])
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()
        if b2.form_submit_button("⭐️RENOVAR +30"):
            idx = sheet.col_values(1).index(str(c['id'])) + 1
            sheet.update_cell(idx, 7, (hoje + timedelta(days=30)).strftime('%Y-%m-%d'))
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()
        if b3.form_submit_button("🗑️ EXCLUIR"):
            sheet.delete_rows(sheet.col_values(1).index(str(c['id'])) + 1)
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()
        if b4.form_submit_button("✖️ FECHAR"):
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()

st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

if not df.empty:
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-card"><div class="metric-label">👤 Ativos</div><div class="metric-value">{len(df[df["dias_res"]>=0])}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">❌ Vencidos</div><div class="metric-value" style="color:#ff4b4b">{len(df[df["dias_res"]<0])}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-label">⏰ Vence Hoje</div><div class="metric-value" style="color:#ffd700">{len(df[df["dias_res"]==0])}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-label">💰 Lucro</div><div class="metric-value" style="color:#00ff88">R$ {(df["mensalidade"].sum()-df["custo"].sum()):,.2f}</div></div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    with tab1:
        busca = st.text_input("🔎 BUSCAR...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            cor = get_cor_classe(r['dias_res'])
            st.markdown(f'''
                <div class="cliente-card-container">
                    <a href="/?editar_id={r['id']}" target="_self" class="overlay-link"></a>
                    <img src="{img}" class="logo-fixa">
                    <div class="info-box">
                        <p class="nome-texto">{r['nome']}</p>
                        <p class="sub-texto">{r['servidor'].upper()} | {r['sistema']}</p>
                    </div>
                    <div class="dias-badge {cor}">{r['dias_res']} DIAS</div>
                </div>
            ''', unsafe_allow_html=True)

    with tab3:
        st.subheader("🚨 COBRANÇA")
        c_cols = st.columns(6)
        filtros = ["vencidos", "hoje", "1dia", "2dias", "3dias", "todos"]
        labels = ["🆘 VENCIDOS", "⏰ HOJE", "⚠️ AMANHÃ", "2️⃣ DIAS", "⏳ 3️⃣ DIAS", "🛗 TODOS"]
        for i, f in enumerate(filtros):
            if c_cols[i].button(labels[i]): st.session_state.filtro_f = f
        
        f_atual = st.session_state.filtro_f
        df_c = df
        if f_atual == "vencidos": df_c = df[df['dias_res'] < 0]
        elif f_atual == "hoje": df_c = df[df['dias_res'] == 0]
        elif f_atual == "1dia": df_c = df[df['dias_res'] == 1]
        elif f_atual == "2dias": df_c = df[df['dias_res'] == 2]
        elif f_atual == "3dias": df_c = df[df['dias_res'] == 3]

        for _, r in df_c.iterrows():
            col_c, col_b = st.columns([4, 1.2])
            img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            cor = get_cor_classe(r['dias_res'])
            with col_c:
                st.markdown(f'''
                    <div class="cliente-card-container">
                        <img src="{img}" class="logo-fixa">
                        <div class="info-box">
                            <p class="nome-texto">{r['nome']}</p>
                            <p class="sub-texto">{r['servidor'].upper()} | {r['sistema']}</p>
                        </div>
                        <div class="dias-badge {cor}">{r['dias_res']} DIAS</div>
                    </div>
                ''', unsafe_allow_html=True)
            with col_b:
                st.write(" ") # Espaçador
                msg = f"Olá! Sua assinatura vence em {r['dias_res']} dias. Pix: 62.326.879/0001-13"
                url = f"https://wa.me/55{r['whatsapp']}?text={urllib.parse.quote(msg)}"
                st.link_button("📲 COBRAR", url, use_container_width=True)

    with tab4:
        st.subheader("🛠️ AJUSTES")
        if st.button("🔄 SINCRONIZAR"): st.rerun()
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.drop(columns=['dt_venc_calc', 'dias_res']).to_excel(writer, index=False)
        st.download_button("📥 BACKUP EXCEL", data=buffer.getvalue(), file_name="backup.xlsx")
