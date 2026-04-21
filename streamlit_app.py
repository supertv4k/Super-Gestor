
import streamlit as st
import pandas as pd
import sqlite3
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

# --- 3. BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, usuario TEXT, senha TEXT, 
                  servidor TEXT, sistema TEXT, vencimento TEXT, custo REAL, 
                  mensalidade REAL, inicio TEXT, whatsapp TEXT, observacao TEXT, logo_blob TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    conn.commit()
    conn.close()

def get_servidores():
    lista_fixa = [
        "UNIPLAY", "MUNDO GF", "P2BRAZ", "UNITV", "PLAYTV", 
        "P2CINE", "P2SPEED", "BLADE", "MEGATV", 
        "BOB PLAYER", "IBO PLAYER", "IBO PRO PLAYER"
    ]
    conn = sqlite3.connect('supertv_gestao.db')
    extras = pd.read_sql_query("SELECT nome FROM lista_servidores", conn)['nome'].tolist()
    conn.close()
    extras_filtrados = sorted([e for e in extras if e not in lista_fixa])
    return lista_fixa + extras_filtrados

def format_data_br(data_str):
    try: return datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except: return data_str

init_db()

# --- 4. LÓGICA DE ESTADO ---
if 'cliente_selecionado' not in st.session_state:
    st.session_state.cliente_selecionado = None

# --- 5. INTERFACE ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

