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

# --- 2. ESTILIZAÇÃO CSS ---
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

# --- 3. FUNÇÕES DE SUPORTE ---
def conectar_gs():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1ntE8RpofySu5IFupuvOZxZnrnmHKzaYbyqAQ-Mzc8so").sheet1
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

def carregar_dados(sheet):
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame(columns=["id", "nome", "usuario", "senha", "servidor", "sistema", "vencimento", "custo", "mensalidade", "whatsapp", "observacao", "logo_blob"])
        
        # CORREÇÃO: Remove linhas vazias ou que o Sheets marcou com fórmulas (resolve o erro do +1)
        df = df[df['nome'].astype(str).str.strip() != ""]
        df = df[df['nome'].notna()]
        return df
    return pd.DataFrame()

def format_data_br(data_str):
    try: 
        # Tenta converter de YYYY-MM-DD para DD/MM/YYYY
        return datetime.strptime(str(data_str), '%Y-%m-%d').strftime('%d/%m/%Y')
    except: 
        return data_str

# Gerenciamento de Servidores (Editável nos Ajustes)
if 'lista_servidores' not in st.session_state:
    st.session_state.lista_servidores = ["UNIPLAY", "MUNDO GF", "P2BRAZ", "UNITV", "PLAYTV", "P2CINE", "P2SPEED", "BLADE", "MEGATV", "BOB PLAYER", "IBO PLAYER", "IBO PRO PLAYER", "OUTROS"]

# --- 4. LÓGICA DE ESTADO ---
if 'cliente_selecionado' not in st.session_state:
    st.session_state.cliente_selecionado = None

# --- 5. INTERFACE ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)

