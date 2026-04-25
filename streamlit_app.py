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
    st.session_state.lista_servidores = ["Uniplay", "Mundo GF", "P2Braz", "Unitv", "Playtv", "P2Cine", "P2Speed", "Blade", "MegaTV", "Bob Player", "Ibo Player"]

# --- 2. ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; margin-bottom: 20px; }
    .logo-gestao { width: 380px; margin-bottom: -15px !important; }
    .logo-supertv { width: 320px; }
    
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; text-align: center; margin-bottom: 20px; }
    .metric-label { font-size: 12px; color: #8b949e; font-weight: bold; text-transform: uppercase; }
    .metric-value { font-size: 20px; color: #00d4ff; font-weight: 900; }

    .cliente-card {
        display: flex; align-items: center; background-color: #161b22;
        border: 1px solid #30363d; border-radius: 12px; padding: 15px;
        margin-bottom: 10px; position: relative; height: 100px;
    }
    .img-servidor-card { width: 60px; height: 60px; border-radius: 10px; object-fit: cover; margin-right: 20px; border: 1px solid #444; }
    .nome-c { font-weight: 900; font-size: 18px; color: white; text-transform: uppercase; }
    .dias-box { margin-left: 20px; padding-left: 20px; border-left: 1px solid #30363d; min-width: 120px; }
    
    .cor-vencido { color: #FF4B4B; font-weight: 900; }
    .cor-alerta { color: #FFD700; font-weight: 900; }
    .cor-ok { color: #00FF00; font-weight: 900; }
    .cor-tranquilo { color: #00D4FF; font-weight: 900; }

    .cobransa-item-box { background-color: #1c2128; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #00d4ff; }
    div.stButton > button { width: 100% !important; font-weight: bold !important; }
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

# --- 4. EXECUÇÃO ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

sheet = conectar_gs()
df = carregar_dados(sheet)
hoje = datetime.now().date()

if not df.empty:
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    # --- MÉTRICAS ---
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

    with tab1:
        if st.session_state.get('cliente_selecionado') is not None:
            c = st.session_state.cliente_selecionado
            with st.form("form_edit_full"):
                st.subheader(f"📝 GERENCIAR: {c['nome']}")
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
                if b1.form_submit_button("💾 SALVAR"):
                    idx = sheet.col_values(1).index(str(c['id'])) + 1
                    blob = base64.b64encode(eimg.read()).decode() if eimg else c['logo_blob']
                    sheet.update(f'A{idx}:L{idx}', [[c['id'], enome.upper(), euser, esenha, eserv, esist, evenc.strftime('%Y-%m-%d'), ecusto, emensal, ewhats, eobs, blob]])
                    st.session_state.cliente_selecionado = None
                    st.rerun()

                if b2.form_submit_button("⚡ RENOVAR +30 DIAS"):
                    idx = sheet.col_values(1).index(str(c['id'])) + 1
                    nova_data = (hoje + timedelta(days=30)).strftime('%Y-%m-%d')
                    sheet.update_cell(idx, 7, nova_data)
                    st.success("Renovado por +30 dias!"); st.session_state.cliente_selecionado = None
                    time.sleep(1); st.rerun()

                if b3.form_submit_button("🗑️ EXCLUIR"):
                    sheet.delete_rows(sheet.col_values(1).index(str(c['id'])) + 1)
                    st.session_state.cliente_selecionado = None; st.rerun()
                
                if b4.form_submit_button("✖️ FECHAR"):
                    st.session_state.cliente_selecionado = None; st.rerun()
            st.divider()

        busca = st.text_input("🔎 BUSCAR CLIENTE...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
            cor = get_cor_classe(r['dias_res'])
            data_br = r['dt_venc_calc'].strftime('%d/%m/%Y')
            
            with st.container():
                col_card, col_btn = st.columns([5, 1])
                col_card.markdown(f'''
                    <div class="cliente-card">
                        <img src="{img}" class="img-servidor-card">
                        <div style="flex-grow: 1; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div class="nome-c">{r['nome']}</div>
                                <span style="color:#8b949e; font-size:14px;">🔑 {r['usuario']} | 🖥️ {r['sistema']}</span>
                            </div>
                            <div class="dias-box">
                                <span class="{cor}" style="font-size:16px;">{r['dias_res']} DIAS</span><br>
                                <small style="color:#8b949e;">{data_br}</small>
                            </div>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                if col_btn.button("⚙️ ABRIR", key=f"btn_{r['id']}"):
                    st.session_state.cliente_selecionado = r.to_dict(); st.rerun()

    with tab2:
        st.subheader("🚀 NOVO CADASTRO")
        with st.form("add_cli", clear_on_submit=True):
            ca1, ca2 = st.columns(2)
            nnome = ca1.text_input("NOME")
            nuser = ca2.text_input("USUÁRIO")
            nsenha = ca1.text_input("SENHA")
            nserv = ca2.selectbox("SERVIDOR", sorted(st.session_state.lista_servidores))
            nsist = ca1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0)
            nvenc = ca2.date_input("VENCIMENTO", value=hoje + timedelta(days=30), format="DD/MM/YYYY")
            ncusto = ca1.number_input("CUSTO", value=10.0)
            nmensal = ca2.number_input("MENSALIDADE", value=35.0)
            nwhats = ca1.text_input("WHATSAPP")
            nobs = ca2.text_area("OBSERVAÇÃO")
            nimg = st.file_uploader("LOGO DO SERVIDOR", type=['png', 'jpg'])
            if st.form_submit_button("🚀 CADASTRAR"):
                prox_id = int(df['id'].max() + 1) if not df.empty else 1
                blob = base64.b64encode(nimg.read()).decode() if nimg else ""
                sheet.append_row([prox_id, nnome.upper(), nuser, nsenha, nserv, nsist, nvenc.strftime('%Y-%m-%d'), ncusto, nmensal, nwhats, nobs, blob])
                st.success("Salvo!"); st.rerun()

    # --- ABA 3: COBRANÇA (CORRIGIDA) ---
    with tab3:
        st.subheader("🚨 COBRANÇAS")
        c_cols = st.columns(6)
        filtros = ["vencidos", "hoje", "1dia", "2dias", "3dias", "todos"]
        labels = ["❌ Vencidos", "📅 Hoje", "🌅 Amanhã", "⏳ 2 Dias", "⏳ 3 Dias", "🗓️ Todos"]
        for i, f in enumerate(filtros):
            if c_cols[i].button(labels[i]): st.session_state.filtro_f = f

        filtro = st.session_state.filtro_f
        mensagens = {
            "vencidos": "🚨SUA ASSINATURA DE TV VENCEU !\n\nNÃO PREOCUPE, BASTA FAZER O PIX QUE REATIVAMOS PRA VOCÊ!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "hoje": "⚠️SUA ASSINATURA DE TV VENCE HOJE ⏰! \n\nNÃO FIQUE SEM TV, BASTA FAZER O PIX QUE RENOVAMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "1dia": "⚠️SUA ASSINATURA DE TV VENCE AMANHÃ ⏰! \n\nNÃO FIQUE SEM TV, FAÇA O PIX E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "2dias": "⚠️SUA ASSINATURA DE TV VENCE EM 2️⃣ DIAS ⏰! \n\nFAÇA O PIX  AGORA E RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "3dias": "⚠️SUA ASSINATURA DE TV VENCE EM 3️⃣ DIAS ⏰! \n\nFAÇA O PIX  AGORA E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!"
        }

        # Aplicar Filtro ANTES do Selecionar Todos
        if filtro == "vencidos": df_c = df[df['dias_res'] < 0]; msg_atual = mensagens["vencidos"]
        elif filtro == "hoje": df_c = df[df['dias_res'] == 0]; msg_atual = mensagens["hoje"]
        elif filtro == "1dia": df_c = df[df['dias_res'] == 1]; msg_atual = mensagens["1dia"]
        elif filtro == "2dias": df_c = df[df['dias_res'] == 2]; msg_atual = mensagens["2dias"]
        elif filtro == "3dias": df_c = df[df['dias_res'] == 3]; msg_atual = mensagens["3dias"]
        else: df_c = df; msg_atual = "Lembrete SUPERTV4K"

        if not df_c.empty:
            # O Selecionar Todos agora só afeta os IDs da lista 'df_c' (a filtrada)
            sel_all = st.checkbox(f"✅ Selecionar apenas os {len(df_c)} clientes desta lista", key=f"sel_all_{filtro}")
            for _, r in df_c.iterrows():
                with st.container():
                    col_ch, col_inf, col_z = st.columns([0.4, 4, 1.6])
                    col_ch.checkbox("", value=sel_all, key=f"chk_{r['id']}")
                    col_inf.markdown(f'<div class="cobransa-item-box"><strong>{r["nome"]}</strong> | {r["sistema"]}<br><small>Venc: {r["dt_venc_calc"].strftime("%d/%m/%Y")}</small></div>', unsafe_allow_html=True)
                    col_z.link_button("📲 COBRAR", f"https://wa.me/55{r['whatsapp']}?text={urllib.parse.quote(msg_atual)}")

    # --- ABA 4: AJUSTES ---
    with tab4:
        st.subheader("⚙️ AJUSTES")
        srv_nome = st.text_input("Nome do Servidor")
        col_s1, col_s2 = st.columns(2)
        if col_s1.button("💾 SALVAR SERVIDOR"):
            if srv_nome and srv_nome not in st.session_state.lista_servidores:
                st.session_state.lista_servidores.append(srv_nome); st.rerun()
        if col_s2.button("🗑️ EXCLUIR SERVIDOR"):
            if srv_nome in st.session_state.lista_servidores:
                st.session_state.lista_servidores.remove(srv_nome); st.rerun()
        st.divider()
        if st.button("🔄 SINCRONIZAR GOOGLE SHEETS"): st.rerun()
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.drop(columns=['dt_venc_calc', 'dias_res']).to_excel(writer, index=False)
        st.download_button(label="📥 BACKUP EXCEL", data=buffer.getvalue(), file_name=f"backup_supertv_{datetime.now().strftime('%d_%m_%Y')}.xlsx")
