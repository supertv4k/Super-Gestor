import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse
import base64
import time

# --- 1. CONFIGURAÇÃO E ESTADO ---
st.set_page_config(page_title="SUPERTV4K GESTÃO PRO", layout="wide")

if 'filtro_f' not in st.session_state:
    st.session_state.filtro_f = "vencidos"

# --- 2. AS 5 MENSAGENS DETALHADAS (RECUPERADAS) ---
def obter_mensagens_oficiais(nome_cliente):
    pix = "💠 *PIX CNPJ:* `62.326.879/0001-13`\n*SUPERTV4K PRO*"
    rodape = "\n\n⚠️ *NÃO ESQUEÇA DE ENVIAR O COMPROVANTE!*"
    
    msg_map = {
        "vencidos": f"🚨 *AVISO DE BLOQUEIO - SUPERTV4K*\n\nOlá *{nome_cliente}*, identificamos que sua assinatura *VENCEU* e o sinal foi interrompido. Para reativar agora, realize o pagamento abaixo:\n\n💰 *VALOR:* R$ 35,00\n{pix}{rodape}",
        
        "hoje": f"⏰ *VENCE HOJE! - SUPERTV4K*\n\nOlá *{nome_cliente}*, sua assinatura vence hoje! Não deixe para a última hora e evite interrupções no seu sinal.\n\n💰 *VALOR:* R$ 35,00\n{pix}{rodape}",
        
        "1dia": f"⏳ *VENCE AMANHÃ! - SUPERTV4K*\n\nOlá *{nome_cliente}*, passando para lembrar que sua assinatura vence *AMANHÃ*. Garanta sua renovação!\n\n💰 *VALOR:* R$ 35,00\n{pix}{rodape}",
        
        "2dias": f"🗓️ *LEMBRETE DE RENOVAÇÃO*\n\nOlá *{nome_cliente}*, sua assinatura SUPERTV4K vence em *2 DIAS*. Já deixamos tudo pronto para sua renovação.\n\n💰 *VALOR:* R$ 35,00\n{pix}{rodape}",
        
        "3dias": f"💡 *AVISO ANTECIPADO*\n\nOlá *{nome_cliente}*, sua assinatura vence em *3 DIAS*. Programe-se para não ficar sem o melhor do streaming!\n\n💰 *VALOR:* R$ 35,00\n{pix}{rodape}",
        
        "todos": f"Olá *{nome_cliente}*, aqui está seu lembrete de renovação SUPERTV4K.\n\n{pix}{rodape}"
    }
    return msg_map

# --- 3. ESTILO CSS (4K / CYBERPUNK) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .metric-value { font-size: 22px; color: #00d4ff; font-weight: 900; }
    .cliente-card-html { display: flex; align-items: center; background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 15px; margin-bottom: 10px; }
    .img-servidor-card { width: 60px; height: 60px; border-radius: 10px; margin-right: 15px; border: 1px solid #444; }
    .nome-c { font-weight: 900; font-size: 17px; text-transform: uppercase; color: #fff; }
    .cor-vencido { color: #FF4B4B; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNÇÕES DE DADOS ---
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

sheet = conectar_gs()
df = carregar_dados(sheet)
hoje = datetime.now().date()

# --- 5. INTERFACE ---
st.markdown("""<div style="text-align:center; margin-bottom:20px;"><img src="https://i.imgur.com/CKq9BVx.png" width="350"></div>""", unsafe_allow_html=True)

if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    # Lógica de Edição Completa
    qp = st.query_params
    if "editar_id" in qp:
        sel = df[df['id'].astype(str) == str(qp["editar_id"])]
        if not sel.empty:
            c = sel.iloc[0].to_dict()
            st.markdown(f"### 📝 EDITANDO: {c['nome']}")
            with st.form("form_edit"):
                col1, col2 = st.columns(2)
                enome = col1.text_input("NOME", value=c['nome'])
                euser = col2.text_input("USUÁRIO", value=c['usuario'])
                eserv = col1.selectbox("SERVIDOR", ["Uniplay", "Mundo GF", "P2Braz", "Unitv", "Playtv", "P2Cine", "P2Speed", "Blade", "MegaTV", "Bob Player", "Ibo Player", "Ibo Pro Player"], index=0)
                ewhats = col2.text_input("WHATSAPP", value=c['whatsapp'])
                evenc = col1.date_input("VENCIMENTO", value=pd.to_datetime(c['vencimento']).date())
                eobs = col2.text_area("OBSERVAÇÃO", value=c['observacao'])
                if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                    # Aqui você completa a atualização na planilha conforme o ID
                    st.query_params.clear(); st.rerun()
            st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ CADASTRAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    with tab1:
        busca = st.text_input("🔎 Pesquisar cliente...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            cor = "#FF4B4B" if r['dias_res'] < 0 else "#00D4FF"
            st.markdown(f'''<a href="/?editar_id={r['id']}" target="_self" style="text-decoration:none;"><div class="cliente-card-html"><img src="{img}" class="img-servidor-card"><div class="info-container"><div class="nome-c">{r['nome']}</div><span style="color:#8b949e;">{r['servidor']} | {r['sistema']}</span></div><div style="text-align:right; margin-left:auto;"><span style="color:{cor}; font-weight:bold;">{r['dias_res']} DIAS</span></div></div></a>''', unsafe_allow_html=True)

    with tab3:
        st.subheader("🚨 FILA DE DISPARO (MENSAGENS DETALHADAS)")
        
        # Botões de Filtro
        f_cols = st.columns(6)
        filtros = ["vencidos", "hoje", "1dia", "2dias", "3dias", "todos"]
        labels = ["❌ Vencidos", "📅 Hoje", "🌅 Amanhã", "⏳ 2 Dias", "⏳ 3 Dias", "🗓️ Todos"]
        for i, f in enumerate(filtros):
            if f_cols[i].button(labels[i]): st.session_state.filtro_f = f
        
        filtro = st.session_state.filtro_f
        
        # Filtragem do DF
        if filtro == "vencidos": df_c = df[df['dias_res'] < 0]
        elif filtro == "hoje": df_c = df[df['dias_res'] == 0]
        elif filtro == "1dia": df_c = df[df['dias_res'] == 1]
        elif filtro == "2dias": df_c = df[df['dias_res'] == 2]
        elif filtro == "3dias": df_c = df[df['dias_res'] == 3]
        else: df_c = df

        st.info(f"Lista de: **{filtro.upper()}** ({len(df_c)} clientes)")

        for _, r in df_c.iterrows():
            # RECUPERA A MENSAGEM DETALHADA QUE VOCÊ CRIOU
            mensagens = obter_mensagens_oficiais(r['nome'])
            texto_final = mensagens.get(filtro, mensagens["todos"])
            
            url_w = f"https://api.whatsapp.com/send?phone=55{r['whatsapp']}&text={urllib.parse.quote(texto_final)}"
            
            with st.container():
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{r['nome']}** ({r['dias_res']} dias)")
                c2.link_button("📲 ENVIAR", url_w, use_container_width=True)
            st.divider()

    with tab4:
        st.subheader("⚙️ AJUSTES")
        if st.button("🔄 ATUALIZAR PLANILHA"): st.rerun()
