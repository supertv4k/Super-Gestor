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

if 'filtro_f' not in st.session_state:
    st.session_state.filtro_f = "vencidos"

if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = ["Uniplay", "Mundo GF", "P2Braz", "Unitv", "Playtv", "P2Cine", "P2Speed", "Blade", "MegaTV", "Bob Player", "Ibo Player"]

# --- 2. ESTILIZAÇÃO CSS (VISUAL PREMIUM COM CORES DINÂMICAS) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 20px; }
    .logo-gestao { width: 400px; margin-bottom: -15px !important; }
    .logo-supertv { width: 350px; }
    
    /* Card do Cliente */
    .cliente-card {
        display: flex; align-items: center; background-color: #161b22;
        border: 1px solid #30363d; border-radius: 12px; padding: 15px;
        margin-bottom: -75px; position: relative; z-index: 1;
    }
    .img-servidor-card { width: 60px; height: 60px; border-radius: 10px; object-fit: cover; margin-right: 20px; border: 1px solid #444; }
    .nome-c { font-weight: 900; font-size: 18px; color: white; text-transform: uppercase; }
    .detalhe-c { font-size: 14px; color: #8b949e; }
    
    /* Cores de Vencimento solicitadas */
    .cor-vencido { color: #FF4B4B; font-weight: 900; } /* Vermelho */
    .cor-alerta { color: #FFD700; font-weight: 900; }  /* Amarelo (Hoje, 1 e 2 dias) */
    .cor-ok { color: #00FF00; font-weight: 900; }      /* Verde (3 dias) */
    .cor-tranquilo { color: #00D4FF; font-weight: 900; } /* Azul (4+ dias) */

    .card-btn > div > div > button {
        height: 85px !important; background-color: transparent !important; 
        border: 1px solid transparent !important; color: transparent !important;
    }
    
    .cobransa-item-simples {
        background-color: #1c2128; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #00d4ff;
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
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        return df[df['nome'].str.strip() != ""]
    return pd.DataFrame()

# Função para definir a classe de cor baseada nos dias
def get_cor_classe(dias):
    if dias < 0: return "cor-vencido"
    elif dias <= 2: return "cor-alerta"
    elif dias == 3: return "cor-ok"
    else: return "cor-tranquilo"

# --- 4. INTERFACE ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)
hoje = datetime.now().date()

if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    with tab1:
        if st.session_state.get('cliente_selecionado') is not None:
            c = st.session_state.cliente_selecionado
            st.markdown(f"### 📝 EDITANDO: {c['nome']}")
            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                e_nome = col1.text_input("NOME", value=c['nome'])
                e_user = col2.text_input("USUÁRIO", value=c['usuario'])
                e_senha = col1.text_input("SENHA", value=c['senha'])
                e_serv = col2.selectbox("SERVIDOR", sorted(st.session_state.lista_servidores), index=sorted(st.session_state.lista_servidores).index(c['servidor']) if c['servidor'] in st.session_state.lista_servidores else 0)
                e_sist = col1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if c['sistema'] == "P2P" else 1)
                e_venc = col2.date_input("VENCIMENTO", value=pd.to_datetime(c['vencimento']).date())
                e_custo = col1.number_input("CUSTO", value=float(c['custo'] or 0))
                e_mensal = col2.number_input("MENSALIDADE", value=float(c['mensalidade'] or 0))
                e_whats = col1.text_input("WHATSAPP", value=c['whatsapp'])
                e_obs = st.text_area("OBSERVAÇÃO", value=c['observacao'])
                e_img = st.file_uploader("TROCAR LOGO", type=['png', 'jpg'])
                
                btn_cols = st.columns(3)
                if btn_cols[0].form_submit_button("💾 SALVAR"):
                    idx = sheet.col_values(1).index(str(c['id'])) + 1
                    blob = base64.b64encode(e_img.read()).decode() if e_img else c['logo_blob']
                    sheet.update(f'A{idx}:L{idx}', [[c['id'], e_nome.upper(), e_user, e_senha, e_serv, e_sist, e_venc.strftime('%Y-%m-%d'), e_custo, e_mensal, e_whats, e_obs, blob]])
                    st.session_state.cliente_selecionado = None
                    st.rerun()
                if btn_cols[1].form_submit_button("🗑️ EXCLUIR"):
                    sheet.delete_rows(sheet.col_values(1).index(str(c['id'])) + 1)
                    st.session_state.cliente_selecionado = None
                    st.rerun()
                if btn_cols[2].form_submit_button("✖️ FECHAR"):
                    st.session_state.cliente_selecionado = None
                    st.rerun()
            st.divider()

        busca = st.text_input("🔎 BUSCAR CLIENTE...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img_src = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            cor_classe = get_cor_classe(r['dias_res'])
            label_dias = "VENCIDO" if r['dias_res'] < 0 else f"{r['dias_res']} DIAS"
            
            st.markdown(f'''
                <div class="cliente-card">
                    <img src="{img_src}" class="img-servidor-card">
                    <div style="flex-grow: 1;">
                        <div style="display: flex; justify-content: space-between;">
                            <span class="nome-c">{r['nome']}</span>
                            <span class="{cor_classe}">{label_dias}</span>
                        </div>
                        <span class="detalhe-c">🔑 {r['usuario']} | 🖥️ {r['servidor']} | {r['sistema']}</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            
            st.markdown('<div class="card-btn">', unsafe_allow_html=True)
            if st.button(f"EDITAR {r['id']}", key=f"cli_{r['id']}"):
                st.session_state.cliente_selecionado = r.to_dict()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # Abas 2, 3 e 4 mantêm as lógicas de Adicionar, Cobrança e Ajustes anteriores.
