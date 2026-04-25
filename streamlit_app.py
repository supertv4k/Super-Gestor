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

if 'indice_fila' not in st.session_state:
    st.session_state.indice_fila = 0
if 'filtro_f' not in st.session_state:
    st.session_state.filtro_f = "vencidos"
if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = ["Uniplay", "Mundo GF", "P2Braz", "Unitv", "Playtv", "P2Cine", "P2Speed", "Blade", "MegaTV", "Bob Player", "Ibo Player", "Ibo Pro Player"]

# --- 2. ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; margin-bottom: 20px; }
    .metric-value { font-size: 20px; color: #00d4ff; font-weight: 900; }
    .cliente-card-html { display: flex; align-items: center; background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 15px; margin-bottom: 10px; }
    .img-servidor-card { width: 60px; height: 60px; border-radius: 10px; margin-right: 15px; }
    .nome-c { font-weight: 900; font-size: 17px; text-transform: uppercase; }
    .cor-vencido { color: #FF4B4B; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXÃO E DADOS ---
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

# --- 4. DASHBOARD E TABS ---
st.markdown("""<div style="text-align:center"><img src="https://i.imgur.com/CKq9BVx.png" width="300"></div>""", unsafe_allow_html=True)

if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    # Lógica de Edição (Se houver query param)
    qp = st.query_params
    if "editar_id" in qp:
        sel = df[df['id'].astype(str) == str(qp["editar_id"])]
        if not sel.empty:
            c = sel.iloc[0].to_dict()
            with st.expander("📝 EDITAR CLIENTE SELECIONADO", expanded=True):
                with st.form("edit_form"):
                    col1, col2 = st.columns(2)
                    enome = col1.text_input("NOME", value=c['nome'])
                    euser = col2.text_input("USUÁRIO", value=c['usuario'])
                    eserv = col1.selectbox("SERVIDOR", sorted(st.session_state.lista_servidores), index=0)
                    ewhats = col2.text_input("WHATSAPP", value=c['whatsapp'])
                    if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                        # Lógica de salvar na planilha aqui...
                        st.query_params.clear(); st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ CADASTRAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    with tab1:
        busca = st.text_input("🔎 Buscar...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            st.markdown(f'''<a href="/?editar_id={r['id']}" target="_self" style="text-decoration:none; color:inherit;"><div class="cliente-card-html"><img src="{img}" class="img-servidor-card"><div class="info-container"><div class="nome-c">{r['nome']}</div><span style="color:#8b949e;">{r['usuario']}</span></div><div style="margin-left:auto; text-align:right;"><span class="cor-vencido">{r['dias_res']} DIAS</span></div></div></a>''', unsafe_allow_html=True)

    with tab3:
        st.subheader("🚨 FILA DE COBRANÇA SEGURA")
        
        # Filtros e Mensagens
        f_cols = st.columns(6)
        filtros = ["vencidos", "hoje", "1dia", "2dias", "3dias", "todos"]
        labels = ["❌ Vencidos", "📅 Hoje", "🌅 Amanhã", "⏳ 2 Dias", "⏳ 3 Dias", "🗓️ Todos"]
        for i, f in enumerate(filtros):
            if f_cols[i].button(labels[i]): 
                st.session_state.filtro_f = f
                st.session_state.indice_fila = 0 # Reseta a fila ao mudar filtro

        # Mensagens conforme você pediu
        cnpj_pix = "\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA O COMPROVANTE!"
        msg_map = {
            "vencidos": "🚨SUA ASSINATURA DE TV VENCEU !" + cnpj_pix,
            "hoje": "⚠️SUA ASSINATURA DE TV VENCE HOJE ⏰!" + cnpj_pix,
            "1dia": "⚠️SUA ASSINATURA DE TV VENCE AMANHÃ ⏰!" + cnpj_pix,
            "2dias": "⚠️SUA ASSINATURA DE TV VENCE EM 2️⃣ DIAS ⏰!" + cnpj_pix,
            "3dias": "⚠️SUA ASSINATURA DE TV VENCE EM 3️⃣ DIAS ⏰!" + cnpj_pix,
            "todos": "Olá! Segue seu lembrete de renovação SUPERTV4K."
        }
        
        msg_atual = msg_map.get(st.session_state.filtro_f, msg_map["todos"])
        
        # Filtrar DF para a fila
        if st.session_state.filtro_f == "vencidos": df_fila = df[df['dias_res'] < 0]
        elif st.session_state.filtro_f == "hoje": df_fila = df[df['dias_res'] == 0]
        elif st.session_state.filtro_f == "1dia": df_fila = df[df['dias_res'] == 1]
        elif st.session_state.filtro_f == "2dias": df_fila = df[df['dias_res'] == 2]
        elif st.session_state.filtro_f == "3dias": df_fila = df[df['dias_res'] == 3]
        else: df_fila = df

        if not df_fila.empty:
            idx = st.session_state.indice_fila
            if idx < len(df_fila):
                cliente = df_fila.iloc[idx]
                
                st.warning(f"Processando: {idx + 1} de {len(df_fila)}")
                
                # Card do Cliente Atual
                st.markdown(f'''<div class="cliente-card-html"><div class="info-container"><div class="nome-c">{cliente['nome']}</div><span>WhatsApp: {cliente['whatsapp']}</span></div></div>''', unsafe_allow_html=True)
                
                url_zap = f"https://api.whatsapp.com/send?phone=55{cliente['whatsapp']}&text={urllib.parse.quote(msg_atual)}"
                
                col_btn1, col_btn2 = st.columns(2)
                
                if col_btn1.link_button(f"📲 ENVIAR PARA {cliente['nome']}", url_zap, use_container_width=True, type="primary"):
                    st.session_state.indice_fila += 1
                    # Simula o tempo de espera antes de liberar o próximo
                    with st.spinner("Aguardando 10 segundos de segurança..."):
                        time.sleep(10)
                    st.rerun()

                if col_btn2.button("⏭️ PULAR CLIENTE", use_container_width=True):
                    st.session_state.indice_fila += 1
                    st.rerun()
                
                if st.button("🔄 RECOMEÇAR FILA"):
                    st.session_state.indice_fila = 0
                    st.rerun()
            else:
                st.success("✅ Fila concluída! Todos os clientes do filtro foram processados.")
                if st.button("RECOMEÇAR"):
                    st.session_state.indice_fila = 0
                    st.rerun()
        else:
            st.info("Nenhum cliente encontrado para este filtro.")

    with tab4:
        st.subheader("⚙️ AJUSTES")
        if st.button("🔄 Sincronizar Agora"): st.rerun()