if not df.empty:
    hoje = datetime.now().date()
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    df_ativos = df[df['dias_res'] >= 0]
    
    # Cálculo de Lucro
    mensalidades = pd.to_numeric(df_ativos['mensalidade'], errors='coerce').fillna(0)
    custos = pd.to_numeric(df_ativos['custo'], errors='coerce').fillna(0)
    lucro_total = mensalidades.sum() - custos.sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.markdown(f'<div class="metric-container"><div class="metric-label">TOTAL</div><div class="val-azul">{len(df)}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-container"><div class="metric-label">ATIVOS</div><div class="val-verde">{len(df_ativos)}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-container"><div class="metric-label">VENCE HOJE</div><div class="val-laranja">{len(df[df["dias_res"] == 0])}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-container"><div class="metric-label">VENCIDOS</div><div class="val-vermelho">{len(df[df["dias_res"] < 0])}</div></div>', unsafe_allow_html=True)
    m5.markdown(f'<div class="metric-container"><div class="metric-label">LUCRO ESTIMADO</div><div class="val-lucro">R$ {lucro_total:,.2f}</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ NOVO CADASTRO", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    if st.session_state.cliente_selecionado is not None:
        c_sel = st.session_state.cliente_selecionado
        st.markdown(f'<div class="edit-panel"><h3>📝 Editando: {str(c_sel.get("nome", "Cliente")).upper()}</h3></div>', unsafe_allow_html=True)
        with st.form("edit_form"):
            col1, col2, col3 = st.columns(3)
            en_nome = col1.text_input("Nome", value=c_sel.get('nome', ''))
            en_user = col2.text_input("Usuário", value=c_sel.get('usuario', ''))
            en_senha = col3.text_input("Senha", value=c_sel.get('senha', ''))
            en_serv = col1.selectbox("Servidor", st.session_state.lista_servidores)
            
            # Garante que a data de vencimento seja válida para o componente
            try:
                data_padrao = pd.to_datetime(c_sel['vencimento']).date()
            except:
                data_padrao = datetime.now().date()
                
            en_venc = col2.date_input("Vencimento", value=data_padrao, format="DD/MM/YYYY")
            en_whats = col3.text_input("WhatsApp", value=c_sel.get('whatsapp', ''))
            en_custo = col1.number_input("Custo", value=float(c_sel.get('custo') or 0))
            en_mensal = col2.number_input("Valor Cobrado", value=float(c_sel.get('mensalidade') or 0))
            en_obs = st.text_area("Observação", value=str(c_sel.get('observacao') or ""))
            en_img = st.file_uploader("Trocar Logo", type=['png', 'jpg'])

            b_salvar, b_excluir, b_cancelar = st.columns(3)
            if b_salvar.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                l_b = base64.b64encode(en_img.read()).decode() if en_img else c_sel.get('logo_blob', '')
                ids = sheet.col_values(1)
                row_idx = ids.index(str(c_sel['id'])) + 1
                sheet.update(range_name=f'A{row_idx}:L{row_idx}', values=[[c_sel['id'], en_nome, en_user, en_senha, en_serv, c_sel.get('sistema', 'P2P'), en_venc.strftime('%Y-%m-%d'), en_custo, en_mensal, en_whats, en_obs, l_b]])
                st.session_state.cliente_selecionado = None
                st.success("Sincronizado!")
                st.rerun()
            if b_excluir.form_submit_button("🗑️ EXCLUIR CLIENTE"):
                ids = sheet.col_values(1)
                row_idx = ids.index(str(c_sel['id'])) + 1
                sheet.delete_rows(row_idx)
                st.session_state.cliente_selecionado = None
                st.rerun()
            if b_cancelar.form_submit_button("✖️ FECHAR"):
                st.session_state.cliente_selecionado = None
                st.rerun()

    busca = st.text_input("🔎 Pesquisar cliente...", placeholder="Nome ou Usuário")
    if not df.empty:
        df_f = df[df['nome'].str.contains(busca, case=False, na=False) | df['usuario'].str.contains(busca, case=False, na=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res', ascending=True).iterrows():
            img_tag = f"data:image/png;base64,{r['logo_blob']}" if r.get('logo_blob') else "https://i.imgur.com/vH9XvI0.png"
            c1, c2 = st.columns([1, 10])
            c1.markdown(f'<img src="{img_tag}" class="img-servidor">', unsafe_allow_html=True)
            
            # CORREÇÃO KEYERROR: Usando .get() para evitar quebra caso falte coluna
            label_botao = f"{str(r.get('nome', 'S/N')).upper()} | 🔑 {r.get('usuario', 'S/U')} | 📅 {format_data_br(r.get('vencimento'))}"
            if c2.button(label_botao, key=f"b_{r.get('id')}"):
                st.session_state.cliente_selecionado = r.to_dict()
                st.rerun()

with tab2:
    st.subheader("🚀 Novo Cadastro")
    with st.form("add_new", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        n_nome = f1.text_input("Nome")
        n_user = f2.text_input("Usuário")
        n_senha = f3.text_input("Senha")
        n_serv = f1.selectbox("Servidor", st.session_state.lista_servidores)
        n_venc = f3.date_input("Vencimento", value=datetime.now() + timedelta(days=30), format="DD/MM/YYYY")
        n_whats = f1.text_input("WhatsApp")
        n_valor = f3.number_input("Valor Cobrado", value=35.0)
        n_img = st.file_uploader("Logo", type=['png', 'jpg'])
        
        if st.form_submit_button("🚀 CADASTRAR CLIENTE"):
            l_b = base64.b64encode(n_img.read()).decode() if n_img else ""
            # Calcula ID novo ignorando erros
            try:
                ids_existentes = pd.to_numeric(df['id'], errors='coerce').dropna()
                novo_id = int(ids_existentes.max() + 1) if not ids_existentes.empty else 1
            except:
                novo_id = 1
                
            sheet.append_row([novo_id, n_nome, n_user, n_senha, n_serv, "P2P", n_venc.strftime('%Y-%m-%d'), 10.0, n_valor, n_whats, "", l_b])
            st.success("✅ Salvo no Google Sheets!")
            st.rerun()

with tab3:
    st.subheader("🚨 Cobrança Automática")
    pix_cnpj = "62.326.879/0001-13"
    if not df.empty:
        df_c = df[df['dias_res'] <= 3]
        for _, c in df_c.sort_values(by='dias_res').iterrows():
            dias = c['dias_res']
            nome_p = str(c.get('nome', '')).split()[0].upper()
            data_venc_br = format_data_br(c.get('vencimento'))
            
            if dias < 0: status = "VENCIDA"
            elif dias == 0: status = "VENCE HOJE"
            else: status = f"VENCE EM {dias} DIAS"
            
            msg = f"⚠️ *{nome_p}, SUA ASSINATURA ({status})!* \n📅 Vencimento: {data_venc_br}\n\nPara renovar e não perder o acesso, segue nossa chave PIX:\n🔑 {pix_cnpj}"
            st.link_button(f"📲 Cobrar: {c['nome']} ({status})", f"https://wa.me/55{c['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Ajustes e Ferramentas")
    
    col_aj1, col_aj2 = st.columns(2)
    
    with col_aj1:
        st.markdown("### 🛠️ Gestão de Dados")
        if st.button("🔄 Forçar Sincronização"):
            st.cache_data.clear()
            st.rerun()
            
        # BOTÃO BACKUP EXCEL
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Baixar Backup Excel (CSV)",
            data=csv,
            file_name=f'backup_supertv_{datetime.now().strftime("%d_%m_%Y")}.csv',
            mime='text/csv',
        )
        
        # BOTÃO UPLOAD
        st.markdown("---")
        st.markdown("### 📤 Importar Dados")
        uploaded_file = st.file_uploader("Subir planilha de backup", type=['csv'])
        if uploaded_file is not None:
            if st.button("Confirmar Upload"):
                # Lógica para processar o upload se necessário
                st.info("Função de importação em desenvolvimento para garantir segurança dos dados.")

    with col_aj2:
        st.markdown("### 🖥️ Servidores Disponíveis")
        novos_servidores = st.text_area("Edite os servidores (um por linha)", value="\n".join(st.session_state.lista_servidores))
        if st.button("Atualizar Lista de Servidores"):
            st.session_state.lista_servidores = novos_servidores.split("\n")
            st.success("Lista atualizada!")