if not df.empty:
    hoje = datetime.now().date()
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    df['dias_res'] = df['dt_venc_calc'].apply(lambda x: (x - hoje).days if pd.notnull(x) else 999)
    
    df_ativos = df[df['dias_res'] >= 0]
    lucro_total = (df_ativos['mensalidade'].sum()) - (df_ativos['custo'].sum())

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
            
            lista_sistemas = ["P2P", "IPTV"]
            idx_sis = lista_sistemas.index(c_sel['sistema']) if c_sel['sistema'] in lista_sistemas else 0
            new_sistema = col2.selectbox("Sistema", lista_sistemas, index=idx_sis)
            
            v_data = datetime.strptime(c_sel['vencimento'], '%Y-%m-%d') if isinstance(c_sel['vencimento'], str) else c_sel['vencimento']
            new_venc = col3.date_input("Vencimento", value=v_data, format="DD/MM/YYYY")
            
            new_whats = col1.text_input("WhatsApp", value=c_sel['whatsapp'])
            new_custo = col2.number_input("Custo", value=float(c_sel['custo']))
            new_mensal = col3.number_input("Valor Cobrado", value=float(c_sel['mensalidade']))
            new_obs = st.text_area("Observação", value=str(c_sel['observacao']))
            
            # --- NOVO: CAMPO DE UPLOAD NA EDIÇÃO ---
            st.write("🖼️ **Trocar Logo do Servidor**")
            new_img = st.file_uploader("Selecione uma nova imagem para atualizar", type=['png', 'jpg'], key="edit_img")

            b_salvar, b_renovar, b_excluir, b_cancelar = st.columns(4)
            
            if b_salvar.button("💾 SALVAR ALTERAÇÕES", use_container_width=True):
                w_limpo = ''.join(filter(str.isdigit, str(new_whats)))
                # Lógica para manter imagem antiga ou salvar a nova
                l_b = base64.b64encode(new_img.read()).decode() if new_img else c_sel['logo_blob']
                
                conn = sqlite3.connect('supertv_gestao.db')
                conn.execute("""UPDATE clientes SET 
                             nome=?, usuario=?, senha=?, servidor=?, sistema=?, 
                             vencimento=?, custo=?, mensalidade=?, whatsapp=?, 
                             observacao=?, logo_blob=? WHERE id=?""",
                             (new_nome, new_user, new_senha, new_serv, new_sistema, 
                              new_venc.strftime('%Y-%m-%d'), new_custo, new_mensal, 
                              w_limpo, new_obs, l_b, c_sel['id']))
                conn.commit(); conn.close()
                st.session_state.cliente_selecionado = None
                st.success("Dados atualizados com sucesso!")
                st.rerun()

            if b_renovar.button("➕ RENOVAR (+30d)", use_container_width=True):
                v_at = datetime.strptime(c_sel['vencimento'], '%Y-%m-%d') if isinstance(c_sel['vencimento'], str) else c_sel['vencimento']
                n_data = (v_at + timedelta(days=30)).strftime('%Y-%m-%d')
                conn = sqlite3.connect('supertv_gestao.db')
                conn.execute("UPDATE clientes SET vencimento=? WHERE id=?", (n_data, c_sel['id']))
                conn.commit(); conn.close()
                st.session_state.cliente_selecionado = None
                st.rerun()

            if b_excluir.button("🗑️ EXCLUIR", type="primary", use_container_width=True):
                conn = sqlite3.connect('supertv_gestao.db')
                conn.execute("DELETE FROM clientes WHERE id=?", (c_sel['id'],))
                conn.commit(); conn.close()
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
            tipo_sis = f" | ⚡ {r['sistema']}" if r['sistema'] else ""
            if c2.button(f"{prefixo}{str(r['nome']).upper()} | 🔑 {r['usuario']}{tipo_sis} | 📅 {format_data_br(r['vencimento'])}", key=f"b_{r['id']}"):
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
        n_venc = f3.date_input("Vencimento", value=datetime.now() + timedelta(days=30), format="DD/MM/YYYY")
        n_whats = f1.text_input("WhatsApp (DDD+Número)")
        n_custo = f2.number_input("Custo", value=10.0)
        n_valor = f3.number_input("Valor Cobrado", value=35.0)
        n_img = st.file_uploader("Logo", type=['png', 'jpg'])
        
        if st.form_submit_button("🚀 CADASTRAR CLIENTE"):
            w_ok = ''.join(filter(str.isdigit, n_whats))
            l_b = base64.b64encode(n_img.read()).decode() if n_img else None
            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("INSERT INTO clientes (nome, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, whatsapp, logo_blob) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (n_nome, n_user, n_senha, n_serv, n_sistema, n_venc.strftime('%Y-%m-%d'), n_custo, n_valor, w_ok, l_b))
            conn.commit(); conn.close(); st.rerun()

with tab3:
    st.subheader("🚨 Central de Cobrança Automática")
    pix_cnpj = "62.326.879/0001-13"
    
    st.write("Selecione o grupo para cobrar:")
    filtro_btn = st.radio("Filtro:", ["Todos", "Vencidos", "Vence Hoje", "Amanhã", "2 Dias", "3 Dias"], horizontal=True)

    if not df.empty:
        if filtro_btn == "Vencidos":
            df_cobranca = df[df['dias_res'] < 0]
        elif filtro_btn == "Vence Hoje":
            df_cobranca = df[df['dias_res'] == 0]
        elif filtro_btn == "Amanhã":
            df_cobranca = df[df['dias_res'] == 1]
        elif filtro_btn == "2 Dias":
            df_cobranca = df[df['dias_res'] == 2]
        elif filtro_btn == "3 Dias":
            df_cobranca = df[df['dias_res'] == 3]
        else:
            df_cobranca = df[df['dias_res'] <= 3]

        if df_cobranca.empty:
            st.info(f"Nenhum cliente no grupo: {filtro_btn}")
        else:
            for _, c in df_cobranca.sort_values(by='dias_res').iterrows():
                dias = c['dias_res']
                nome_cli = str(c['nome']).split()[0].upper()
                
                if dias < 0:
                    msg = f"🚨*{nome_cli}, SUA ASSINATURA DE TV VENCEU !*\n\nNÃO PREOCUPE, BASTA FAZER O PIX QUE REATIVAMOS PRA VOCÊ!\n\n💠*PIX CNPJ*\n{pix_cnpj}\n\n⚠️ *NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!*"
                    status_txt = "❌ VENCIDO"
                elif dias == 0:
                    msg = f"⚠️*{nome_cli}, SUA ASSINATURA DE TV VENCE HOJE ⏰ !*\n\nNÃO FIQUE SEM TV, BASTA FAZER O PIX QUE RENOVAMOS PRA VOCÊ +30 DIAS!\n\n💠*PIX CNPJ*\n{pix_cnpj}\n\n⚠️ *NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!*"
                    status_txt = "⏰ VENCE HOJE"
                elif dias == 1:
                    msg = f"⚠️*{nome_cli}, SUA ASSINATURA DE TV VENCE AMANHÃ ⏰ !*\n\nNÃO FIQUE SEM TV, FAÇA O PIX E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠*PIX CNPJ*\n{pix_cnpj}\n\n⚠️ *NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!*"
                    status_txt = "📅 VENCE AMANHÃ"
                elif dias == 2:
                    msg = f"⚠️*{nome_cli}, SUA ASSINATURA DE TV VENCE EM 2️⃣ DIAS ⏰ !*\n\nFAÇA O PIX AGORA E RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠*PIX CNPJ*\n{pix_cnpj}\n\n⚠️ *NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!*"
                    status_txt = "⏳ 2 DIAS"
                elif dias == 3:
                    msg = f"⚠️*{nome_cli}, SUA ASSINATURA DE TV VENCE EM 3️⃣ DIAS ⏰ !*\n\nFAÇA O PIX AGORA E FIQUE TRANQUILO RENOVAREMOS PRA VOCÊ +30 DIAS!\n\n💠*PIX CNPJ*\n{pix_cnpj}\n\n⚠️ *NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!*"
                    status_txt = "⏳ 3 DIAS"
                
                num = str(c['whatsapp'])
                if not num.startswith('55'): num = '55' + num
                st.link_button(f"📲 {status_txt} | {c['nome']}", f"https://wa.me/{num}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ Sistema")
    
    st.write("🖥️ **Gerenciar Servidores**")
    col_srv1, col_srv2 = st.columns([3, 1])
    novo_srv = col_srv1.text_input("Nome do novo servidor", placeholder="Ex: NOVO_SRV")
    if col_srv2.button("➕ Adicionar"):
        if novo_srv:
            try:
                conn = sqlite3.connect('supertv_gestao.db')
                conn.execute("INSERT INTO lista_servidores (nome) VALUES (?)", (novo_srv.upper().strip(),))
                conn.commit(); conn.close()
                st.success(f"Servidor {novo_srv} adicionado!")
                st.rerun()
            except:
                st.error("Servidor já existe!")
        else:
            st.warning("Digite um nome.")
    
    st.divider()

    st.write("📤 **Exportar Dados**")
    if st.button("📦 Gerar Backup Excel"):
        out = io.BytesIO()
        df_export = df.drop(columns=['dt_venc_calc', 'dias_res'], errors='ignore')
        df_export.to_excel(out, index=False)
        st.download_button("⬇️ Baixar Backup", out.getvalue(), "backup.xlsx")

    st.divider()

    st.write("📥 **Importar Dados**")
    arquivo_upload = st.file_uploader("Selecione o arquivo backup.xlsx para restaurar", type=['xlsx'])

    if arquivo_upload is not None:
        if st.button("🚀 Iniciar Importação"):
            try:
                df_importado = pd.read_excel(arquivo_upload)
                colunas_bd = ['nome', 'usuario', 'senha', 'servidor', 'sistema', 'vencimento', 'custo', 'mensalidade', 'whatsapp', 'observacao', 'logo_blob']
                for col in colunas_bd:
                    if col not in df_importado.columns: df_importado[col] = None

                conn = sqlite3.connect('supertv_gestao.db')
                sucesso, erros = 0, 0
                for _, row in df_importado.iterrows():
                    try:
                        check = conn.execute("SELECT id FROM clientes WHERE nome=? AND usuario=?", (row['nome'], row['usuario'])).fetchone()
                        if not check:
                            conn.execute("""INSERT INTO clientes (nome, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, whatsapp, observacao, logo_blob) 
                                            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                                         (row['nome'], row['usuario'], row['senha'], row['servidor'], row['sistema'], str(row['vencimento']).split()[0], 
                                          row['custo'], row['mensalidade'], row['whatsapp'], row['observacao'], row['logo_blob']))
                            sucesso += 1
                        else: erros += 1
                    except: erros += 1
                conn.commit(); conn.close()
                st.success(f"✅ Concluído! {sucesso} importados.")
                if erros > 0: st.warning(f"⚠️ {erros} já existiam ou deram erro.")
                st.rerun()
            except Exception as e: st.error(f"❌ Erro: {e}")
