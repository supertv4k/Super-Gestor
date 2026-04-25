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

if 'filtro_f' not in st.session_state:
    st.session_state.filtro_f = "vencidos"

if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = ["Uniplay", "Mundo GF", "P2Braz", "Unitv", "Playtv", "P2Cine", "P2Speed", "Blade", "MegaTV", "Bob Player", "Ibo Player", "Ibo Pro Player"]

# --- LÓGICA DE DISPARO ---
if 'clientes_para_disparo' not in st.session_state:
    st.session_state.clientes_para_disparo = []
if 'indice_disparo' not in st.session_state:
    st.session_state.indice_disparo = 0
if 'executando_disparo' not in st.session_state:
    st.session_state.executando_disparo = False

# --- 2. ESTILIZAÇÃO CSS (FOCO NA ALTURA E LARGURA DO CARD) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; margin-bottom: 20px; }
    .logo-gestao { width: 380px; margin-bottom: -15px !important; }
    .logo-supertv { width: 320px; }
    
    /* CARD RETANGULAR ESTREITO (ALTURA REDUZIDA) */
    .card-link-custom {
        text-decoration: none !important;
        display: block;
        width: 100%;
        max-width: 450px; /* Largura controlada */
        margin: 8px auto; /* Espaçamento entre cards */
    }

    .cliente-card-html {
        display: flex; 
        align-items: center; 
        background-color: #161b22;
        border: 1px solid #30363d; 
        border-radius: 10px; 
        padding: 8px 12px; /* Reduzi o padding para diminuir a altura total */
        height: 70px; /* ALTURA FIXA E ESTREITA */
        transition: 0.2s;
    }
    
    .cliente-card-html:hover { 
        border-color: #00d4ff; 
        background-color: #1c2128; 
        transform: scale(1.02);
    }

    .img-servidor-card { width: 45px; height: 45px; border-radius: 6px; object-fit: cover; margin-right: 12px; border: 1px solid #444; }
    .info-container { flex-grow: 1; display: flex; flex-direction: column; justify-content: center; }
    .nome-c { font-weight: 900; font-size: 14px; color: white; text-transform: uppercase; margin: 0; }
    .sub-c { color: #8b949e; font-size: 12px; }
    .dias-box { border-left: 1px solid #30363d; padding-left: 10px; width: 85px; text-align: right; }
    
    .cor-vencido { color: #FF4B4B; font-weight: 900; font-size: 13px; }
    .cor-alerta { color: #FFD700; font-weight: 900; font-size: 13px; }
    .cor-ok { color: #00FF00; font-weight: 900; font-size: 13px; }
    .cor-tranquilo { color: #00D4FF; font-weight: 900; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE DADOS (MANTIDAS 100% ORIGINAIS) ---
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

# --- LÓGICA DE EDIÇÃO ---
if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    # Pegar ID da URL para editar
    params = st.query_params
    if "editar_id" in params:
        sel = df[df['id'].astype(str) == str(params["editar_id"])]
        if not sel.empty:
            st.session_state.cliente_selecionado = sel.iloc[0].to_dict()

# --- 4. INTERFACE ---

# FORMULÁRIO DE EDIÇÃO (MANTIDO)
if st.session_state.get('cliente_selecionado') is not None:
    c = st.session_state.cliente_selecionado
    st.markdown("### 📝 EDITAR CLIENTE")
    with st.form("form_edit_full"):
        col1, col2 = st.columns(2)
        enome = col1.text_input("NOME", value=c['nome'])
        euser = col2.text_input("USUÁRIO", value=c['usuario'])
        esenha = col1.text_input("SENHA", value=c['senha'])
        eserv = col2.selectbox("SERVIDOR", sorted(st.session_state.lista_servidores), index=st.session_state.lista_servidores.index(c['servidor']) if c['servidor'] in st.session_state.lista_servidores else 0)
        esist = col1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if c['sistema']=="P2P" else 1)
        evenc = col2.date_input("VENCIMENTO", value=pd.to_datetime(c['vencimento']).date())
        ecusto = col1.number_input("CUSTO", value=float(c['custo']))
        emensal = col2.number_input("MENSALIDADE", value=float(c['mensalidade']))
        ewhats = col1.text_input("WHATSAPP", value=c['whatsapp'])
        eobs = col2.text_area("OBSERVAÇÃO", value=c['observacao'])
        eimg = st.file_uploader("LOGO", type=['png', 'jpg'])
        
        b1, b2, b3, b4 = st.columns(4)
        if b1.form_submit_button("💾 SALVAR"):
            idx = sheet.col_values(1).index(str(c['id'])) + 1
            blob = base64.b64encode(eimg.read()).decode() if eimg else c['logo_blob']
            sheet.update(f'A{idx}:L{idx}', [[c['id'], enome.upper(), euser, esenha, eserv, esist, evenc.strftime('%Y-%m-%d'), ecusto, emensal, ewhats, eobs, blob]])
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()
        if b2.form_submit_button("⚡ +30 DIAS"):
            idx = sheet.col_values(1).index(str(c['id'])) + 1
            nova_data = (hoje + timedelta(days=30)).strftime('%Y-%m-%d')
            sheet.update_cell(idx, 7, nova_data)
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()
        if b3.form_submit_button("🗑️ EXCLUIR"):
            sheet.delete_rows(sheet.col_values(1).index(str(c['id'])) + 1)
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()
        if b4.form_submit_button("✖️ FECHAR"):
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()
    st.divider()

# CABEÇALHO
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

if not df.empty:
    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    # ABA CLIENTES: CARD ESTREITO COM CLIQUE
    with tab1:
        busca = st.text_input("🔎 BUSCAR...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            cor = get_cor_classe(r['dias_res'])
            st.markdown(f'''
                <a href="/?editar_id={r['id']}" target="_self" class="card-link-custom">
                    <div class="cliente-card-html">
                        <img src="{img}" class="img-servidor-card">
                        <div class="info-container">
                            <div class="nome-c">{r['nome']}</div>
                            <div class="sub-c">{r['sistema']} | {r['servidor']}</div>
                        </div>
                        <div class="dias-box">
                            <span class="{cor}">{r['dias_res']} DIAS</span><br>
                            <small style="color:#8b949e; font-size:10px;">{r['dt_venc_calc'].strftime('%d/%m')}</small>
                        </div>
                    </div>
                </a>
            ''', unsafe_allow_html=True)

    # ABA ADICIONAR (MANTIDA)
    with tab2:
        st.subheader("🚀 NOVO CADASTRO")
        with st.form("add_cli", clear_on_submit=True):
            ca1, ca2 = st.columns(2)
            nnome = ca1.text_input("NOME"); nuser = ca2.text_input("USUÁRIO")
            nsenha = ca1.text_input("SENHA"); nserv = ca2.selectbox("SERVIDOR", sorted(st.session_state.lista_servidores))
            nsist = ca1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0); nvenc = ca2.date_input("VENCIMENTO", value=hoje + timedelta(days=30))
            ncusto = ca1.number_input("CUSTO", value=10.0); nmensal = ca2.number_input("MENSALIDADE", value=35.0)
            nwhats = ca1.text_input("WHATSAPP"); nobs = ca2.text_area("OBSERVAÇÃO"); nimg = st.file_uploader("LOGO", type=['png', 'jpg'])
            if st.form_submit_button("🚀 CADASTRAR"):
                prox_id = int(df['id'].max() + 1) if not df.empty else 1
                blob = base64.b64encode(nimg.read()).decode() if nimg else ""
                sheet.append_row([prox_id, nnome.upper(), nuser, nsenha, nserv, nsist, nvenc.strftime('%Y-%m-%d'), ncusto, nmensal, nwhats, nobs, blob])
                st.rerun()

    # ABA COBRANÇA (MANTIDA COM ENVIO EM MASSA)
    with tab3:
        if st.session_state.executando_disparo:
            fila = st.session_state.clientes_para_disparo
            idx = st.session_state.indice_disparo
            if idx < len(fila):
                cliente = fila[idx]
                st.warning(f"🚀 ENVIANDO: {idx + 1} de {len(fila)}")
                st.write(f"**Cliente:** {cliente['nome']}")
                cnpj_pix = "\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA O COMPROVANTE!"
                msg = "Lembrete de renovação SUPERTV4K." + cnpj_pix
                url = f"https://wa.me/55{cliente['whatsapp']}?text={urllib.parse.quote(msg)}"
                col1, col2 = st.columns(2)
                if col1.link_button("📲 ENVIAR AGORA", url, type="primary"): st.session_state.aguardando_proximo = True
                if col2.button("✖️ PARAR"): st.session_state.executando_disparo = False; st.rerun()
                if st.session_state.get('aguardando_proximo'):
                    time.sleep(10)
                    st.session_state.indice_disparo += 1; st.session_state.aguardando_proximo = False; st.rerun()
            else:
                st.success("✅ Fim da fila!"); st.session_state.executando_disparo = False
        else:
            filtros = ["vencidos", "hoje", "todos"]
            c_cols = st.columns(3)
            for i, f in enumerate(filtros):
                if c_cols[i].button(f.upper()): st.session_state.filtro_f = f
            
            df_c = df
            if st.session_state.filtro_f == "vencidos": df_c = df[df['dias_res'] < 0]
            elif st.session_state.filtro_f == "hoje": df_c = df[df['dias_res'] == 0]

            if not df_c.empty:
                st.write(f"Filtrados: {len(df_c)}")
                clientes_marcados = []
                for _, r in df_c.iterrows():
                    if st.checkbox(f"Selecionar {r['nome']}", key=f"c_{r['id']}"):
                        clientes_marcados.append(r.to_dict())
                if st.button("🚀 INICIAR ENVIO EM MASSA"):
                    st.session_state.clientes_para_disparo = clientes_marcados
                    st.session_state.indice_disparo = 0; st.session_state.executando_disparo = True; st.rerun()

    # ABA AJUSTES (MANTIDA)
    with tab4:
        if st.button("🔄 ATUALIZAR DADOS"): st.rerun()
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.drop(columns=['dt_venc_calc', 'dias_res']).to_excel(writer, index=False)
        st.download_button("📥 BACKUP EXCEL", data=buffer.getvalue(), file_name="backup.xlsx")
