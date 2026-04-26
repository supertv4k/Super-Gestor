import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse
import base64
import io
import pytz 

# --- 1. CONFIGURAÇÃO DE FUSO HORÁRIO BRASIL ---
fuso_br = pytz.timezone('America/Sao_Paulo')
hoje = datetime.now(fuso_br).date()

st.set_page_config(page_title="SUPERTV4K GESTÃO PRO", layout="wide")

# Lógica de Edição via URL e Estados
if 'filtro_f' not in st.session_state:
    st.session_state.filtro_f = "vencidos"

if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = [
        "MUNDO GF", "UNIPLAY", "P2BRAZ", "UNITV", "PLAYTV", 
        "P2CINE", "P2SPEED", "BLADE", "MEGATV", "BOB PLAYER", 
        "IBO PLAYER", "IBO PRO PLAYER"
    ]

# --- 2. ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; margin-bottom: 20px; }
    .logo-gestao { width: 380px; margin-bottom: -15px !important; }
    .logo-supertv { width: 320px; }
    
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; margin-bottom: 20px; }
    .metric-label { font-size: 12px; color: #8b949e; font-weight: bold; text-transform: uppercase; }
    .metric-value { font-size: 20px; color: #00d4ff; font-weight: 900; }

    .cliente-card-wrapper {
        display: flex; align-items: center; background-color: #161b22;
        border: 1px solid #30363d; border-radius: 12px; padding: 8px 15px;
        height: 75px; transition: 0.2s; overflow: hidden;
    }
    
    .img-card { width: 50px; height: 50px; border-radius: 8px; object-fit: cover; margin-right: 15px; border: 1px solid #444; flex-shrink: 0; }
    .info-box { display: flex; flex-direction: column; justify-content: center; flex-grow: 1; overflow: hidden; }
    .nome-texto { font-weight: 900; font-size: 16px; color: white; text-transform: uppercase; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .sub-texto { font-size: 13px; color: #8b949e; font-weight: 700; margin: 0; }
    .dias-box-html { font-weight: 900; font-size: 15px; text-align: right; min-width: 90px; border-left: 1px solid #30363d; padding-left: 10px; }
    
    /* BOTÃO QUE COBRE O CARD PARA FUNCIONAR O CLIQUE */
    div.stButton > button[kind="secondary"] {
        background: transparent; color: transparent; border: none;
        height: 75px; margin-top: -75px; width: 100%; display: block;
        z-index: 10; position: relative;
    }
    div.stButton > button:hover { background: rgba(0, 212, 255, 0.05); border: 1px solid #00d4ff; }

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

if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)

# --- LOGO (CABEÇALHO) ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

# --- 4. ÁREA DE EDIÇÃO (ABRE NO INÍCIO) ---
if st.session_state.get('cliente_selecionado') is not None:
    c = st.session_state.cliente_selecionado
    st.markdown(f"### 📝 EDITAR CLIENTE: {c['nome']}")
    with st.form("form_edit_full"):
        col1, col2 = st.columns(2)
        enome = col1.text_input("NOME", value=c['nome'])
        euser = col2.text_input("USUÁRIO", value=c['usuario'])
        esenha = col1.text_input("SENHA", value=c['senha'])
        eserv = col2.selectbox("SERVIDOR", st.session_state.lista_servidores, index=st.session_state.lista_servidores.index(c['servidor'].upper()) if c['servidor'].upper() in st.session_state.lista_servidores else 0)
        esist = col1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if c['sistema']=="P2P" else 1)
        evenc = col2.date_input("VENCIMENTO", value=pd.to_datetime(c['vencimento']).date(), format="DD/MM/YYYY")
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
            st.session_state.cliente_selecionado = None; st.rerun()
        if b2.form_submit_button("⭐️ RENOVAR (+30)"):
            idx = sheet.col_values(1).index(str(c['id'])) + 1
            nova_data = (hoje + timedelta(days=30)).strftime('%Y-%m-%d')
            sheet.update_cell(idx, 7, nova_data)
            st.session_state.cliente_selecionado = None; st.rerun()
        if b3.form_submit_button("🗑️ EXCLUIR"):
            idx = sheet.col_values(1).index(str(c['id'])) + 1
            sheet.delete_rows(idx)
            st.session_state.cliente_selecionado = None; st.rerun()
        if b4.form_submit_button("✖️ FECHAR"):
            st.session_state.cliente_selecionado = None; st.rerun()
    st.divider()

# --- DASHBOARD ---
if not df.empty:
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-card"><div class="metric-label">👤 Ativos</div><div class="metric-value">{len(df[df["dias_res"]>=0])}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">❌ Vencidos</div><div class="metric-value" style="color:#ff4b4b">{len(df[df["dias_res"]<0])}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-label">⏰ Vence Hoje</div><div class="metric-value" style="color:#ffd700">{len(df[df["dias_res"]==0])}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-label">💲 Lucro</div><div class="metric-value" style="color:#00ff88">R$ {(df["mensalidade"].sum()-df["custo"].sum()):,.2f}</div></div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    with tab1:
        busca = st.text_input("🔎 BUSCAR CLIENTE...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            cor = get_cor_classe(r['dias_res'])
            st.markdown(f'''
                <div class="cliente-card-wrapper">
                    <img src="{img}" class="img-card">
                    <div class="info-box">
                        <p class="nome-texto">{r['nome']}</p>
                        <p class="sub-texto">{r['servidor'].upper()} | {r['sistema']}</p>
                    </div>
                    <div class="dias-box-html {cor}">{r['dias_res']} DIAS</div>
                </div>
            ''', unsafe_allow_html=True)
            if st.button("Abrir", key=f"edit_{r['id']}", use_container_width=True):
                st.session_state.cliente_selecionado = r.to_dict()
                st.rerun()

    with tab2:
        st.subheader("🚀CADASTRAR CLIENTE")
        with st.form("add_cli", clear_on_submit=True):
            ca1, ca2 = st.columns(2)
            nnome = ca1.text_input("NOME"); nuser = ca2.text_input("USUÁRIO")
            nsenha = ca1.text_input("SENHA"); nserv = ca2.selectbox("SERVIDOR", st.session_state.lista_servidores)
            nsist = ca1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0)
            nvenc = ca2.date_input("VENCIMENTO", value=hoje + timedelta(days=30), format="DD/MM/YYYY")
            ncusto = ca1.number_input("CUSTO", value=5.0); nmensal = ca2.number_input("MENSALIDADE", value=35.0)
            nwhats = ca1.text_input("WHATSAPP"); nobs = ca2.text_area("OBSERVAÇÃO"); nimg = st.file_uploader("LOGO", type=['png', 'jpg'])
            if st.form_submit_button("🚀 CADASTRAR CLIENTE"):
                prox_id = int(df['id'].max() + 1) if not df.empty else 1
                blob = base64.b64encode(nimg.read()).decode() if nimg else ""
                sheet.append_row([prox_id, nnome.upper(), nuser, nsenha, nserv.upper(), nsist, nvenc.strftime('%Y-%m-%d'), ncusto, nmensal, nwhats, nobs, blob])
                st.rerun()

    with tab3:
        st.subheader("🚨 ENVIAR COBRANÇAS")
        c_cols = st.columns(6)
        labels = ["🆘 VENCIDOS", "⏰ HOJE", "⚠️ AMANHÃ", "2️⃣ DIAS", " 3️⃣ DIAS", "👥 TODOS"]
        filtros = ["vencidos", "hoje", "1dia", "2dias", "3dias", "todos"]
        for i, f in enumerate(filtros):
            if c_cols[i].button(labels[i], key=f"btn_filtro_{f}"): st.session_state.filtro_f = f
        
        msg_map = {
            "vencidos": "🚨SUA ASSINATURA DE TV VENCEU !\n\nNÃO PREOCUPE, BASTA FAZER O PIX QUE REATIVAMOS PRA VOCÊ!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "hoje": "⚠️SUA ASSINATURA DE TV VENCE HOJE ⏰! \n\nNÃO FIQUE SEM TV, BASTA FAZER O PIX QUE RENOVAMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "1dia": "⚠️SUA ASSINATURA DE TV VENCE AMANHÃ ⏰! \n\nNÃO FIQUE SEM TV, FAÇA O PIX E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "2dias": "⚠️SUA ASSINATURA DE TV VENCE EM 2️⃣ DIAS ⏰! \n\nFAÇA O PIX AGORA E RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "3dias": "⚠️SUA ASSINATURA DE TV VENCE EM 3️⃣ DIAS ⏰! \n\nFAÇA O PIX AGORA E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!",
            "todos": "Olá! Sua assinatura SuperTV4K precisa de atenção. Pix CNPJ: 62.326.879/0001-13"
        }
        
        f_at = st.session_state.filtro_f
        msg_atual = msg_map.get(f_at, msg_map["todos"])

        df_c = df
        if f_at == "vencidos": df_c = df[df['dias_res'] < 0]
        elif f_at == "hoje": df_c = df[df['dias_res'] == 0]
        elif f_at == "1dia": df_c = df[df['dias_res'] == 1]
        elif f_at == "2dias": df_c = df[df['dias_res'] == 2]
        elif f_at == "3dias": df_c = df[df['dias_res'] == 3]

        for _, r in df_c.iterrows():
            col1, col2 = st.columns([4, 1.2])
            img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            cor = get_cor_classe(r['dias_res'])
            with col1:
                st.markdown(f'''<div class="cliente-card-wrapper"><img src="{img}" class="img-card"><div class="info-box"><p class="nome-texto">{r['nome']}</p><p class="sub-texto">{r['servidor'].upper()} | {r['sistema']}</p></div><div class="dias-box-html {cor}">{r['dias_res']} DIAS</div></div>''', unsafe_allow_html=True)
            with col2:
                st.write("") 
                url = f"https://wa.me/55{r['whatsapp']}?text={urllib.parse.quote(msg_atual)}"
                st.link_button("📲 ENVIAR COBRANÇA", url, use_container_width=True)

    with tab4:
        st.subheader("⚙️ AJUSTES E SERVIDORES")
        s_nome = st.text_input("NOME DO NOVO SERVIDOR")
        c1, c2 = st.columns(2)
        if c1.button("📡 ADICIONAR SERVIDOR"):
            if s_nome and s_nome.upper() not in st.session_state.lista_servidores:
                st.session_state.lista_servidores.append(s_nome.upper()); st.rerun()
        if c2.button("🗑️ EXCLUIR SERVIDOR"):
            if s_nome.upper() in st.session_state.lista_servidores:
                st.session_state.lista_servidores.remove(s_nome.upper()); st.rerun()
        st.divider()
        if st.button("🔄 SINCRONIZAR GOOGLE SHEETS"): st.rerun()
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.drop(columns=['dt_venc_calc', 'dias_res']).to_excel(writer, index=False)
        st.download_button("📥 BAIXAR BACKUP EXCEL", data=buffer.getvalue(), file_name="backup_gestao.xlsx")
