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

# Inicialização de estados
if 'filtro_f' not in st.session_state:
    st.session_state.filtro_f = "vencidos"

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
    .cobransa-item {
        background-color: #1c2128; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #00d4ff;
    }
    .vencido-border { border-left: 5px solid #ff4b4b !important; }
    div.stButton > button { width: 100% !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE DADOS ---
def conectar_gs():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1ntE8RpofySu5IFupuvOZxZnrnmHKzaYbyqAQ-Mzc8so").sheet1
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return None

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

    # ABA CLIENTES (Edição e Lista)
    with tab1:
        if st.session_state.get('cliente_selecionado') is not None:
            c = st.session_state.cliente_selecionado
            with st.form("edit_form"):
                e_nome = st.text_input("NOME", value=c['nome'])
                e_user = st.text_input("USUÁRIO", value=c['usuario'])
                e_senha = st.text_input("SENHA", value=c['senha'])
                e_serv = st.selectbox("SERVIDOR", sorted(st.session_state.lista_servidores), index=sorted(st.session_state.lista_servidores).index(c['servidor']) if c['servidor'] in st.session_state.lista_servidores else 0)
                e_sist = st.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if c['sistema'] == "P2P" else 1)
                e_venc = st.date_input("VENCIMENTO", value=pd.to_datetime(c['vencimento']).date())
                e_custo = st.number_input("CUSTO", value=float(c['custo']))
                e_mensal = st.number_input("MENSALIDADE", value=float(c['mensalidade']))
                e_whats = st.text_input("WHATSAPP", value=c['whatsapp'])
                e_obs = st.text_area("OBSERVAÇÃO", value=c['observacao'])
                e_img = st.file_uploader("LOGO_BLOB", type=['png', 'jpg'])
                
                b1, b2, b3 = st.columns(3)
                if b1.form_submit_button("💾 SALVAR"):
                    idx = sheet.col_values(1).index(str(c['id'])) + 1
                    blob = base64.b64encode(e_img.read()).decode() if e_img else c['logo_blob']
                    sheet.update(f'A{idx}:L{idx}', [[c['id'], e_nome.upper(), e_user, e_senha, e_serv, e_sist, e_venc.strftime('%Y-%m-%d'), e_custo, e_mensal, e_whats, e_obs, blob]])
                    st.session_state.cliente_selecionado = None
                    st.rerun()
                if b2.form_submit_button("🗑️ EXCLUIR"):
                    sheet.delete_rows(sheet.col_values(1).index(str(c['id'])) + 1)
                    st.session_state.cliente_selecionado = None
                    st.rerun()
                if b3.form_submit_button("✖️ FECHAR"):
                    st.session_state.cliente_selecionado = None
                    st.rerun()

        busca = st.text_input("🔎 PESQUISAR CLIENTE...")
        df_f = df[df['nome'].str.contains(busca, case=False)] if busca else df
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            st.markdown(f'<div class="cobransa-item"><strong>{r["nome"]}</strong> | {r["servidor"]} | {r["dias_res"]} Dias</div>', unsafe_allow_html=True)
            if st.button(f"EDITAR {r['id']}", key=f"edit_list_{r['id']}"):
                st.session_state.cliente_selecionado = r.to_dict()
                st.rerun()

    # ABA ADICIONAR
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
                st.success("Salvo com sucesso!"); time.sleep(1); st.rerun()

    # ABA COBRANÇA
    with tab3:
        st.subheader("🚨 GESTÃO DE COBRANÇAS")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        if c1.button("❌ Vencidos"): st.session_state.filtro_f = "vencidos"
        if c2.button("📅 Hoje"): st.session_state.filtro_f = "hoje"
        if c3.button("🌅 Amanhã"): st.session_state.filtro_f = "1dia"
        if c4.button("⏳ 2 Dias"): st.session_state.filtro_f = "2dias"
        if c5.button("⏳ 3 Dias"): st.session_state.filtro_f = "3dias"
        if c6.button("🗓️ Todos"): st.session_state.filtro_f = "todos"

        filtro = st.session_state.filtro_f
        mensagens = {
            "vencidos": "🚨SUA ASSINATURA DE TV VENCEU !\n\nNÃO PREOCUPE, BASTA FAZER O PIX QUE REATIVAMOS PRA VOCÊ!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "hoje": "⚠️SUA ASSINATURA DE TV VENCE HOJE ⏰! \n\nNÃO FIQUE SEM TV, BASTA FAZER O PIX QUE RENOVAMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "1dia": "⚠️SUA ASSINATURA DE TV VENCE AMANHÃ ⏰! \n\nNÃO FIQUE SEM TV, FAÇA O PIX E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "2dias": "⚠️SUA ASSINATURA DE TV VENCE EM 2️⃣ DIAS ⏰! \n\nFAÇA O PIX  AGORA E RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!",
            "3dias": "⚠️SUA ASSINATURA DE TV VENCE EM 3️⃣ DIAS ⏰! \n\nFAÇA O PIX  AGORA E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!"
        }

        if filtro == "vencidos": df_c = df[df['dias_res'] < 0]; msg_atual = mensagens["vencidos"]
        elif filtro == "hoje": df_c = df[df['dias_res'] == 0]; msg_atual = mensagens["hoje"]
        elif filtro == "1dia": df_c = df[df['dias_res'] == 1]; msg_atual = mensagens["1dia"]
        elif filtro == "2dias": df_c = df[df['dias_res'] == 2]; msg_atual = mensagens["2dias"]
        elif filtro == "3dias": df_c = df[df['dias_res'] == 3]; msg_atual = mensagens["3dias"]
        else: df_c = df; msg_atual = "Lembrete SUPERTV4K"

        st.info(f"Filtro: {filtro.upper()} | {len(df_c)} clientes.")
        if not df_c.empty:
            sel_all = st.checkbox("✅ Selecionar Todos da Lista")
            clientes_sel = []
            for _, r in df_c.iterrows():
                with st.container():
                    col_ch, col_inf, col_z = st.columns([0.4, 4, 1.6])
                    if col_ch.checkbox("", value=sel_all, key=f"cobr_{r['id']}"): clientes_sel.append(r)
                    border = "vencido-border" if r['dias_res'] < 0 else ""
                    col_inf.markdown(f'<div class="cobransa-item {border}"><strong>{r["nome"]}</strong> | {r["servidor"]}<br><small>Vencimento: {r["vencimento"]}</small></div>', unsafe_allow_html=True)
                    col_z.link_button("📲 COBRAR", f"https://wa.me/55{r['whatsapp']}?text={urllib.parse.quote(msg_atual)}")
            if clientes_sel and st.button("📢 GERAR LINKS EM MASSA"):
                for s in clientes_sel: st.write(f"👉 **{s['nome']}**: https://wa.me/55{s['whatsapp']}?text={urllib.parse.quote(msg_atual)}")

    # ABA AJUSTES (RECUPERADA)
    with tab4:
        st.subheader("⚙️ AJUSTES DO SISTEMA")
        st.markdown("### 🖥️ Gerenciar Servidores")
        srv_nome = st.text_input("Nome do Servidor (para salvar ou excluir)")
        col_s1, col_s2 = st.columns(2)
        if col_s1.button("💾 SALVAR SERVIDOR"):
            if srv_nome and srv_nome not in st.session_state.lista_servidores:
                st.session_state.lista_servidores.append(srv_nome); st.success(f"'{srv_nome}' salvo!"); st.rerun()
        if col_s2.button("🗑️ EXCLUIR SERVIDOR"):
            if srv_nome in st.session_state.lista_servidores:
                st.session_state.lista_servidores.remove(srv_nome); st.warning(f"'{srv_nome}' removido!"); st.rerun()
        
        st.divider()
        st.markdown("### 🛠️ Ferramentas e Dados")
        as1, as2 = st.columns(2)
        if as1.button("🔄 SINCRONIZAR SHEETS"): st.rerun()
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Clientes')
        as2.download_button(label="📥 BACKUP EXCEL", data=buffer.getvalue(), file_name=f"backup_supertv_{hoje}.xlsx")
        
        st.markdown("---")
        st.file_uploader("📤 UPLOAD DE ARQUIVO (CSV/Excel)", type=['csv', 'xlsx'])
