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

query_params = st.query_params
if "editar_id" in query_params:
    st.session_state.id_para_editar = query_params["editar_id"]

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

# --- 2. ESTILIZAÇÃO CSS (AJUSTE DE LARGURA E PROPORÇÃO) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; margin-bottom: 20px; }
    .logo-gestao { width: 380px; margin-bottom: -15px !important; }
    .logo-supertv { width: 320px; }
    
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; margin-bottom: 20px; }
    .metric-label { font-size: 12px; color: #8b949e; font-weight: bold; text-transform: uppercase; }
    .metric-value { font-size: 20px; color: #00d4ff; font-weight: 900; }

    /* AJUSTE: Centraliza e limita a largura do botão/link */
    .card-link { 
        text-decoration: none !important; 
        color: inherit !important; 
        display: block; 
        margin: 0 auto 12px auto; /* Centraliza o card */
        max-width: 500px; /* Define o tamanho retangular estreito */
    }
    
    .cliente-card-html {
        display: flex; align-items: center; background-color: #161b22;
        border: 1px solid #30363d; border-radius: 12px; padding: 12px 15px;
        min-height: 80px; width: 100%; transition: 0.2s;
        overflow: hidden;
    }
    .cliente-card-html:hover { border-color: #00d4ff; background-color: #1c2128; }
    
    .img-servidor-card { width: 55px; height: 55px; border-radius: 8px; object-fit: cover; margin-right: 15px; border: 1px solid #444; flex-shrink: 0; }
    .info-container { flex-grow: 1; display: flex; flex-direction: column; justify-content: center; min-width: 0; }
    .nome-c { font-weight: 900; font-size: 16px; color: white; text-transform: uppercase; line-height: 1.2; }
    .dias-box { flex-shrink: 0; margin-left: 15px; padding-left: 15px; border-left: 1px solid #30363d; width: 100px; text-align: right; }
    
    .cor-vencido { color: #FF4B4B; font-weight: 900; }
    .cor-alerta { color: #FFD700; font-weight: 900; }
    .cor-ok { color: #00FF00; font-weight: 900; }
    .cor-tranquilo { color: #00D4FF; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE DADOS (PRESERVADAS) ---
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

# --- LÓGICA DE SELEÇÃO ---
if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    if "id_para_editar" in st.session_state:
        sel = df[df['id'].astype(str) == str(st.session_state.id_para_editar)]
        if not sel.empty:
            st.session_state.cliente_selecionado = sel.iloc[0].to_dict()
            del st.session_state.id_para_editar

# --- 4. INTERFACE ---
if st.session_state.get('cliente_selecionado') is not None:
    c = st.session_state.cliente_selecionado
    st.markdown("### 📝 GERENCIANDO CLIENTE SELECIONADO")
    with st.form("form_edit_full"):
        col1, col2 = st.columns(2)
        enome = col1.text_input("NOME", value=c['nome'])
        euser = col2.text_input("USUÁRIO", value=c['usuario'])
        esenha = col1.text_input("SENHA", value=c['senha'])
        eserv = col2.selectbox("SERVIDOR", sorted(st.session_state.lista_servidores), index=st.session_state.lista_servidores.index(c['servidor']) if c['servidor'] in st.session_state.lista_servidores else 0)
        esist = col1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if c['sistema']=="P2P" else 1)
        evenc = col2.date_input("VENCIMENTO", value=pd.to_datetime(c['vencimento']).date(), format="DD/MM/YYYY")
        ecusto = col1.number_input("CUSTO", value=float(c['custo']))
        emensal = col2.number_input("MENSALIDADE", value=float(c['mensalidade']))
        ewhats = col1.text_input("WHATSAPP", value=c['whatsapp'])
        eobs = col2.text_area("OBSERVAÇÃO", value=c['observacao'])
        eimg = st.file_uploader("TROCAR LOGO", type=['png', 'jpg'])
        
        b1, b2, b3, b4 = st.columns(4)
        if b1.form_submit_button("💾 SALVAR ALTERAÇÕES"):
            idx = sheet.col_values(1).index(str(c['id'])) + 1
            blob = base64.b64encode(eimg.read()).decode() if eimg else c['logo_blob']
            sheet.update(f'A{idx}:L{idx}', [[c['id'], enome.upper(), euser, esenha, eserv, esist, evenc.strftime('%Y-%m-%d'), ecusto, emensal, ewhats, eobs, blob]])
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()

        if b2.form_submit_button("⚡ RENOVAR +30 DIAS"):
            idx = sheet.col_values(1).index(str(c['id'])) + 1
            nova_data = (hoje + timedelta(days=30)).strftime('%Y-%m-%d')
            sheet.update_cell(idx, 7, nova_data)
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()

        if b3.form_submit_button("🗑️ EXCLUIR CLIENTE"):
            sheet.delete_rows(sheet.col_values(1).index(str(c['id'])) + 1)
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()
        
        if b4.form_submit_button("✖️ FECHAR SEM SALVAR"):
            st.session_state.cliente_selecionado = None; st.query_params.clear(); st.rerun()
    st.divider()

st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

if not df.empty:
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-card"><div class="metric-label">👤 Ativos</div><div class="metric-value">{len(df[df["dias_res"]>=0])}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">❌ Vencidos</div><div class="metric-value" style="color:#ff4b4b">{len(df[df["dias_res"]<0])}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-label">⏰ Vence Hoje</div><div class="metric-value" style="color:#ffd700">{len(df[df["dias_res"]==0])}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-label">💰 Lucro Líquido</div><div class="metric-value" style="color:#00ff88">R$ {(df["mensalidade"].sum()-df["custo"].sum()):,.2f}</div></div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    with tab1:
        busca = st.text_input("🔎 BUSCAR CLIENTE...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            cor = get_cor_classe(r['dias_res'])
            data_br = r['dt_venc_calc'].strftime('%d/%m/%Y')
            st.markdown(f'''<a href="/?editar_id={r['id']}" target="_self" class="card-link"><div class="cliente-card-html"><img src="{img}" class="img-servidor-card"><div class="info-container"><div class="nome-c">{r['nome']}</div><span style="color:#8b949e; font-size:14px;">🔑 {r['usuario']} | 🖥️ {r['sistema']}</span></div><div class="dias-box"><span class="{cor}" style="font-size:16px;">{r['dias_res']} DIAS</span><br><small style="color:#8b949e;">{data_br}</small></div></div></a>''', unsafe_allow_html=True)

    with tab2:
        st.subheader("🚀 NOVO CADASTRO")
        with st.form("add_cli", clear_on_submit=True):
            ca1, ca2 = st.columns(2)
            nnome = ca1.text_input("NOME"); nuser = ca2.text_input("USUÁRIO")
            nsenha = ca1.text_input("SENHA"); nserv = ca2.selectbox("SERVIDOR", sorted(st.session_state.lista_servidores))
            nsist = ca1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0); nvenc = ca2.date_input("VENCIMENTO", value=hoje + timedelta(days=30), format="DD/MM/YYYY")
            ncusto = ca1.number_input("CUSTO", value=10.0); nmensal = ca2.number_input("MENSALIDADE", value=35.0)
            nwhats = ca1.text_input("WHATSAPP"); nobs = ca2.text_area("OBSERVAÇÃO"); nimg = st.file_uploader("LOGO", type=['png', 'jpg'])
            if st.form_submit_button("🚀 CADASTRAR"):
                prox_id = int(df['id'].max() + 1) if not df.empty else 1
                blob = base64.b64encode(nimg.read()).decode() if nimg else ""
                sheet.append_row([prox_id, nnome.upper(), nuser, nsenha, nserv, nsist, nvenc.strftime('%Y-%m-%d'), ncusto, nmensal, nwhats, nobs, blob])
                st.rerun()

    with tab3:
        if st.session_state.executando_disparo:
            fila = st.session_state.clientes_para_disparo
            idx = st.session_state.indice_disparo
            if idx < len(fila):
                cliente = fila[idx]
                st.warning(f"🚀 ENVIANDO EM MASSA: {idx + 1} de {len(fila)}")
                st.subheader(f"Cliente: {cliente['nome']}")
                cnpj_pix = "\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!"
                msg_map = {"vencidos": "🚨SUA ASSINATURA DE TV VENCEU !" + cnpj_pix, "hoje": "⚠️SUA ASSINATURA DE TV VENCE HOJE ⏰!" + cnpj_pix, "1dia": "⚠️SUA ASSINATURA DE TV VENCE AMANHÃ ⏰!" + cnpj_pix, "2dias": "⚠️SUA ASSINATURA DE TV VENCE EM 2️⃣ DIAS ⏰!" + cnpj_pix, "3dias": "⚠️SUA ASSINATURA DE TV VENCE EM 3️⃣ DIAS ⏰!" + cnpj_pix, "todos": "Olá! Segue seu lembrete de renovação SUPERTV4K."}
                msg_atual = msg_map.get(st.session_state.filtro_f, msg_map["todos"])
                url_whats = f"https://wa.me/55{cliente['whatsapp']}?text={urllib.parse.quote(msg_atual)}"
                col1, col2, col3 = st.columns(3)
                if col1.link_button("📲 ENVIAR AGORA", url_whats, type="primary"): st.session_state.aguardando_proximo = True
                if col2.button("⏭️ PULAR"): st.session_state.indice_disparo += 1; st.rerun()
                if col3.button("✖️ PARAR DISPARO"): st.session_state.executando_disparo = False; st.rerun()
                if st.session_state.get('aguardando_proximo'):
                    st.info("⏱️ Aguardando 10 segundos...")
                    barra = st.progress(0)
                    for i in range(10): time.sleep(1); barra.progress((i + 1) * 10)
                    st.session_state.indice_disparo += 1; st.session_state.aguardando_proximo = False; st.rerun()
            else:
                st.success("✅ Fila finalizada!"); st.session_state.executando_disparo = False
                if st.button("VOLTAR"): st.rerun()
        else:
            st.subheader("🚨 COBRANÇAS")
            c_cols = st.columns(6)
            filtros = ["vencidos", "hoje", "1dia", "2dias", "3dias", "todos"]
            labels = ["❌ Vencidos", "📅 Hoje", "🌅 Amanhã", "⏳ 2 Dias", "⏳ 3 Dias", "🗓️ Todos"]
            for i, f in enumerate(filtros):
                if c_cols[i].button(labels[i]): st.session_state.filtro_f = f
            
            filtro = st.session_state.filtro_f
            df_c = df
            if filtro == "vencidos": df_c = df[df['dias_res'] < 0]
            elif filtro == "hoje": df_c = df[df['dias_res'] == 0]
            elif filtro == "1dia": df_c = df[df['dias_res'] == 1]
            elif filtro == "2dias": df_c = df[df['dias_res'] == 2]
            elif filtro == "3dias": df_c = df[df['dias_res'] == 3]

            if not df_c.empty:
                col_btn1, col_btn2 = st.columns([4, 2])
                sel_all = col_btn1.checkbox(f"✅ Selecionar todos ({len(df_c)})", key=f"sel_all_{filtro}")
                clientes_marcados = []
                for _, r in df_c.iterrows():
                    img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
                    cor = get_cor_classe(r['dias_res'])
                    with st.container():
                        c1, c2, c3 = st.columns([0.5, 4.3, 1.2])
                        if c1.checkbox("", value=sel_all, key=f"chk_{r['id']}"): clientes_marcados.append(r.to_dict())
                        c2.markdown(f'<div class="cliente-card-html"><img src="{img}" class="img-servidor-card"><div class="info-container"><div class="nome-c">{r["nome"]}</div><span style="color:#8b949e;">{r["sistema"]}</span></div><div class="dias-box"><span class="{cor}">{r["dias_res"]} DIAS</span></div></div>', unsafe_allow_html=True)
                        url_whats = f"https://wa.me/55{r['whatsapp']}?text={urllib.parse.quote(msg_map.get(filtro, msg_map['todos']))}"
                        c3.link_button("📲 COBRAR", url_whats)
                if col_btn2.button("🚀 ENVIAR EM MASSA", type="primary"):
                    if clientes_marcados: st.session_state.clientes_para_disparo = clientes_marcados; st.session_state.indice_disparo = 0; st.session_state.executando_disparo = True; st.rerun()

    with tab4:
        st.subheader("⚙️ AJUSTES")
        srv_nome = st.text_input("NOME DO SERVIDOR")
        if st.button("💾 SALVAR"):
            if srv_nome and srv_nome not in st.session_state.lista_servidores: st.session_state.lista_servidores.append(srv_nome); st.rerun()
        if st.button("🔄 SINCRONIZAR"): st.rerun()
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer: df.drop(columns=['dt_venc_calc', 'dias_res']).to_excel(writer, index=False)
        st.download_button("📥 BACKUP EXCEL", data=buffer.getvalue(), file_name="backup_supertv.xlsx")
