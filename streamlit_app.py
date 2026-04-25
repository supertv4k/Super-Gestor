import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse
import base64
import io

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="SUPERTV4K GESTÃO PRO", layout="wide")

if 'filtro_f' not in st.session_state:
    st.session_state.filtro_f = "vencidos"

if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = ["Uniplay", "Mundo GF", "P2Braz", "Unitv", "Playtv", "P2Cine", "P2Speed", "Blade", "MegaTV", "Bob Player", "Ibo Player", "Ibo Pro Player"]

# --- 2. ESTILIZAÇÃO CSS (ESTILO CYBERPUNK/4K) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; margin-bottom: 20px; }
    .logo-gestao { width: 380px; margin-bottom: -15px !important; }
    .logo-supertv { width: 320px; }
    
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; margin-bottom: 20px; }
    .metric-label { font-size: 12px; color: #8b949e; font-weight: bold; text-transform: uppercase; }
    .metric-value { font-size: 20px; color: #00d4ff; font-weight: 900; }

    .cliente-card-html {
        display: flex; align-items: center; background-color: #161b22;
        border: 1px solid #30363d; border-radius: 12px; padding: 12px;
        min-height: 80px; width: 100%; transition: 0.2s;
    }
    
    .img-servidor-card { width: 50px; height: 50px; border-radius: 8px; object-fit: cover; margin-right: 12px; border: 1px solid #444; flex-shrink: 0; }
    .info-container { flex-grow: 1; display: flex; flex-direction: column; justify-content: center; min-width: 0; }
    .nome-c { font-weight: 900; font-size: 15px; color: white; text-transform: uppercase; word-wrap: break-word; line-height: 1.1; margin-bottom: 2px; }
    
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

if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)

# --- 4. INTERFACE PRINCIPAL ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

if not df.empty:
    # Métricas
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-card"><div class="metric-label">Ativos</div><div class="metric-value">{len(df[df["dias_res"]>=0])}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">Vencidos</div><div class="metric-value" style="color:red">{len(df[df["dias_res"]<0])}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-label">Vence Hoje</div><div class="metric-value" style="color:orange">{len(df[df["dias_res"]==0])}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-label">Lucro</div><div class="metric-value" style="color:green">R$ {(df["mensalidade"].sum() - df["custo"].sum()):.2f}</div></div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    with tab1:
        busca = st.text_input("🔎 BUSCAR CLIENTE...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            cor = get_cor_classe(r['dias_res'])
            st.markdown(f'''<div class="cliente-card-html"><img src="{img}" class="img-servidor-card"><div class="info-container"><div class="nome-c">{r['nome']}</div><span style="color:#8b949e; font-size:13px;">🔑 {r['usuario']} | 🖥️ {r['sistema']}</span></div><div class="dias-box" style="text-align:right;"><span class="{cor}" style="font-size:15px;">{r['dias_res']} DIAS</span><br><small style="color:#8b949e;">{r['dt_venc_calc'].strftime('%d/%m/%Y')}</small></div></div>''', unsafe_allow_html=True)
            st.write("")

    with tab2:
        st.subheader("🚀 NOVO CADASTRO")
        with st.form("add_cli", clear_on_submit=True):
            ca1, ca2 = st.columns(2)
            nnome = ca1.text_input("NOME")
            nwhats = ca2.text_input("WHATSAPP (Ex: 11999998888)")
            nserv = ca1.selectbox("SERVIDOR", sorted(st.session_state.lista_servidores))
            nuser = ca2.text_input("USUÁRIO")
            if st.form_submit_button("🚀 CADASTRAR"):
                prox_id = int(df['id'].max() + 1) if not df.empty else 1
                sheet.append_row([prox_id, nnome.upper(), nuser, "", nserv, "P2P", (hoje + timedelta(days=30)).strftime('%Y-%m-%d'), 10, 35, nwhats, "", ""])
                st.rerun()

    with tab3:
        st.subheader("🚨 COBRANÇA RÁPIDA (LG K41S)")
        
        # Filtros das Mensagens
        f_cols = st.columns(6)
        filtros = ["vencidos", "hoje", "1dia", "2dias", "3dias", "todos"]
        labels = ["❌ Vencidos", "📅 Hoje", "🌅 Amanhã", "⏳ 2 Dias", "⏳ 3 Dias", "🗓️ Todos"]
        
        for i, f in enumerate(filtros):
            if f_cols[i].button(labels[i]): 
                st.session_state.filtro_f = f

        # Configuração das 5 MENSAGENS específicas
        cnpj_pix = "\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!"
        
        msg_map = {
            "vencidos": "🚨SUA ASSINATURA DE TV VENCEU !" + cnpj_pix,
            "hoje": "⚠️SUA ASSINATURA DE TV VENCE HOJE ⏰!" + cnpj_pix,
            "1dia": "⚠️SUA ASSINATURA DE TV VENCE AMANHÃ ⏰!" + cnpj_pix,
            "2dias": "⚠️SUA ASSINATURA DE TV VENCE EM 2️⃣ DIAS ⏰!" + cnpj_pix,
            "3dias": "⚠️SUA ASSINATURA DE TV VENCE EM 3️⃣ DIAS ⏰!" + cnpj_pix,
            "todos": "Olá! Segue seu lembrete de renovação SUPERTV4K."
        }
        
        filtro_atual = st.session_state.filtro_f
        msg_para_enviar = msg_map.get(filtro_atual, msg_map["todos"])
        
        # Filtragem do DataFrame conforme o botão clicado
        if filtro_atual == "vencidos": df_c = df[df['dias_res'] < 0]
        elif filtro_atual == "hoje": df_c = df[df['dias_res'] == 0]
        elif filtro_atual == "1dia": df_c = df[df['dias_res'] == 1]
        elif filtro_atual == "2dias": df_c = df[df['dias_res'] == 2]
        elif filtro_atual == "3dias": df_c = df[df['dias_res'] == 3]
        else: df_c = df

        st.write(f"Filtrado por: **{filtro_atual.upper()}** ({len(df_c)} clientes)")

        if not df_c.empty:
            for _, r in df_c.iterrows():
                url_w = f"https://api.whatsapp.com/send?phone=55{r['whatsapp']}&text={urllib.parse.quote(msg_para_enviar)}"
                
                with st.container():
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        cor = get_cor_classe(r['dias_res'])
                        st.markdown(f'''<div class="cliente-card-html" style="border:none; padding:0; background:none;"><div class="info-container"><div class="nome-c">{r['nome']}</div><span class="{cor}">{r['dias_res']} DIAS</span></div></div>''', unsafe_allow_html=True)
                    with c2:
                        st.link_button("📲 ENVIAR", url_w, use_container_width=True)
                st.divider()

    with tab4:
        st.subheader("⚙️ AJUSTES")
        if st.button("🔄 ATUALIZAR/SINCRONIZAR"): st.rerun()
