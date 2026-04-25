import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse
import base64
import io
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTV4K GESTÃO PRO", layout="wide")

# Inicialização de estados para evitar que a aba de cobrança fique vazia no primeiro carregamento
if 'filtro_f' not in st.session_state:
    st.session_state.filtro_f = "vencidos"

if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = ["Uniplay", "Mundo GF", "P2Braz", "Unitv", "Playtv", "P2Cine", "P2Speed", "Blade", "MegaTV", "Bob Player"]

# --- 2. ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 20px; }
    .logo-gestao { width: 400px; margin-bottom: -15px !important; }
    .logo-supertv { width: 350px; }
    .cobransa-item {
        background-color: #1c2128; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #00d4ff;
    }
    .vencido-border { border-left: 5px solid #ff4b4b !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE DADOS ---
def conectar_gs():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        # Verifique se o ID da planilha abaixo está correto
        return client.open_by_key("1ntE8RpofySu5IFupuvOZxZnrnmHKzaYbyqAQ-Mzc8so").sheet1
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return None

def carregar_dados(sheet):
    if sheet:
        valores = sheet.get_all_values()
        if len(valores) < 2: return pd.DataFrame()
        colunas = ["id", "nome", "usuario", "senha", "servidor", "sistema", "vencimento", "custo", "mensalidade", "whatsapp", "observacao", "logo_blob"]
        df = pd.DataFrame(valores[1:], columns=colunas[:len(valores[0])])
        
        # Correção de tipos e datas
        df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        # Tenta converter a data de vencimento (ajuste o formato se necessário na sua planilha)
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        return df[df['nome'].str.strip() != ""]
    return pd.DataFrame()

# --- 4. INTERFACE ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)
hoje = datetime.now().date()

if not df.empty:
    # Cálculo crucial para a aba de cobrança
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    with tab3:
        st.subheader("🚨 GESTÃO DE COBRANÇAS")
        
        # Botões de Filtro
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        if c1.button("❌ Vencidos"): st.session_state.filtro_f = "vencidos"
        if c2.button("📅 Hoje"): st.session_state.filtro_f = "hoje"
        if c3.button("🌅 Amanhã"): st.session_state.filtro_f = "1dia"
        if c4.button("⏳ 2 Dias"): st.session_state.filtro_f = "2dias"
        if c5.button("⏳ 3 Dias"): st.session_state.filtro_f = "3dias"
        if c6.button("🗓️ Todos"): st.session_state.filtro_f = "todos"

        filtro = st.session_state.filtro_f

        # Mensagens Oficiais
        mensagens = {
            "vencidos": "🚨SUA ASSINATURA DE TV VENCEU !\n\nNÃO PREOCUPE, BASTA FAZER O PIX QUE REATIVAMOS PRA VOCÊ!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "hoje": "⚠️SUA ASSINATURA DE TV VENCE HOJE ⏰! \n\nNÃO FIQUE SEM TV, BASTA FAZER O PIX QUE RENOVAMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "1dia": "⚠️SUA ASSINATURA DE TV VENCE AMANHÃ ⏰! \n\nNÃO FIQUE SEM TV, FAÇA O PIX E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "2dias": "⚠️SUA ASSINATURA DE TV VENCE EM 2️⃣ DIAS ⏰! \n\nFAÇA O PIX  AGORA E RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "3dias": "⚠️SUA ASSINATURA DE TV VENCE EM 3️⃣ DIAS ⏰! \n\nFAÇA O PIX  AGORA E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!"
        }

        # Filtragem dinâmica
        if filtro == "vencidos": df_c = df[df['dias_res'] < 0]; msg_atual = mensagens["vencidos"]
        elif filtro == "hoje": df_c = df[df['dias_res'] == 0]; msg_atual = mensagens["hoje"]
        elif filtro == "1dia": df_c = df[df['dias_res'] == 1]; msg_atual = mensagens["1dia"]
        elif filtro == "2dias": df_c = df[df['dias_res'] == 2]; msg_atual = mensagens["2dias"]
        elif filtro == "3dias": df_c = df[df['dias_res'] == 3]; msg_atual = mensagens["3dias"]
        else: df_c = df; msg_atual = "Lembrete SUPERTV4K"

        st.info(f"Filtro ativo: {filtro.upper()} | {len(df_c)} clientes encontrados.")

        if not df_c.empty:
            col_sel, _ = st.columns([2, 4])
            selecionar_todos = col_sel.checkbox("✅ Selecionar Todos da Lista")

            clientes_selecionados = []
            for _, r in df_c.iterrows():
                with st.container():
                    c_ch, c_inf, c_z = st.columns([0.4, 4, 1.6])
                    is_sel = c_ch.checkbox("", value=selecionar_todos, key=f"cob_{r['id']}")
                    if is_sel: clientes_selecionados.append(r)
                    
                    border = "vencido-border" if r['dias_res'] < 0 else ""
                    c_inf.markdown(f"""
                    <div class="cobransa-item {border}">
                        <strong>{r['nome']}</strong> - {r['servidor']}<br>
                        <small>Vencimento: {r['vencimento']} ({r['dias_res']} dias)</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    link = f"https://wa.me/55{r['whatsapp']}?text={urllib.parse.quote(msg_atual)}"
                    c_z.link_button("📲 ENVIAR", link)
            
            if clientes_selecionados:
                if st.button("📢 GERAR LINKS EM MASSA"):
                    for sel in clientes_selecionados:
                        st.write(f"👉 **{sel['nome']}**: https://wa.me/55{sel['whatsapp']}?text={urllib.parse.quote(msg_atual)}")
        else:
            st.warning("Nenhum cliente encontrado para este filtro.")

else:
    st.error("Planilha vazia ou não conectada. Verifique os dados no Google Sheets.")
