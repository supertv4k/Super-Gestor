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

# --- 2. ESTILIZAÇÃO CSS (DESIGN DOS CARDS) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; margin-bottom: 20px; }
    .logo-gestao { width: 380px; margin-bottom: -15px !important; }
    .logo-supertv { width: 320px; }
    
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; margin-bottom: 20px; }
    .metric-label { font-size: 12px; color: #8b949e; font-weight: bold; text-transform: uppercase; }
    .metric-value { font-size: 20px; color: #00d4ff; font-weight: 900; }

    .card-link { text-decoration: none !important; color: inherit !important; display: block; margin-bottom: 12px; }
    
    .cliente-card-html {
        display: flex; align-items: center; background-color: #161b22;
        border: 1px solid #30363d; border-radius: 12px; padding: 15px;
        min-height: 100px; width: 100%; transition: 0.2s;
        overflow: hidden;
    }
    .cliente-card-html:hover { border-color: #00d4ff; background-color: #1c2128; }
    
    .img-servidor-card { width: 60px; height: 60px; border-radius: 10px; object-fit: cover; margin-right: 15px; border: 1px solid #444; flex-shrink: 0; }
    .info-container { flex-grow: 1; display: flex; flex-direction: column; justify-content: center; min-width: 0; }
    .nome-c { font-weight: 900; font-size: 17px; color: white; text-transform: uppercase; word-wrap: break-word; line-height: 1.2; margin-bottom: 4px; }
    .dias-box { flex-shrink: 0; margin-left: 15px; padding-left: 15px; border-left: 1px solid #30363d; width: 115px; text-align: right; }
    
    .cor-vencido { color: #FF4B4B; font-weight: 900; }
    .cor-alerta { color: #FFD700; font-weight: 900; }
    .cor-ok { color: #00FF00; font-weight: 900; }
    .cor-tranquilo { color: #00D4FF; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE DADOS ---
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

# --- LÓGICA DE SELEÇÃO DE CLIENTE ---
if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    if "id_para_editar" in st.session_state:
        sel = df[df['id'].astype(str) == str(st.session_state.id_para_editar)]
        if not sel.empty:
            st.session_state.cliente_selecionado = sel.iloc[0].to_dict()
            del st.session_state.id_para_editar

# --- 4. INTERFACE ---

# MODO FOCO: Se clicar em um cliente, o formulário aparece PRIMEIRO
if st.session_state.get('cliente_selecionado') is not None:
    c = st.session_state.cliente_selecionado
    st.markdown("### 📝 GERENCIANDO CLIENTE SELECIONADO")
    with st.form("form_edit_full"):
        col1, col2 = st.columns(2)
        # ORDENADO CONFORME GOOGLE SHEETS
        enome = col1.text_input("NOME", value=c['nome'])
        euser = col2.text_input("USUÁRIO", value=c['usuario'])
        esenha = col1.text_input("SENHA", value=c['senha'])
        eserv = col2.selectbox("SERVIDOR", sorted(st.session_state.lista_servidores), index=st.session_state.lista_servidores.index(c['servidor']) if c['servidor'] in st.session_state.lista_servidores else 0)
        esist = col1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if c['sistema']=="P2P" else 1)
        evenc = col2.date_input("VENCIMENTO", value=pd.to_datetime(c['vencimento']).date(), format="DD/MM/YYYY")
        ecusto = col1.number_input("CUSTO", value=float(c['custo']))
        emensal = col2.number_input("MENSALIDADE", value=float(c['mensalidade']))
        ewhats = col1.text_input("WHATSAPP", value=c['whatsapp'])
        eimg = col2.file_uploader("TROCAR LOGO", type=['png', 'jpg'])
        eobs = st.text_area("OBSERVAÇÃO", value=c['observacao'])
        
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

# CABEÇALHO E MÉTRICAS
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

if not df.empty:
    vencidos_count = len(df[df['dias_res'] < 0])
    vencem_hoje_count = len(df[df['dias_res'] == 0])
    ativos_count = len(df[df['dias_res'] >= 0])
    lucro = df["mensalidade"].sum() - df["custo"].sum()

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-card"><div class="metric-label">👤 Ativos</div><div class="metric-value">{ativos_count}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">❌ Vencidos</div><div class="metric-value" style="color:#ff4b4b">{vencidos_count}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-label">⏰ Vence Hoje</div><div class="metric-value" style="color:#ffd700">{vencem_hoje_count}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-label">💰 Lucro Líquido</div><div class="metric-value" style="color:#00ff88">R$ {lucro:,.2f}</div></div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADICIONAR", "🚨 COBRANÇA", "⚙️ AJUSTES"])

    # TABELA DE BUSCA
    with tab1:
        busca = st.text_input("🔎 BUSCAR CLIENTE...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            cor = get_cor_classe(r['dias_res'])
            data_br = r['dt_venc_calc'].strftime('%d/%m/%Y')
            
            st.markdown(f'''
                <a href="/?editar_id={r['id']}" target="_self" class="card-link">
                    <div class="cliente-card-html">
                        <img src="{img}" class="img-servidor-card">
                        <div class="info-container">
                            <div class="nome-c">{r['nome']}</div>
                            <span style="color:#8b949e; font-size:14px;">🔑 {r['usuario']} | 🖥️ {r['sistema']}</span>
                        </div>
                        <div class="dias-box">
                            <span class="{cor}" style="font-size:16px;">{r['dias_res']} DIAS</span><br>
                            <small style="color:#8b949e;">{data_br}</small>
                        </div>
                    </div>
                </a>
            ''', unsafe_allow_html=True)

    # CADASTRO NOVO (ORDENADO CONFORME GOOGLE SHEETS)
    with tab2:
        st.subheader("🚀 NOVO CADASTRO")
        with st.form("add_cli", clear_on_submit=True):
            ca1, ca2 = st.columns(2)
            nnome = ca1.text_input("NOME"); nuser = ca2.text_input("USUÁRIO")
            nsenha = ca1.text_input("SENHA"); nserv = ca2.selectbox("SERVIDOR", sorted(st.session_state.lista_servidores))
            nsist = ca1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0); nvenc = ca2.date_input("VENCIMENTO", value=hoje + timedelta(days=30), format="DD/MM/YYYY")
            ncusto = ca1.number_input("CUSTO", value=10.0); nmensal = ca2.number_input("MENSALIDADE", value=35.0)
            nwhats = ca1.text_input("WHATSAPP"); nimg = ca2.file_uploader("LOGO", type=['png', 'jpg'])
            nobs = st.text_area("OBSERVAÇÃO")
            if st.form_submit_button("🚀 CADASTRAR"):
                prox_id = int(df['id'].max() + 1) if not df.empty else 1
                blob = base64.b64encode(nimg.read()).decode() if nimg else ""
                sheet.append_row([prox_id, nnome.upper(), nuser, nsenha, nserv, nsist, nvenc.strftime('%Y-%m-%d'), ncusto, nmensal, nwhats, nobs, blob])
                st.rerun()

    # COBRANÇA (MENSAGENS ATUALIZADAS)
    with tab3:
        st.subheader("🚨 COBRANÇAS")
        c_cols = st.columns(6)
        filtros = ["vencidos", "hoje", "1dia", "2dias", "3dias", "todos"]
        labels = ["❌ Vencidos", "📅 Hoje", "🌅 Amanhã", "⏳ 2 Dias", "⏳ 3 Dias", "🗓️ Todos"]
        for i, f in enumerate(filtros):
            if c_cols[i].button(labels[i]): st.session_state.filtro_f = f
        
        filtro = st.session_state.filtro_f
        
        msg_map = {
            "vencidos": "🚨SUA ASSINATURA DE TV VENCEU !\n\nNÃO PREOCUPE, BASTA FAZER O PIX QUE REATIVAMOS PRA VOCÊ!\n\n💠PIX\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "hoje": "⚠️SUA ASSINATURA DE TV VENCE HOJE ⏰! \n\nNÃO FIQUE SEM TV, BASTA FAZER O PIX QUE RENOVAMOS PRA VOCÊ +30 DIAS!\n\n💠PIX\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "1dia": "⚠️SUA ASSINATURA DE TV VENCE AMANHÃ ⏰! \n\nNÃO FIQUE SEM TV, FAÇA O PIX E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "2dias": "⚠️SUA ASSINATURA DE TV VENCE EM 2️⃣ DIAS ⏰! \n\nFAÇA O PIX AGORA E RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "3dias": "⚠️SUA ASSINATURA DE TV VENCE EM 3️⃣ DIAS ⏰! \n\nFAÇA O PIX AGORA E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "todos": "Olá! Segue seu lembrete de renovação SUPERTV4K."
        }
        msg_atual = msg_map.get(filtro, msg_map["todos"])

        df_c = df
        if filtro == "vencidos": df_c = df[df['dias_res'] < 0]
        elif filtro == "hoje": df_c = df[df['dias_res'] == 0]
        elif filtro == "1dia": df_c = df[df['dias_res'] == 1]
        elif filtro == "2dias": df_c = df[df['dias_res'] == 2]
        elif filtro == "3dias": df_c = df[df['dias_res'] == 3]

        if not df_c.empty:
            sel_all = st.checkbox(f"✅ Selecionar todos ({len(df_c)})", key=f"sel_all_{filtro}")
            for _, r in df_c.iterrows():
                img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
                cor = get_cor_classe(r['dias_res'])
                with st.container():
                    c1, c2, c3 = st.columns([0.5, 4.3, 1.2])
                    c1.checkbox("", value=sel_all, key=f"chk_{r['id']}")
                    c2.markdown(f'<div class="cliente-card-html"><img src="{img}" class="img-servidor-card"><div class="info-container"><div class="nome-c">{r["nome"]}</div><span style="color:#8b949e;">{r["sistema"]}</span></div><div class="dias-box"><span class="{cor}">{r["dias_res"]} DIAS</span></div></div>', unsafe_allow_html=True)
                    url_whats = f"https://wa.me/55{r['whatsapp']}?text={urllib.parse.quote(msg_atual)}"
                    c3.link_button("📲 COBRAR", url_whats)

    # AJUSTES
    with tab4:
        st.subheader("⚙️ AJUSTES DO SISTEMA")
        srv_nome = st.text_input("NOME DO SERVIDOR")
        if st.button("💾 SALVAR SERVIDOR"):
            if srv_nome and srv_nome not in st.session_state.lista_servidores:
                st.session_state.lista_servidores.append(srv_nome); st.rerun()
        if st.button("🗑️ EXCLUIR SERVIDOR"):
            if srv_nome in st.session_state.lista_servidores:
                st.session_state.lista_servidores.remove(srv_nome); st.rerun()
        st.divider()
        if st.button("🔄 SINCRONIZAR"): st.rerun()
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.drop(columns=['dt_venc_calc', 'dias_res']).to_excel(writer, index=False)
        st.download_button("📥 GERAR BACKUP EXCEL", data=buffer.getvalue(), file_name="backup_supertv.xlsx")
