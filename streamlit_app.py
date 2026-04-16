import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta, time
import urllib.parse
import io
import base64
import time as t_lib

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    
    .cliente-row {
        background-color: #161b22; border: 1px solid #30363d; border-radius: 12px;
        padding: 15px; margin-bottom: 0px; display: flex; align-items: center; gap: 20px;
    }
    .logo-externa {
        width: 85px; height: 85px; border-radius: 10px;
        object-fit: contain; background: #21262d; border: 1px solid #444;
    }
    .info-container { flex-grow: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .info-txt { font-size: 14px; color: #c9d1d9; }
    .destaque-vermelho { color: #ff4b4b; font-weight: bold; }
    .destaque-verde { color: #00ff00; font-weight: bold; }
    
    .stExpander { border: none !important; background-color: #161b22 !important; margin-bottom: 15px !important; border-radius: 0 0 12px 12px !important; }
    
    .metric-card { 
        background-color: #161b22; padding: 15px; border-radius: 12px; 
        text-align: center; border: 1px solid #30363d; margin-bottom: 10px; 
    }
    .metric-label { font-size: 11px; font-weight: bold; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 20px; font-weight: bold; color: #ff0000; margin-top: 5px; }

    div.stFormSubmitButton > button {
        background: linear-gradient(135deg, #0052D4 0%, #929ED1 50%, #E0EAFC 100%) !important;
        color: #1e1e1e !important; font-weight: 900 !important; border-radius: 10px !important;
        width: 100%; height: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE APOIO ---
def limpar_numero(valor):
    if valor is None or str(valor).strip() == "" or str(valor).lower() == 'nan':
        return 0.0
    try:
        v = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        return float(v)
    except:
        return 0.0

def image_to_base64(image_file):
    if image_file is not None:
        try:
            return base64.b64encode(image_file.read()).decode()
        except: return None
    return None

def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento TEXT, custo REAL, mensalidade REAL, 
                  inicio TEXT, observacao TEXT, logo_blob TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    conn.commit()
    conn.close()

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    try: 
        lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    except: 
        lista = []
    conn.close()
    return lista if lista else ["UNITV", "UNIPLAY", "P2BRAZ", "MUNDOGF", "PLAY TV"]

def adicionar_servidor(nome):
    if nome:
        conn = sqlite3.connect('supertv_gestao.db')
        try:
            conn.execute("INSERT INTO lista_servidores (nome) VALUES (?)", (nome.upper(),))
            conn.commit()
            return True
        except: return False
        finally: conn.close()
    return False

def excluir_servidor(nome):
    conn = sqlite3.connect('supertv_gestao.db')
    conn.execute("DELETE FROM lista_servidores WHERE nome = ?", (nome,))
    conn.commit(); conn.close()

# Inicializa o banco de dados
init_db()

# --- 4. CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- 5. HEADER ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

# --- 6. DASHBOARD ---
if not df.empty:
    hoje_dt = datetime.now()
    # Converte vencimento com segurança
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').fillna(hoje_dt)
    df['dias_res'] = (df['dt_venc_calc'].dt.date - hoje_dt.date()).apply(lambda x: x.days)
    
    bruto = df['mensalidade'].apply(limpar_numero).sum()
    custos = df['custo'].apply(limpar_numero).sum()
    liquido = bruto - custos

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value">{len(df[df["dias_res"] < 0])}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">VENCENDO</div><div class="metric-value">{len(df[(df["dias_res"] >= 0) & (df["dias_res"] <= 3)])}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">BRUTO</div><div class="metric-value">R${bruto:,.2f}</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-label">LÍQUIDO</div><div class="metric-value">R${liquido:,.2f}</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="metric-card"><div class="metric-label">CUSTO</div><div class="metric-value">R${custos:,.2f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 7. ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADD CLIENTE", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔎 Pesquisar cliente...", placeholder="Nome ou Usuário...")
    if not df.empty:
        df_f = df.copy()
        if busca:
            df_f = df_f[df_f['nome'].astype(str).str.contains(busca, case=False, na=False) | df_f['usuario'].astype(str).str.contains(busca, case=False, na=False)]

        for _, r in df_f.sort_values(by='dias_res').iterrows():
            status_cor = "destaque-verde" if r['dias_res'] >= 0 else "destaque-vermelho"
            dias_txt = f"{r['dias_res']} DIAS" if r['dias_res'] >= 0 else "VENCIDO"
            img_data = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
            
            st.markdown(f"""<div class="cliente-row"><img src="{img_data}" class="logo-externa"><div class="info-container">
                    <div class="info-txt">👤 <b>CLIENTE:</b> {str(r['nome']).upper()}</div>
                    <div class="info-txt">📅 <b>STATUS:</b> <span class="{status_cor}">{dias_txt}</span></div>
                    <div class="info-txt">🔑 <b>USER:</b> {r['usuario']}</div>
                    <div class="info-txt">📶 <b>SERVIDOR:</b> {r['servidor']}</div>
                </div></div>""", unsafe_allow_html=True)
            
            with st.expander("⚙️ EDITAR CLIENTE"):
                with st.form(key=f"edit_{r['id']}"):
                    servs = get_servidores()
                    if r['servidor'] not in servs: servs.append(r['servidor'])
                    
                    c1, c2 = st.columns(2)
                    en = c1.text_input("NOME", value=r['nome'])
                    ew = c2.text_input("WHATSAPP", value=r['whatsapp'])
                    eu = c1.text_input("USUÁRIO", value=r['usuario'])
                    es = c2.text_input("SENHA", value=r['senha'])
                    
                    try: dv = pd.to_datetime(r['vencimento']).date()
                    except: dv = datetime.now().date()
                    
                    ev = c1.date_input("VENCIMENTO", value=dv)
                    esrv = c2.selectbox("SERVIDOR", servs, index=servs.index(r['servidor']))
                    esis = c1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if r['sistema']=="P2P" else 1)
                    ec = c2.number_input("CUSTO", value=limpar_numero(r['custo']))
                    evlr = c1.number_input("VALOR COBRADO", value=limpar_numero(r['mensalidade']))
                    elogo = st.file_uploader("TROCAR LOGO", type=['png','jpg','jpeg'], key=f"l_{r['id']}")
                    
                    b1, b2 = st.columns(2)
                    if b1.form_submit_button("💾 SALVAR"):
                        l_final = image_to_base64(elogo) if elogo else r['logo_blob']
                        v_final = datetime.combine(ev, time(12,0)).strftime('%Y-%m-%d %H:%M:%S')
                        conn_up = sqlite3.connect('supertv_gestao.db')
                        conn_up.execute("UPDATE clientes SET nome=?, whatsapp=?, usuario=?, senha=?, servidor=?, sistema=?, vencimento=?, custo=?, mensalidade=?, logo_blob=? WHERE id=?", 
                                     (en, ew, eu, es, esrv, esis, v_final, ec, evlr, l_final, r['id']))
                        conn_up.commit(); conn_up.close(); st.rerun()
                    if b2.form_submit_button("🗑️ EXCLUIR"):
                        conn_del = sqlite3.connect('supertv_gestao.db')
                        conn_del.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                        conn_del.commit(); conn_del.close(); st.rerun()

with tab2:
    st.subheader("🚀 Novo Cadastro")
    with st.form("add"):
        servidores_lista = get_servidores()
        c1, c2 = st.columns(2)
        n_nome = c1.text_input("CLIENTE")
        n_zap = c2.text_input("WHATSAPP")
        n_user = c1.text_input("USUÁRIO")
        n_senha = c2.text_input("SENHA")
        n_serv = c1.selectbox("SERVIDOR", servidores_lista)
        n_venc = c2.date_input("VENCIMENTO", value=datetime.now()+timedelta(days=30))
        n_custo = c1.number_input("CUSTO", value=10.0)
        n_valor = c2.number_input("VALOR COBRADO", value=35.0)
        n_logo = st.file_uploader("LOGOMARCA", type=['png','jpg','jpeg'])
        if st.form_submit_button("🚀 CADASTRAR"):
            l_b = image_to_base64(n_logo)
            vf = datetime.combine(n_venc, time(12,0)).strftime('%Y-%m-%d %H:%M:%S')
            conn_in = sqlite3.connect('supertv_gestao.db')
            conn_in.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, vencimento, custo, mensalidade, logo_blob) VALUES (?,?,?,?,?,?,?,?,?)", 
                         (n_nome, n_zap, n_user, n_senha, n_serv, vf, n_custo, n_valor, l_b))
            conn_in.commit(); conn_in.close(); st.rerun()

with tab3:
    st.subheader("🚨 Gestão de Cobrança Profissional")
    if not df.empty:
        hoje = datetime.now().date()
        def calc_status(venc_str):
            try:
                dv = pd.to_datetime(venc_str).date()
                dias = (dv - hoje).days
                if dias < 0: return "🔴 VENCIDO", -1, dias, "ficar sem sinal"
                if dias == 0: return "🟠 VENCE HOJE", 0, dias, "renovar hoje"
                if dias == 1: return "🟡 1 DIA (Forte)", 1, dias, "renovar"
                if dias == 2: return "🟡 2 DIAS (Claro)", 2, dias, "renovar"
                if dias == 3: return "🟢 3 DIAS", 3, dias, "renovar"
                if 4 <= dias <= 7: return "🔵 4-7 DIAS", 4, dias, "se organizar"
                return "🟡 DOURADO (8-31)", 5, dias, "manter em dia"
            except: return "⚪ ERRO", 6, 999, ""

        df_c = df.copy()
        res = df_c['vencimento'].apply(calc_status)
        df_c['SITUAÇÃO'] = res.apply(lambda x: x[0]); df_c['ORDEM'] = res.apply(lambda x: x[1])
        df_c['DIAS'] = res.apply(lambda x: x[2]); df_c['MOTIVO'] = res.apply(lambda x: x[3])
        df_c = df_c.sort_values(by=['ORDEM', 'DIAS'])

        opcoes_status = df_c['SITUAÇÃO'].unique()
        filtro = st.multiselect("Filtrar por urgência:", options=opcoes_status, default=opcoes_status)
        df_filtrado = df_c[df_c['SITUAÇÃO'].isin(filtro)].copy()

        if 'sel_ids' not in st.session_state: st.session_state.sel_ids = []
        
        c_b1, c_b2, _ = st.columns([1, 1, 3])
        if c_b1.button("✅ Selecionar Todos"):
            st.session_state.sel_ids = df_filtrado['id'].tolist(); st.rerun()
        if c_b2.button("⬜ Limpar"):
            st.session_state.sel_ids = []; st.rerun()

        df_tab = df_filtrado.copy()
        df_tab.insert(0, "SELECIONAR", df_tab['id'].apply(lambda x: x in st.session_state.sel_ids))
        
        edit_c = st.data_editor(
            df_tab[['SELECIONAR', 'id', 'SITUAÇÃO', 'nome', 'servidor', 'vencimento']], 
            hide_index=True, use_container_width=True,
            column_config={
                "SELECIONAR": st.column_config.CheckboxColumn("✔"),
                "id": None, 
                "SITUAÇÃO": st.column_config.TextColumn("Status", width="small"),
            },
            disabled=["SITUAÇÃO", "nome", "servidor", "vencimento"], key="editor_v5"
        )

        ids_finais = edit_c[edit_c["SELECIONAR"] == True]["id"].tolist()
        st.divider()

        col_envio, col_gestao = st.columns([2, 1])
        with col_envio:
            st.markdown(f"### 💬 Envio ({len(ids_finais)})")
            template = st.text_area("Mensagem:", value="Olá {nome}! 👋\n\nLembramos que seu acesso no {servidor} está: {status}.\n\nVamos {motivo} para garantir o melhor sinal? 🚀")
            if st.button("🔗 GERAR LINKS"):
                if ids_finais:
                    for _, cli in df_c[df_c['id'].isin(ids_finais)].iterrows():
                        msg = template.format(nome=str(cli['nome']).split()[0].capitalize(), servidor=cli['servidor'], status=cli['SITUAÇÃO'], motivo=cli['MOTIVO'])
                        st.info(f"**{cli['SITUAÇÃO']}** | {cli['nome']} \n\n [ENVIAR WHATSAPP](https://wa.me/{cli['whatsapp']}?text={urllib.parse.quote(msg)})")
                else: st.warning("Selecione alguém na tabela.")

        with col_gestao:
            st.markdown("### 🛠️ Ação")
            if st.button("🗑️ EXCLUIR MARCADOS", type="secondary", use_container_width=True):
                if ids_finais:
                    c_db = sqlite3.connect('supertv_gestao.db')
                    c_db.execute(f"DELETE FROM clientes WHERE id IN ({','.join(['?']*len(ids_finais))})", ids_finais)
                    c_db.commit(); c_db.close(); st.session_state.sel_ids = []; st.rerun()
                else: st.error("Nenhum cliente marcado.")
    else: st.info("Sem dados.")

with tab4:
    st.subheader("⚙️ AJUSTES")
    st.markdown("### 📶 Servidores")
    with st.form("f_serv", clear_on_submit=True):
        col1, col2 = st.columns([3,1])
        novo = col1.text_input("Nome")
        if col2.form_submit_button("➕ ADD"):
            if adicionar_servidor(novo): st.success("OK!"); t_lib.sleep(0.5); st.rerun()
    
    lista = get_servidores()
    if lista:
        excl = st.selectbox("Remover:", ["Selecione..."] + lista)
        if excl != "Selecione..." and st.button("🗑️ Remover"):
            excluir_servidor(excl); st.rerun()

    st.divider()
    if not df.empty:
        st.markdown("### 📤 Backup")
        out = io.BytesIO()
        df.drop(columns=['logo_blob', 'dt_venc_calc', 'dias_res'], errors='ignore').to_excel(out, index=False, engine='xlsxwriter')
        st.download_button("📥 BAIXAR EXCEL (RECOMENDADO)", data=out.getvalue(), file_name="backup_supertv.xlsx")

    st.divider()
    st.markdown("### 📥 Importar Planilha")
    f_up = st.file_uploader("Arquivo .xlsx", type=["xlsx"])
    if f_up and st.button("🚀 PROCESSAR IMPORTAÇÃO"):
        try:
            df_imp = pd.read_excel(f_up)
            df_imp.columns = [str(c).strip().upper() for c in df_imp.columns]
            map_cols = {'nome': 'CLIENTE', 'usuario': 'USUÁRIO', 'senha': 'SENHA', 'servidor': 'SERVIDOR', 'vencimento': 'VENCIMENTO', 'whatsapp': 'WHATSAPP', 'custo': 'CUSTO', 'mensalidade': 'VALOR COBRADO'}
            df_final = pd.DataFrame()
            for db, ex in map_cols.items():
                if ex in df_imp.columns:
                    df_final[db] = df_imp[ex].apply(limpar_numero) if db in ['custo', 'mensalidade'] else df_imp[ex]
                else: df_final[db] = 0.0 if db in ['custo', 'mensalidade'] else ""
            df_final['vencimento'] = pd.to_datetime(df_final['vencimento'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
            conn_i = sqlite3.connect('supertv_gestao.db'); df_final.to_sql('clientes', conn_i, if_exists='append', index=False); conn_i.close()
            st.success("Importado com sucesso!"); t_lib.sleep(1); st.rerun()
        except Exception as e: st.error(f"Erro na importação: {e}")

    st.divider()
    st.markdown("### 🚨 ZONA DE PERIGO")
    confirmar = st.checkbox("Eu desejo apagar TODOS os dados permanentemente.")
    if confirmar:
        if st.button("🗑️ RESETAR BANCO DE DADOS", type="primary"):
            c_db = sqlite3.connect('supertv_gestao.db')
            c_db.execute("DELETE FROM clientes")
            c_db.commit()
            c_db.close()
            st.rerun()
