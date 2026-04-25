import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse
import base64
import io
import time

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="SUPERTV4K GESTÃO PRO", layout="wide")

if "editar_id" in st.query_params:
    st.session_state.id_para_editar = st.query_params["editar_id"]

if 'filtro_f' not in st.session_state:
    st.session_state.filtro_f = "vencidos"

if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = ["Uniplay", "Mundo GF", "P2Braz", "Unitv", "Playtv", "P2Cine", "P2Speed", "Blade", "MegaTV", "Bob Player", "Ibo Player", "Ibo Pro Player"]

# --- LÓGICA DE FILA E DISPARO EM MASSA ---
if 'clientes_selecionados' not in st.session_state:
    st.session_state.clientes_selecionados = []
if 'indice_fila' not in st.session_state:
    st.session_state.indice_fila = 0
if 'em_disparo' not in st.session_state:
    st.session_state.em_disparo = False
if 'modo_fila_ativo' not in st.session_state:
    st.session_state.modo_fila_ativo = False

# --- 2. ESTILIZAÇÃO CSS (PRESERVADA) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; margin-bottom: 20px; }
    .logo-gestao { width: 380px; margin-bottom: -15px !important; }
    .logo-supertv { width: 320px; }
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; margin-bottom: 20px; }
    .metric-label { font-size: 12px; color: #8b949e; font-weight: bold; text-transform: uppercase; }
    .metric-value { font-size: 20px; color: #00d4ff; font-weight: 900; }
    .card-link { text-decoration: none !important; color: inherit !important; display: block; margin-bottom: 8px; }
    .cliente-card-html { display: flex; flex-direction: row; align-items: center; background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 12px 15px; width: 100%; transition: 0.2s; }
    .img-servidor-card { width: 50px; height: 50px; border-radius: 8px; object-fit: cover; margin-right: 15px; border: 1px solid #444; flex-shrink: 0; }
    .info-container { flex-grow: 1; display: flex; flex-direction: column; justify-content: center; }
    .nome-c { font-weight: 900; font-size: 16px; color: white; text-transform: uppercase; margin: 0; }
    .sub-info { color: #8b949e; font-size: 13px; margin-top: 2px; }
    .dias-box { flex-shrink: 0; margin-left: 10px; padding-left: 15px; border-left: 1px solid #30363d; width: 95px; text-align: right; }
    .cor-vencido { color: #FF4B4B; font-weight: 900; }
    .cor-alerta { color: #FFD700; font-weight: 900; }
    .cor-ok { color: #00FF00; font-weight: 900; }
    .cor-tranquilo { color: #00D4FF; font-weight: 900; }
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
hoje = datetime.now().date()

# --- 4. INTERFACE ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    with tab1:
        busca = st.text_input("🔎 BUSCAR CLIENTE...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            cor = get_cor_classe(r['dias_res'])
            st.markdown(f'''<a href="/?editar_id={r['id']}" target="_self" class="card-link"><div class="cliente-card-html"><img src="{img}" class="img-servidor-card"><div class="info-container"><div class="nome-c">{r['nome']}</div><div class="sub-info">🔑 {r['usuario']} | 🖥️ {r['sistema']}</div></div><div class="dias-box"><span class="{cor}">{r['dias_res']} DIAS</span></div></div></a>''', unsafe_allow_html=True)

    with tab2:
        st.subheader("🚀 NOVO CADASTRO")
        with st.form("add_cli", clear_on_submit=True):
            ca1, ca2 = st.columns(2)
            nnome = ca1.text_input("NOME"); nuser = ca2.text_input("USUÁRIO")
            nsenha = ca1.text_input("SENHA"); nserv = ca2.selectbox("SERVIDOR", st.session_state.lista_servidores)
            nsist = ca1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0); nvenc = ca2.date_input("VENCIMENTO", value=hoje+timedelta(days=30), format="DD/MM/YYYY")
            ncusto = ca1.number_input("CUSTO", value=10.0); nmensal = ca2.number_input("MENSALIDADE", value=35.0)
            nwhats = ca1.text_input("WHATSAPP"); nobs = ca2.text_area("OBSERVAÇÃO"); nimg = st.file_uploader("LOGO", type=['png', 'jpg'])
            if st.form_submit_button("🚀 CADASTRAR"):
                prox_id = int(df['id'].max() + 1) if not df.empty else 1
                blob = base64.b64encode(nimg.read()).decode() if nimg else ""
                sheet.append_row([prox_id, nnome.upper(), nuser, nsenha, nserv, nsist, nvenc.strftime('%Y-%m-%d'), ncusto, nmensal, nwhats, nobs, blob])
                st.rerun()

    with tab3:
        if not st.session_state.modo_fila_ativo:
            st.subheader("🚨 COBRANÇAS EM MASSA")
            c_cols = st.columns(6)
            filtros = ["vencidos", "hoje", "1dia", "2dias", "3dias", "todos"]
            labels = ["❌ Vencidos", "📅 Hoje", "🌅 Amanhã", "⏳ 2 Dias", "⏳ 3 Dias", "🗓️ Todos"]
            for i, f in enumerate(filtros):
                if c_cols[i].button(labels[i]): st.session_state.filtro_f = f; st.rerun()
            
            filtro = st.session_state.filtro_f
            df_c = df
            if filtro == "vencidos": df_c = df[df['dias_res'] < 0]
            elif filtro == "hoje": df_c = df[df['dias_res'] == 0]
            elif filtro == "1dia": df_c = df[df['dias_res'] == 1]
            elif filtro == "2dias": df_c = df[df['dias_res'] == 2]
            elif filtro == "3dias": df_c = df[df['dias_res'] == 3]

            if not df_c.empty:
                sel_all = st.checkbox(f"✅ Selecionar todos ({len(df_c)})", key=f"sel_all_{filtro}")
                clientes_marcados = []
                for _, r in df_c.iterrows():
                    img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
                    cor = get_cor_classe(r['dias_res'])
                    with st.container():
                        c1, c2 = st.columns([0.5, 5.5])
                        if c1.checkbox("", value=sel_all, key=f"chk_{r['id']}"):
                            clientes_marcados.append(r.to_dict())
                        c2.markdown(f'<div class="cliente-card-html"><img src="{img}" class="img-servidor-card"><div class="info-container"><div class="nome-c">{r["nome"]}</div><div class="sub-info">{r["sistema"]}</div></div><div class="dias-box"><span class="{cor}">{r["dias_res"]} DIAS</span></div></div>', unsafe_allow_html=True)
                
                if st.button("🚀 INICIAR DISPARO EM MASSA", type="primary"):
                    if clientes_marcados:
                        st.session_state.clientes_selecionados = clientes_marcados
                        st.session_state.indice_fila = 0
                        st.session_state.modo_fila_ativo = True
                        st.rerun()
        else:
            # --- LÓGICA DO TEMPORIZADOR DE 10 SEGUNDOS ---
            fila = st.session_state.clientes_selecionados
            idx = st.session_state.indice_fila
            if idx < len(fila):
                r = fila[idx]
                st.info(f"Enviando: {idx + 1} de {len(fila)}")
                st.markdown(f"### Cliente Atual: **{r['nome']}**")
                
                msg_map = {
                    "vencidos": "🚨SUA ASSINATURA DE TV VENCEU !\n\nNÃO PREOCUPE, BASTA FAZER O PIX QUE REATIVAMOS PRA VOCÊ!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
                    "hoje": "⚠️SUA ASSINATURA DE TV VENCE HOJE ⏰! \n\nNÃO FIQUE SEM TV, BASTA FAZER O PIX QUE RENOVAMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
                    "1dia": "⚠️SUA ASSINATURA DE TV VENCE AMANHÃ ⏰! \n\nNÃO FIQUE SEM TV, FAÇA O PIX E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
                    "2dias": "⚠️SUA ASSINATURA DE TV VENCE EM 2️⃣ DIAS ⏰! \n\nFAÇA O PIX  AGORA E RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
                    "3dias": "⚠️SUA ASSINATURA DE TV VENCE EM 3️⃣ DIAS ⏰! \n\nFAÇA O PIX  AGORA E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
                    "todos": "Olá! Segue seu lembrete de renovação SUPERTV4K."
                }
                msg_atual = msg_map.get(st.session_state.filtro_f, msg_map["todos"])
                url_whats = f"https://wa.me/55{r['whatsapp']}?text={urllib.parse.quote(msg_atual)}"
                
                col1, col2, col3 = st.columns(3)
                if col1.link_button("📲 ABRIR WHATSAPP", url_whats, type="primary"):
                    st.session_state.em_disparo = True
                if col2.button("⏭️ PULAR"): 
                    st.session_state.indice_fila += 1
                    st.rerun()
                if col3.button("✖️ PARAR TUDO"): 
                    st.session_state.modo_fila_ativo = False
                    st.rerun()

                if st.session_state.em_disparo:
                    st.warning("⏱️ Aguardando 10 segundos para o próximo da fila...")
                    progresso = st.progress(0)
                    for i in range(10):
                        time.sleep(1)
                        progresso.progress((i + 1) * 10)
                    st.session_state.indice_fila += 1
                    st.session_state.em_disparo = False
                    st.rerun()
            else:
                st.success("✅ Todos os disparos foram processados!"); st.session_state.modo_fila_ativo = False
                if st.button("VOLTAR"): st.rerun()

    with tab4:
        st.subheader("⚙️ AJUSTES")
        if st.button("🔄 SINCRONIZAR"): st.rerun()
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.drop(columns=['dt_venc_calc', 'dias_res']).to_excel(writer, index=False)
        st.download_button("📥 BACKUP EXCEL", data=buffer.getvalue(), file_name="backup_supertv.xlsx")
