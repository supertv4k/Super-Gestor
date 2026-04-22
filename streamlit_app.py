import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse
import io
import base64

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS (Padrão Gilmar) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    .metric-container { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .metric-label { color: white; font-size: 14px; font-weight: bold; margin-bottom: 5px; }
    .val-azul { color: #00d4ff; font-size: 24px; font-weight: bold; }
    .val-verde { color: #28a745; font-size: 24px; font-weight: bold; }
    .val-laranja { color: #ffa500; font-size: 24px; font-weight: bold; }
    .val-vermelho { color: #ff4b4b; font-size: 24px; font-weight: bold; }
    .val-lucro { color: #00ff88; font-size: 24px; font-weight: bold; }
    .img-servidor { width: 55px; height: 55px; border-radius: 8px; object-fit: cover; border: 1px solid #444; }
    div.stButton > button { text-align: left !important; background-color: #161b22 !important; border: 1px solid #30363d !important; color: white !important; border-radius: 12px !important; padding: 12px !important; width: 100%; }
    .edit-panel { background-color: #1c2128; padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXÃO E FUNÇÕES ---
def conectar_gs():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1ntE8RpofySu5IFupuvOZxZnrnmHKzaYbyqAQ-Mzc8so").sheet1
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

def format_data_br(data_str):
    try: 
        return datetime.strptime(str(data_str), '%Y-%m-%d').strftime('%d/%m/%Y')
    except: 
        return data_str

def carregar_dados(sheet):
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame(columns=["id", "nome", "usuario", "senha", "servidor", "sistema", "vencimento", "custo", "mensalidade", "whatsapp", "observacao", "logo_blob"])
        # Correção: Remove linhas vazias ou de controle (evita o erro do +1)
        df = df[df['nome'].astype(str).str.strip() != ""]
        return df
    return pd.DataFrame()

if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = ["UNIPLAY", "MUNDO GF", "P2BRAZ", "UNITV", "PLAYTV", "P2CINE", "P2SPEED", "BLADE", "MEGATV", "BOB PLAYER", "IBO PLAYER", "IBO PRO PLAYER", "OUTROS"]

if 'cliente_selecionado' not in st.session_state:
    st.session_state.cliente_selecionado = None

# --- 4. CABEÇALHO E MÉTRICAS ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)

if not df.empty:
    hoje = datetime.now().date()
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    df_ativos = df[df['dias_res'] >= 0]
    
    lucro = pd.to_numeric(df_ativos['mensalidade'], errors='coerce').sum() - pd.to_numeric(df_ativos['custo'], errors='coerce').sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.markdown(f'<div class="metric-container"><div class="metric-label">TOTAL</div><div class="val-azul">{len(df)}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-container"><div class="metric-label">ATIVOS</div><div class="val-verde">{len(df_ativos)}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-container"><div class="metric-label">HOJE</div><div class="val-laranja">{len(df[df["dias_res"] == 0])}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-container"><div class="metric-label">VENCIDOS</div><div class="val-vermelho">{len(df[df["dias_res"] < 0])}</div></div>', unsafe_allow_html=True)
    m5.markdown(f'<div class="metric-container"><div class="metric-label">LUCRO</div><div class="val-lucro">R$ {lucro:,.2f}</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ NOVO", "🚨 COBRANÇA", "⚙️ AJUSTES"])

# --- TAB 1: LISTAGEM E EDIÇÃO ---
with tab1:
    if st.session_state.cliente_selecionado is not None:
        c = st.session_state.cliente_selecionado
        with st.form("edit_form"):
            st.markdown(f"### Editando: {c.get('nome', '')}")
            col1, col2, col3 = st.columns(3)
            en_nome = col1.text_input("Nome", value=c.get('nome'))
            en_user = col2.text_input("Usuário", value=c.get('usuario'))
            en_venc = col3.date_input("Vencimento", value=pd.to_datetime(c.get('vencimento')).date(), format="DD/MM/YYYY")
            if st.form_submit_button("SALVAR"):
                ids = sheet.col_values(1)
                row_idx = ids.index(str(c['id'])) + 1
                sheet.update_cell(row_idx, 2, en_nome)
                sheet.update_cell(row_idx, 3, en_user)
                sheet.update_cell(row_idx, 7, en_venc.strftime('%Y-%m-%d'))
                st.session_state.cliente_selecionado = None
                st.rerun()

    busca = st.text_input("🔎 Pesquisar...")
    df_f = df[df['nome'].str.contains(busca, case=False, na=False)] if busca else df
    for _, r in df_f.sort_values(by='dias_res').iterrows():
        label = f"{str(r.get('nome','')).upper()} | 🔑 {r.get('usuario','')} | 📅 {format_data_br(r.get('vencimento'))}"
        if st.button(label, key=f"btn_{r['id']}"):
            st.session_state.cliente_selecionado = r.to_dict()
            st.rerun()

# --- TAB 3: COBRANÇA (Suas Mensagens) ---
with tab3:
    st.subheader("🚨 Central de Cobrança")
    pix_cnpj = "62.326.879/0001-13"
    
    filtro = st.radio("Prazo:", ["Todos", "Vencidos", "Hoje", "Amanhã", "2 Dias", "3 Dias"], horizontal=True)
    
    # Mapeamento de filtros
    if filtro == "Vencidos": df_c = df[df['dias_res'] < 0]
    elif filtro == "Hoje": df_c = df[df['dias_res'] == 0]
    elif filtro == "Amanhã": df_c = df[df['dias_res'] == 1]
    elif filtro == "2 Dias": df_c = df[df['dias_res'] == 2]
    elif filtro == "3 Dias": df_c = df[df['dias_res'] == 3]
    else: df_c = df[df['dias_res'] <= 3]

    sel_todos = st.checkbox("Selecionar Todos")
    
    for _, cli in df_c.iterrows():
        dias = cli['dias_res']
        nome_c = str(cli.get('nome','')).upper()
        
        if st.checkbox(f"{nome_c} ({format_data_br(cli['vencimento'])})", value=sel_todos, key=f"cb_{cli['id']}"):
            # Definição da Mensagem baseada no prazo (Suas Mensagens Oficiais)
            if dias < 0:
                msg = f"🚨 *{nome_c}, SUA ASSINATURA DE TV VENCEU !*\n\nNÃO PREOCUPE, BASTA FAZER O PIX QUE REATIVAMOS PRA VOCÊ!\n\n💠PIX CNPJ\n{pix_cnpj}\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!"
            elif dias == 0:
                msg = f"⚠️ *{nome_c}, SUA ASSINATURA DE TV VENCE HOJE ⏰!*\n\nNÃO FIQUE SEM TV, BASTA FAZER O PIX QUE RENOVAMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n{pix_cnpj}\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!"
            elif dias == 1:
                msg = f"⚠️ *{nome_c}, SUA ASSINATURA DE TV VENCE AMANHÃ ⏰!*\n\nNÃO FIQUE SEM TV, FAÇA O PIX E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n{pix_cnpj}\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!"
            elif dias == 2:
                msg = f"⚠️ *{nome_c}, SUA ASSINATURA DE TV VENCE EM 2️⃣ DIAS ⏰!*\n\nFAÇA O PIX AGORA E RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n{pix_cnpj}\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!"
            else:
                msg = f"⚠️ *{nome_c}, SUA ASSINATURA DE TV VENCE EM 3️⃣ DIAS ⏰!*\n\nFAÇA O PIX AGORA E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n{pix_cnpj}\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!"
            
            st.link_button(f"📲 Enviar para {nome_c}", f"https://wa.me/55{cli['whatsapp']}?text={urllib.parse.quote(msg)}")

# --- TAB 4: AJUSTES (Botões Restaurados) ---
with tab4:
    st.subheader("⚙️ Ajustes")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔄 Sincronizar Google Sheets"):
            st.cache_data.clear()
            st.rerun()
        
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Backup Excel", data=csv, file_name="backup_clientes.csv", mime="text/csv")
        
    with col_b:
        st.markdown("### Servidores")
        novos_servs = st.text_area("Um por linha:", value="\n".join(st.session_state.lista_servidores))
        if st.button("Atualizar Servidores"):
            st.session_state.lista_servidores = novos_servs.split("\n")
            st.success("Lista atualizada!")
