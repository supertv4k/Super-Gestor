import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse
import base64
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS (ESTÁVEL E LIMPA) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 400px; margin-bottom: -15px !important; }
    .logo-supertv { width: 350px; }
    
    /* Estilo da Imagem do Servidor na Lateral */
    .img-servidor-lista {
        width: 60px !important;
        height: 60px !important;
        border-radius: 8px;
        object-fit: cover;
        border: 1px solid #30363d;
    }

    /* BOTÃO RETANGULAR ALONGADO */
    div.stButton > button {
        width: 100% !important;
        height: 60px !important;
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: white !important;
        border-radius: 8px !important;
        text-align: left !important;
        padding-left: 20px !important;
        font-size: 15px !important;
        transition: 0.3s;
    }

    div.stButton > button:hover {
        border-color: #00d4ff !important;
        background-color: #1c2128 !important;
    }

    .edit-panel { background-color: #1c2128; padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; margin-bottom: 25px; }
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .val-azul { color: #00d4ff; font-size: 22px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXÃO E DADOS ---
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
        df = pd.DataFrame(valores[1:], columns=[str(c).strip().lower() for c in valores[0]])
        if 'id' in df.columns: df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
        df['custo'] = pd.to_numeric(df['custo'], errors='coerce').fillna(0)
        df['mensalidade'] = pd.to_numeric(df['mensalidade'], errors='coerce').fillna(0)
        return df[df['nome'].astype(str).str.strip() != ""]
    return pd.DataFrame()

# --- INTERFACE PRINCIPAL ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)

if not df.empty:
    hoje = datetime.now().date()
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    with tab1:
        # PAINEL DE EDIÇÃO
        if st.session_state.get('cliente_selecionado') is not None:
            c = st.session_state.cliente_selecionado
            st.markdown(f'<div class="edit-panel"><h3>📝 EDITAR: {str(c.get("nome")).upper()}</h3></div>', unsafe_allow_html=True)
            with st.form("form_edit"):
                col_e1, col_e2 = st.columns(2)
                novo_nome = col_e1.text_input("NOME", value=str(c.get('nome')).upper())
                novo_user = col_e2.text_input("USUÁRIO", value=c.get('usuario'))
                novo_senha = col_e1.text_input("SENHA", value=c.get('senha'))
                novo_venc = col_e2.date_input("VENCIMENTO", value=pd.to_datetime(c.get('vencimento')).date())
                novo_whats = col_e1.text_input("WHATSAPP", value=c.get('whatsapp'))
                novo_mensal = col_e2.number_input("MENSALIDADE", value=float(c.get('mensalidade') or 0))
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 SALVAR"):
                    ids = sheet.col_values(1)
                    idx = ids.index(str(c['id'])) + 1
                    sheet.update(range_name=f'B{idx}:C{idx}', values=[[novo_nome.upper(), novo_user]])
                    sheet.update_cell(idx, 4, novo_senha)
                    sheet.update_cell(idx, 7, novo_venc.strftime('%Y-%m-%d'))
                    sheet.update_cell(idx, 9, novo_mensal)
                    sheet.update_cell(idx, 10, novo_whats)
                    st.session_state.cliente_selecionado = None
                    st.success("Atualizado!"); time.sleep(1); st.rerun()
                if b2.form_submit_button("✖️ CANCELAR"):
                    st.session_state.cliente_selecionado = None
                    st.rerun()

        busca = st.text_input("🔎 BUSCAR CLIENTE...")
        df_f = df[df['nome'].str.contains(busca, case=False, na=False)] if busca else df
        
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img_b64 = f"data:image/png;base64,{r['logo_blob']}" if r.get('logo_blob') else "https://i.imgur.com/vH9XvI0.png"
            
            # Layout de linha estável: Imagem | Botão
            c_img, c_btn = st.columns([1, 7])
            with c_img:
                st.markdown(f'<img src="{img_b64}" class="img-servidor-lista">', unsafe_allow_html=True)
            with c_btn:
                info = f"{str(r['nome']).upper()} | 🔑 {r['usuario']} | 📅 {pd.to_datetime(r['vencimento']).strftime('%d/%m/%Y')}"
                if st.button(info, key=f"btn_{r['id']}"):
                    st.session_state.cliente_selecionado = r.to_dict()
                    st.rerun()

    with tab2:
        st.subheader("🚀 NOVO CADASTRO")
        with st.form("form_add", clear_on_submit=True):
            n_nome = st.text_input("NOME COMPLETO")
            n_user = st.text_input("LOGIN / USUÁRIO")
            n_senha = st.text_input("SENHA")
            n_whats = st.text_input("WHATSAPP (DDD+NÚMERO)")
            n_venc = st.date_input("PRIMEIRO VENCIMENTO", value=hoje + timedelta(days=30))
            n_mensal = st.number_input("MENSALIDADE", value=35.0)
            n_img = st.file_uploader("LOGO", type=['png', 'jpg', 'jpeg'])
            if st.form_submit_button("🚀 CADASTRAR CLIENTE"):
                blob = base64.b64encode(n_img.read()).decode() if n_img else ""
                prox_id = int(df['id'].max() + 1) if not df.empty else 1
                sheet.append_row([prox_id, n_nome.upper(), n_user, n_senha, "SERV", "IPTV", n_venc.strftime('%Y-%m-%d'), 10, n_mensal, n_whats, "", blob])
                st.success("Cadastrado!"); time.sleep(1); st.rerun()

    with tab3:
        st.subheader("🚨 COBRANÇA")
        df_v = df[df['dias_res'] <= 3].sort_values('dias_res')
        for _, cli in df_v.iterrows():
            st.write(f"⚠️ {cli['nome']} - Vence em {cli['dias_res']} dias")
            link = f"https://wa.me/55{cli['whatsapp']}?text=Olá, sua assinatura SuperTV4K vence em breve!"
            st.link_button(f"Enviar WhatsApp para {cli['nome']}", link)

    with tab4:
        st.subheader("⚙️ AJUSTES")
        if st.button("🔄 SINCRONIZAR PLANILHA"): st.rerun()
        st.download_button("📥 BAIXAR BACKUP (CSV)", df.to_csv(index=False).encode('utf-8-sig'), "backup_clientes.csv")
