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

# Inicializa lista de servidores no estado da sessão (Persistente durante o uso)
if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = [
        "Uniplay", "Mundo GF", "P2Braz", "Unitv", "Playtv", 
        "P2Cine", "P2Speed", "Blade", "MegaTV", "Bob Player"
    ]

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

    .cliente-card {
        display: flex; align-items: center; background-color: #161b22;
        border: 1px solid #30363d; border-radius: 8px; padding: 10px 15px;
        margin-bottom: -72px; position: relative; z-index: 1;
    }
    .img-servidor-card { width: 55px; height: 55px; border-radius: 8px; object-fit: cover; margin-right: 20px; border: 1px solid #444; }
    .info-text { display: flex; flex-direction: column; width: 100%; }
    .linha-topo { display: flex; justify-content: space-between; align-items: center; margin-right: 15px; }
    .nome-c { font-weight: 900; font-size: 17px; color: white; text-transform: uppercase; }
    .dias-destaque { font-weight: 900; font-size: 15px; color: #00d4ff; }

    div.stButton > button {
        width: 100% !important; height: 50px !important;
        font-weight: bold !important;
    }
    /* Botão Invisível para o Card do Cliente */
    .card-btn > div > div > button {
        height: 75px !important; background-color: transparent !important; 
        border: 1px solid transparent !important; color: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE DADOS ---
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
        if len(valores) < 2: return pd.DataFrame()
        colunas = ["id", "nome", "usuario", "senha", "servidor", "sistema", "vencimento", "custo", "mensalidade", "whatsapp", "observacao", "logo_blob"]
        df = pd.DataFrame(valores[1:], columns=colunas[:len(valores[0])])
        df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        return df[df['nome'].str.strip() != ""]
    return pd.DataFrame()

# --- 4. INTERFACE ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)
hoje = datetime.now().date()

if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    with tab1:
        # EDIÇÃO
        if st.session_state.get('cliente_selecionado') is not None:
            c = st.session_state.cliente_selecionado
            st.markdown(f"### 📝 EDITANDO: {c['nome']}")
            with st.form("edit_form"):
                e_nome = st.text_input("NOME", value=c['nome'])
                e_user = st.text_input("USUÁRIO", value=c['usuario'])
                e_senha = st.text_input("SENHA", value=c['senha'])
                e_serv = st.selectbox("SERVIDOR", sorted(st.session_state.lista_servidores), 
                                     index=sorted(st.session_state.lista_servidores).index(c['servidor']) if c['servidor'] in st.session_state.lista_servidores else 0)
                e_sist = st.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if c['sistema'] == "P2P" else 1)
                e_venc = st.date_input("VENCIMENTO", value=pd.to_datetime(c['vencimento']).date())
                e_custo = st.number_input("CUSTO", value=float(c['custo']))
                e_mensal = st.number_input("MENSALIDADE", value=float(c['mensalidade']))
                e_whats = st.text_input("WHATSAPP", value=c['whatsapp'])
                e_obs = st.text_area("OBSERVAÇÃO", value=c['observacao'])
                e_img = st.file_uploader("LOGO_BLOB (Nova Imagem)", type=['png', 'jpg'])
                
                c_btn = st.columns(3)
                if c_btn[0].form_submit_button("💾 SALVAR"):
                    idx = sheet.col_values(1).index(str(c['id'])) + 1
                    blob = base64.b64encode(e_img.read()).decode() if e_img else c['logo_blob']
                    sheet.update(f'A{idx}:L{idx}', [[c['id'], e_nome.upper(), e_user, e_senha, e_serv, e_sist, e_venc.strftime('%Y-%m-%d'), e_custo, e_mensal, e_whats, e_obs, blob]])
                    st.session_state.cliente_selecionado = None
                    st.rerun()
                if c_btn[1].form_submit_button("🗑️ EXCLUIR"):
                    sheet.delete_rows(sheet.col_values(1).index(str(c['id'])) + 1)
                    st.session_state.cliente_selecionado = None
                    st.rerun()
                if c_btn[2].form_submit_button("✖️ FECHAR"):
                    st.session_state.cliente_selecionado = None
                    st.rerun()

        # LISTAGEM
        busca = st.text_input("🔎 BUSCAR CLIENTE...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img_src = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            st.markdown(f'''
                <div class="cliente-card">
                    <img src="{img_src}" class="img-servidor-card">
                    <div class="info-text">
                        <div class="linha-topo"><span class="nome-c">{r['nome']}</span><span class="dias-destaque">{r['dias_res']} DIAS</span></div>
                        <span class="detalhe-c">🔑 {r['usuario']} | {r['servidor']} | {r['sistema']}</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            st.markdown('<div class="card-btn">', unsafe_allow_html=True)
            if st.button(f"EDITAR {r['id']}", key=f"btn_{r['id']}"):
                st.session_state.cliente_selecionado = r.to_dict()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.subheader("🚀 NOVO CADASTRO")
        with st.form("add_form", clear_on_submit=True):
            n_nome = st.text_input("NOME")
            n_user = st.text_input("USUÁRIO")
            n_senha = st.text_input("SENHA")
            n_serv = st.selectbox("SERVIDOR", sorted(st.session_state.lista_servidores))
            n_sist = st.selectbox("SISTEMA", ["P2P", "IPTV"])
            n_venc = st.date_input("VENCIMENTO", value=hoje + timedelta(days=30))
            n_custo = st.number_input("CUSTO", value=10.0)
            n_mensal = st.number_input("MENSALIDADE", value=35.0)
            n_whats = st.text_input("WHATSAPP")
            n_obs = st.text_area("OBSERVAÇÃO")
            n_img = st.file_uploader("LOGO_BLOB", type=['png', 'jpg'])
            
            if st.form_submit_button("🚀 CADASTRAR"):
                prox_id = int(df['id'].max() + 1) if not df.empty else 1
                blob = base64.b64encode(n_img.read()).decode() if n_img else ""
                sheet.append_row([prox_id, n_nome.upper(), n_user, n_senha, n_serv, n_sist, n_venc.strftime('%Y-%m-%d'), n_custo, n_mensal, n_whats, n_obs, blob])
                st.success("Salvo!"); time.sleep(1); st.rerun()

    with tab4:
        st.subheader("⚙️ AJUSTES DO SISTEMA")
        
        # --- GERENCIAR SERVIDORES ---
        st.markdown("### 🖥️ Gerenciar Servidores")
        srv_nome = st.text_input("Nome do Servidor (para salvar ou excluir)")
        col_srv1, col_srv2 = st.columns(2)
        
        if col_srv1.button("💾 SALVAR SERVIDOR"):
            if srv_nome and srv_nome not in st.session_state.lista_servidores:
                st.session_state.lista_servidores.append(srv_nome)
                st.success(f"Servidor '{srv_nome}' salvo!")
                st.rerun()
                
        if col_srv2.button("🗑️ EXCLUIR SERVIDOR"):
            if srv_nome in st.session_state.lista_servidores:
                st.session_state.lista_servidores.remove(srv_nome)
                st.warning(f"Servidor '{srv_nome}' removido!")
                st.rerun()
            else:
                st.error("Servidor não encontrado.")

        st.divider()

        # --- BOTÕES DE AÇÃO ---
        st.markdown("### 🛠️ Ferramentas e Dados")
        c1, c2, c3 = st.columns(3)
        
        # Sincronizar
        if c1.button("🔄 SINCRONIZAR SHEETS"):
            st.rerun()
            
        # Backup Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Clientes')
        
        c2.download_button(
            label="📥 BACKUP EXCEL",
            data=buffer.getvalue(),
            file_name=f"backup_supertv_{hoje}.xlsx",
            mime="application/vnd.ms-excel"
        )
        
        # Upload de Arquivo
        st.markdown("---")
        st.markdown("### 📤 Upload de Dados")
        file_up = st.file_uploader("Subir arquivo (CSV/Excel)", type=['csv', 'xlsx'])
        if file_up:
            st.info("Arquivo carregado. Implemente a lógica de processamento conforme sua necessidade.")

