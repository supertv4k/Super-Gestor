
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import urllib.parse
import io
import base64

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS (Mantida Original) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    
    .metric-container {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
        text-align: center;
    }
    .metric-label { color: white; font-size: 14px; font-weight: bold; margin-bottom: 5px; }
    .val-azul { color: #00d4ff; font-size: 24px; font-weight: bold; }
    .val-verde { color: #28a745; font-size: 24px; font-weight: bold; }
    .val-laranja { color: #ffa500; font-size: 24px; font-weight: bold; }
    .val-vermelho { color: #ff4b4b; font-size: 24px; font-weight: bold; }
    .val-lucro { color: #00ff88; font-size: 24px; font-weight: bold; }

    .img-servidor { width: 55px; height: 55px; border-radius: 8px; object-fit: cover; border: 1px solid #444; }
    
    div.stButton > button {
        text-align: left !important;
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 12px !important;
        width: 100%;
    }
    
    .edit-panel {
        background-color: #1c2128;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #00d4ff;
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXÃO GOOGLE SHEETS ---
conn_gs = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # Lê os dados da planilha configurada no Secrets
        return conn_gs.read(ttl=0)
    except:
        # Se falhar ou estiver vazia, retorna estrutura básica
        return pd.DataFrame(columns=[
            "id", "nome", "usuario", "senha", "servidor", "sistema", 
            "vencimento", "custo", "mensalidade", "whatsapp", "observacao", "logo_blob"
        ])

def format_data_br(data_str):
    try:
        if isinstance(data_str, str):
            return datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
        return data_str.strftime('%d/%m/%Y')
    except:
        return data_str

def get_servidores():
    return ["UNIPLAY", "MUNDO GF", "P2BRAZ", "UNITV", "PLAYTV", "P2CINE", "P2SPEED", "BLADE", "MEGATV", "BOB PLAYER", "IBO PLAYER", "IBO PRO PLAYER", "OUTROS"]

# --- 4. LÓGICA DE ESTADO ---
if 'cliente_selecionado' not in st.session_state:
    st.session_state.cliente_selecionado = None

# --- 5. INTERFACE PRINCIPAL ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

# Carregar dados da Planilha
df = carregar_dados()

if not df.empty:
    hoje = datetime.now().date()
    # Garante que a coluna de vencimento seja data para cálculos
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    df_ativos = df[df['dias_res'] >= 0]
    lucro_total = (pd.to_numeric(df_ativos['mensalidade'], errors='coerce').sum()) - (pd.to_numeric(df_ativos['custo'], errors='coerce').sum())

    # Métricas
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.markdown(f'<div class="metric-container"><div class="metric-label">TOTAL</div><div class="val-azul">{len(df)}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-container"><div class="metric-label">ATIVOS</div><div class="val-verde">{len(df[df["dias_res"] >= 0])}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-container"><div class="metric-label">VENCE HOJE</div><div class="val-laranja">{len(df[df["dias_res"] == 0])}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-container"><div class="metric-label">VENCIDOS</div><div class="val-vermelho">{len(df[df["dias_res"] < 0])}</div></div>', unsafe_allow_html=True)
    m5.markdown(f'<div class="metric-container"><div class="metric-label">LUCRO ESTIMADO</div><div class="val-lucro">R$ {lucro_total:,.2f}</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ NOVO CADASTRO", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    if st.session_state.cliente_selecionado is not None:
        c_sel = st.session_state.cliente_selecionado
        st.markdown(f'<div class="edit-panel"><h3>📝 Editando: {str(c_sel["nome"]).upper()}</h3></div>', unsafe_allow_html=True)
        
        with st.container():
            col1, col2, col3 = st.columns(3)
            new_nome = col1.text_input("Nome", value=c_sel['nome'])
            new_user = col2.text_input("Usuário", value=c_sel['usuario'])
            new_senha = col3.text_input("Senha", value=c_sel['senha'])
            
            servs = get_servidores()
            idx_s = servs.index(c_sel['servidor']) if c_sel['servidor'] in servs else 0
            new_serv = col1.selectbox("Servidor", servs, index=idx_s)
            
            new_sistema = col2.selectbox("Sistema", ["P2P", "IPTV"], index=0 if c_sel['sistema']=="P2P" else 1)
            
            v_data = pd.to_datetime(c_sel['vencimento']).date() if c_sel['vencimento'] else datetime.now().date()
            new_venc = col3.date_input("Vencimento", value=v_data)
            
            new_whats = col1.text_input("WhatsApp", value=c_sel['whatsapp'])
            new_custo = col2.number_input("Custo", value=float(c_sel['custo'] or 0))
            new_mensal = col3.number_input("Valor Cobrado", value=float(c_sel['mensalidade'] or 0))
            new_obs = st.text_area("Observação", value=str(c_sel['observacao'] or ""))
            
            st.write("🖼️ **Trocar Logo**")
            new_img = st.file_uploader("Nova imagem", type=['png', 'jpg'], key="edit_img")

            b_salvar, b_renovar, b_excluir, b_cancelar = st.columns(4)
            
            if b_salvar.button("💾 SALVAR ALTERAÇÕES", use_container_width=True):
                l_b = base64.b64encode(new_img.read()).decode() if new_img else c_sel['logo_blob']
                
                # Atualiza no DataFrame local
                idx = df[df['id'] == c_sel['id']].index[0]
                df.at[idx, 'nome'] = new_nome
                df.at[idx, 'usuario'] = new_user
                df.at[idx, 'senha'] = new_senha
                df.at[idx, 'servidor'] = new_serv
                df.at[idx, 'sistema'] = new_sistema
                df.at[idx, 'vencimento'] = new_venc.strftime('%Y-%m-%d')
                df.at[idx, 'whatsapp'] = ''.join(filter(str.isdigit, str(new_whats)))
                df.at[idx, 'custo'] = new_custo
                df.at[idx, 'mensalidade'] = new_mensal
                df.at[idx, 'observacao'] = new_obs
                df.at[idx, 'logo_blob'] = l_b
                
                conn_gs.update(data=df)
                st.session_state.cliente_selecionado = None
                st.success("Sincronizado com Google Sheets!")
                st.rerun()

            if b_excluir.button("🗑️ EXCLUIR", type="primary", use_container_width=True):
                df = df[df['id'] != c_sel['id']]
                conn_gs.update(data=df)
                st.session_state.cliente_selecionado = None
                st.rerun()
                
            if b_cancelar.button("✖️ FECHAR", use_container_width=True):
                st.session_state.cliente_selecionado = None
                st.rerun()
        st.divider()

    busca = st.text_input("🔎 Pesquisar...", placeholder="Nome ou Usuário")
    if not df.empty:
        df_f = df[df['nome'].str.contains(busca, case=False, na=False) | df['usuario'].str.contains(busca, case=False, na=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res', ascending=True).iterrows():
            img_tag = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            c1, c2 = st.columns([1, 10])
            c1.markdown(f'<img src="{img_tag}" class="img-servidor">', unsafe_allow_html=True)
            
            prefixo = "🚨 [VENCIDO] " if r['dias_res'] < 0 else "⏰ [HOJE] " if r['dias_res'] == 0 else ""
            if c2.button(f"{prefixo}{str(r['nome']).upper()} | 🔑 {r['usuario']} | 📅 {format_data_br(r['vencimento'])}", key=f"b_{r['id']}"):
                st.session_state.cliente_selecionado = r.to_dict()
                st.rerun()

with tab2:
    st.subheader("🚀 Novo Cadastro")
    with st.form("add", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        n_nome = f1.text_input("Nome")
        n_user = f2.text_input("Usuário")
        n_senha = f3.text_input("Senha")
        n_serv = f1.selectbox("Servidor", get_servidores())
        n_sistema = f2.selectbox("Sistema", ["P2P", "IPTV"])
        n_venc = f3.date_input("Vencimento", value=datetime.now() + timedelta(days=30))
        n_whats = f1.text_input("WhatsApp (DDD+Número)")
        n_custo = f2.number_input("Custo", value=10.0)
        n_valor = f3.number_input("Valor Cobrado", value=35.0)
        n_img = st.file_uploader("Logo", type=['png', 'jpg'])
        
        if st.form_submit_button("🚀 CADASTRAR CLIENTE"):
            l_b = base64.b64encode(n_img.read()).decode() if n_img else ""
            novo_id = int(df['id'].max() + 1) if not df.empty else 1
            
            nova_linha = pd.DataFrame([{
                "id": novo_id, "nome": n_nome, "usuario": n_user, "senha": n_senha,
                "servidor": n_serv, "sistema": n_sistema, "vencimento": n_venc.strftime('%Y-%m-%d'),
                "custo": n_custo, "mensalidade": n_valor, "whatsapp": ''.join(filter(str.isdigit, n_whats)),
                "observacao": "", "logo_blob": l_b
            }])
            
            df_final = pd.concat([df, nova_linha], ignore_index=True)
            conn_gs.update(data=df_final)
            st.success("Salvo no Google Sheets!")
            st.rerun()

with tab3:
    st.subheader("🚨 Central de Cobrança Automática")
    pix_cnpj = "62.326.879/0001-13" # Seu PIX
    filtro_btn = st.radio("Filtro:", ["Vencidos", "Vence Hoje", "Amanhã", "3 Dias"], horizontal=True)

    if not df.empty:
        # Lógica de filtro baseada em dias_res calculada acima
        if filtro_btn == "Vencidos": df_c = df[df['dias_res'] < 0]
        elif filtro_btn == "Vence Hoje": df_c = df[df['dias_res'] == 0]
        elif filtro_btn == "Amanhã": df_c = df[df['dias_res'] == 1]
        else: df_c = df[df['dias_res'].between(1, 3)]

        for _, c in df_c.sort_values(by='dias_res').iterrows():
            nome_p = str(c['nome']).split()[0].upper()
            msg = f"⚠️ *{nome_p}, SUA ASSINATURA VENCE EM BREVE!* \n\nPara renovar, faça o PIX CNPJ: {pix_cnpj}\nEnvie o comprovante aqui!"
            num = str(c['whatsapp'])
            if not num.startswith('55'): num = '55' + num
            st.link_button(f"📲 Cobrar: {c['nome']} ({c['vencimento']})", f"https://wa.me/{num}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Sistema Cloud")
    st.info("Os dados agora são salvos diretamente na sua planilha do Google Sheets.")
    
    if st.button("📊 Forçar Atualização de Dados"):
        st.cache_data.clear()
        st.rerun()

    st.write("📤 **Backup em Excel**")
    out = io.BytesIO()
    df.to_excel(out, index=False)
    st.download_button("⬇️ Baixar Tabela Atual", out.getvalue(), "gestao_supertv.xlsx")
