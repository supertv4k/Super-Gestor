import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse
import unicodedata
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 20px; }
    .logo-gestao { width: 400px; margin-bottom: -15px !important; }
    .logo-supertv { width: 350px; }
    
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .metric-label { font-size: 14px; color: #8b949e; font-weight: bold; }
    .metric-value { font-size: 22px; color: #00d4ff; font-weight: 900; }
    .lucro { color: #00ff7f; }

    .cliente-card {
        display: flex; align-items: center; background-color: #161b22;
        border: 1px solid #30363d; border-radius: 8px; padding: 10px 15px;
        margin-bottom: -72px; position: relative; z-index: 1;
    }
    .img-padrao { width: 55px; height: 55px; border-radius: 8px; margin-right: 20px; background-color: #00d4ff; display: flex; align-items: center; justify-content: center; font-weight: bold; color: black; font-size: 20px; }
    .info-text { display: flex; flex-direction: column; width: 100%; }
    .linha-topo { display: flex; justify-content: space-between; align-items: center; margin-right: 15px; }
    .nome-c { font-weight: 900; font-size: 17px; color: white; text-transform: uppercase; }
    .dias-destaque { font-weight: 900; font-size: 15px; color: #00d4ff; text-transform: uppercase; }
    .vencido { color: #ff4b4b; }

    div.stButton > button {
        width: 100% !important; height: 75px !important;
        background-color: transparent !important; border: 1px solid transparent !important;
        color: transparent !important; position: relative; z-index: 10; cursor: pointer;
    }
    div.stButton > button:hover { border: 1px solid #00d4ff !important; background-color: rgba(0, 212, 255, 0.05) !important; }

    .edit-panel { background-color: #1c2128; padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE SUPORTE ---
def remover_acentos(texto):
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').upper().strip()

def conectar_gs():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1ntE8RpofySu5IFupuvOZxZnrnmHKzaYbyqAQ-Mzc8so").sheet1
    except: return None

def carregar_dados(sheet):
    if sheet:
        valores = sheet.get_all_values()
        if not valores: return pd.DataFrame()
        
        # Limpa os nomes das colunas (tira acento, espaço e deixa maiúsculo)
        colunas_limpas = [remover_acentos(c) for c in valores[0]]
        df = pd.DataFrame(valores[1:], columns=colunas_limpas)
        
        # Conversão de valores
        if 'CUSTO' in df.columns: df['CUSTO'] = pd.to_numeric(df['CUSTO'].str.replace(',', '.'), errors='coerce').fillna(0)
        if 'MENSALIDADE' in df.columns: df['MENSALIDADE'] = pd.to_numeric(df['MENSALIDADE'].str.replace(',', '.'), errors='coerce').fillna(0)
        if 'VENCIMENTO' in df.columns: df['DT_VENC_CALC'] = pd.to_datetime(df['VENCIMENTO'], errors='coerce').dt.date
        
        return df[df['NOME'].astype(str).str.strip() != ""]
    return pd.DataFrame()

# --- 4. INTERFACE ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)
hoje = datetime.now().date()

if not df.empty:
    df['DIAS_RES'] = df['DT_VENC_CALC'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    # --- MÉTRICAS ---
    ativos = len(df[df['DIAS_RES'] >= 0])
    vencidos = len(df[df['DIAS_RES'] < 0])
    lucro = df['MENSALIDADE'].sum() - df['CUSTO'].sum()

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-card"><div class="metric-label">👤 ATIVOS</div><div class="metric-value">{ativos}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">❌ VENCIDOS</div><div class="metric-value" style="color:#ff4b4b">{vencidos}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-label">📅 HOJE</div><div class="metric-value">{len(df[df["DIAS_RES"] == 0])}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-label">💰 LUCRO LÍQUIDO</div><div class="metric-value lucro">R$ {lucro:,.2f}</div></div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    # --- TAB 1: CLIENTES ---
    with tab1:
        if st.session_state.get('cliente_selecionado') is not None:
            c = st.session_state.cliente_selecionado
            st.markdown(f'<div class="edit-panel"><h3>📝 EDITAR: {str(c.get("NOME")).upper()}</h3></div>', unsafe_allow_html=True)
            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                en_nome = col1.text_input("NOME", value=c.get('NOME', ''))
                en_user = col2.text_input("USUÁRIO", value=c.get('USUARIO', '')) # Sem acento na chave do dicionário
                en_senha = col1.text_input("SENHA", value=c.get('SENHA', ''))
                en_serv = col2.text_input("SERVIDOR", value=c.get('SERVIDOR', ''))
                en_sist = col1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if c.get('SISTEMA') == "P2P" else 1)
                en_venc = col2.date_input("VENCIMENTO", value=pd.to_datetime(c.get('VENCIMENTO')).date(), format="DD/MM/YYYY")
                en_custo = col1.number_input("CUSTO", value=float(c.get('CUSTO', 0)))
                en_mensal = col2.number_input("MENSALIDADE", value=float(c.get('MENSALIDADE', 0)))
                en_whats = col1.text_input("WHATSAPP", value=c.get('WHATSAPP', ''))
                en_obs = col2.text_area("OBSERVAÇÃO", value=c.get('OBSERVACAO', ''))
                
                b1, b2, b3 = st.columns(3)
                if b1.form_submit_button("💾 SALVAR"):
                    row = sheet.col_values(1).index(c['NOME']) + 1
                    sheet.update(range_name=f'A{row}:J{row}', values=[[en_nome.upper(), en_user, en_senha, en_serv.upper(), en_sist, en_venc.strftime('%Y-%m-%d'), en_custo, en_mensal, en_whats, en_obs]])
                    st.session_state.cliente_selecionado = None
                    st.rerun()
                if b2.form_submit_button("🗑️ EXCLUIR"):
                    sheet.delete_rows(sheet.col_values(1).index(c['NOME']) + 1)
                    st.session_state.cliente_selecionado = None
                    st.rerun()
                if b3.form_submit_button("✖️ FECHAR"):
                    st.session_state.cliente_selecionado = None
                    st.rerun()

        busca = st.text_input("🔎 PESQUISAR CLIENTE...")
        df_f = df[df['NOME'].str.contains(busca, case=False, na=False)] if busca else df
        
        for _, r in df_f.sort_values(by='DIAS_RES').iterrows():
            dias = r['DIAS_RES']
            txt_dias = f"VENCIDO HÁ {abs(dias)} DIAS" if dias < 0 else ("VENCE HOJE" if dias == 0 else f"FALTAM {dias} DIAS")
            serv_inicial = str(r['SERVIDOR'])[0] if r['SERVIDOR'] else "S"

            st.markdown(f'''
                <div class="cliente-card">
                    <div class="img-padrao">{serv_inicial}</div>
                    <div class="info-text">
                        <div class="linha-topo">
                            <span class="nome-c">{str(r["NOME"]).upper()}</span>
                            <span class="dias-destaque {"vencido" if dias < 0 else ""}">{txt_dias}</span>
                        </div>
                        <span class="detalhe-c">🔑 {r["USUARIO"]} | {r["SISTEMA"]} | 📅 {pd.to_datetime(r["VENCIMENTO"]).strftime("%d/%m/%Y")}</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            if st.button(f"btn_{r['NOME']}", key=f"btn_{r['NOME']}"):
                st.session_state.cliente_selecionado = r.to_dict()
                st.rerun()

    # --- TAB 2: ADICIONAR ---
    with tab2:
        st.subheader("🚀 NOVO CADASTRO")
        with st.form("add_form", clear_on_submit=True):
            c_a, c_b = st.columns(2)
            n_nome = c_a.text_input("NOME")
            n_user = c_b.text_input("USUÁRIO")
            n_senha = c_a.text_input("SENHA")
            n_serv = c_b.text_input("SERVIDOR")
            n_sist = c_a.selectbox("SISTEMA", ["P2P", "IPTV"])
            n_venc = c_b.date_input("VENCIMENTO", value=hoje + timedelta(days=30), format="DD/MM/YYYY")
            n_custo = c_a.number_input("CUSTO", value=10.0)
            n_mensal = c_b.number_input("MENSALIDADE", value=35.0)
            n_whats = c_a.text_input("WHATSAPP")
            n_obs = c_b.text_area("OBSERVAÇÃO")
            if st.form_submit_button("🚀 CADASTRAR"):
                sheet.append_row([n_nome.upper(), n_user, n_senha, n_serv.upper(), n_sist, n_venc.strftime('%Y-%m-%d'), n_custo, n_mensal, n_whats, n_obs])
                st.success("Cadastrado!"); time.sleep(1); st.rerun()

    # --- TAB 3: COBRANÇA ---
    with tab3:
        st.subheader("🚨 FILTROS DE COBRANÇA")
        bt1, bt2, bt3, bt4, bt5, bt6 = st.columns(6)
        if bt1.button("❌ Venceu"): st.session_state.fc = 'venceu'
        if bt2.button("📅 Hoje"): st.session_state.fc = 'hoje'
        if bt3.button("🌅 Amanhã"): st.session_state.fc = 'amanha'
        if bt4.button("⏳ 2 Dias"): st.session_state.fc = '2dias'
        if bt5.button("⏳ 3 Dias"): st.session_state.fc = '3dias'
        if bt6.button("🗓️ Todos"): st.session_state.fc = 'todos'

        f = st.session_state.get('fc', 'todos')
        pix = "\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!"
        
        if f == 'venceu': 
            df_c = df[df['DIAS_RES'] < 0]
            msg = "🚨SUA ASSINATURA DE TV VENCEU !\n\nNÃO PREOCUPE, BASTA FAZER O PIX QUE REATIVAMOS PRA VOCÊ!" + pix
        elif f == 'hoje': 
            df_c = df[df['DIAS_RES'] == 0]
            msg = "⚠️SUA ASSINATURA DE TV VENCE HOJE ⏰! \n\nNÃO FIQUE SEM TV, BASTA FAZER O PIX QUE RENOVAMOS PRA VOCÊ +30 DIAS!" + pix
        elif f == 'amanha': 
            df_c = df[df['DIAS_RES'] == 1]
            msg = "⚠️SUA ASSINATURA DE TV VENCE AMANHÃ ⏰! \n\nNÃO FIQUE SEM TV, FAÇA O PIX E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!" + pix
        elif f == '2dias': 
            df_c = df[df['DIAS_RES'] == 2]
            msg = "⚠️SUA ASSINATURA DE TV VENCE EM 2️⃣ DIAS ⏰! \n\nFAÇA O PIX AGORA E RENOVAREMOS PRA VOCÊ +30 DIAS!" + pix
        elif f == '3dias': 
            df_c = df[df['DIAS_RES'] == 3]
            msg = "⚠️SUA ASSINATURA DE TV VENCE EM 3️⃣ DIAS ⏰! \n\nFAÇA O PIX AGORA E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!" + pix
        else: 
            df_c = df
            msg = "Olá! Passando para lembrar do seu vencimento da SuperTV4K."

        st.divider()
        for _, cli in df_c.iterrows():
            c1, c2 = st.columns([4, 1])
            v_data = pd.to_datetime(cli['VENCIMENTO']).strftime('%d/%m/%Y')
            c1.write(f"👤 **{cli['NOME']}** | Vence em: {v_data}")
            c2.link_button("📲 COBRAR", f"https://wa.me/55{cli['WHATSAPP']}?text={urllib.parse.quote(msg)}")

    with tab4:
        st.subheader("⚙️ AJUSTES")
        if st.button("🔄 ATUALIZAR"): st.rerun()
        st.download_button("📥 BACKUP", df.to_csv(index=False).encode('utf-8-sig'), "backup.csv")
