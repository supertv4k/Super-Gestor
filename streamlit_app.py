import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="CLIENTES", layout="wide")

# Estilização Profissional
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { color: #00ff00; font-size: 20px; }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; }
    div[data-baseweb="radio"] > div { flex-direction: row !important; gap: 20px; }
    .stCheckbox { margin-bottom: -15px; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS E MIGRAÇÃO ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento DATE, custo REAL, mensalidade REAL, observacao TEXT, logo BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    
    # Garantir que todas as colunas existem
    colunas_necessarias = [
        ("SISTEMA", "TEXT DEFAULT 'IPTV'"), 
        ("OBSERVAÇÃO", "TEXT"), 
        ("LOGO", "BLOB"),
        ("CUSTO", "REAL DEFAULT 0.0"),
        ("MENSALIDADE", "REAL DEFAULT 0.0")
    ]
    for col, tipo in colunas_necessarias:
        try: 
            c.execute(f"ALTER TABLE clientes ADD COLUMN {col} {tipo}")
        except: 
            pass
            
    c.execute("SELECT COUNT(*) FROM lista_servidores")
    if c.fetchone()[0] == 0:
        servs = ["UNIPLAY", "MUNDOGF", "P2BRAZ", "PLAYTV", "P2CINE", "BLADETV", "SPEEDTV", "UNITV", "MEGATV", "BobPlayer", "IboPlayer", "IboPlayer pro"]
        for s in servs: c.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (s,))
    conn.commit()
    conn.close()

init_db()

# --- FUNÇÕES DE APOIO ---
def obter_regua(venc_data):
    hoje = datetime.now().date()
    pix = "62.326.879/0001-13"
    try:
        venc_data = datetime.strptime(str(venc_data), '%Y-%m-%d').date() if isinstance(venc_data, str) else venc_data
        dias = (venc_data - hoje).days
        if dias == 3:
            msg = f"Sua Assinatura Vence em 3️⃣ dias! Faça Agora o pagamento pelo PIX e Fique tranquilo !\n\nCopia e Cola no seu Banco!\n\n{pix}"
            return "Vence em 3 dias", msg, "🟨", dias
        elif dias == 2:
            msg = f"Sua Assinatura Vence em 2️⃣ dias! Faça Agora o pagamento pelo PIX e Fique tranquilo !\n\nCopia e Cola no seu Banco!\n\n{pix}"
            return "Vence em 2 dias", msg, "🟨", dias
        elif dias == 1:
            msg = f"Sua Assinatura Vence 1️⃣ Amanhã ! Faça Agora o pagamento pelo PIX e Fique tranquilo !\n\nCopia e Cola no seu Banco!\n\n{pix}"
            return "Vence Amanhã", msg, "🟧", dias
        elif dias == 0:
            msg = f"Sua Assinatura Vence Hoje⏰ ! Faça Agora o pagamento pelo PIX e Já Já Estará Renovado mais 30 Dias!\n\nCopia e Cola no seu Banco!\n\n{pix}"
            return "Vence HOJE", msg, "🟥", dias
        elif dias < 0:
            msg = f"Sua Assinatura Venceu 🚨! Não se Preocupe é só Fazer o Pagamento que Renovamos mais 30 Dias pra Você!\n\nCopia e Cola no seu Banco!\n\n{pix}"
            return "VENCIDO", msg, "🚨", dias
        return f"{dias} dias restantes", "", "🟩", dias
    except: return "ERRO", "", "❌", 0

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    conn.close()
    return lista

# --- INTERFACE ---
st.image("https://i.imgur.com/CKq9BVx.png", width=400)
st.image("https://imgur.com/gallery/frase-gest-o-de-clientes-em-png-ryIgzAf#OkUAPQa.png", width=200)

conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- CÁLCULOS DO DASHBOARD ---
if not df.empty:
    df['status_regua'] = df['vencimento'].apply(lambda x: obter_regua(x))
    total_clientes = len(df)
    em_dia = len(df[df['status_regua'].apply(lambda x: x[2] == "🟩")])
    vencidos = len(df[df['status_regua'].apply(lambda x: x[2] == "🚨")])
    vencendo_3_dias = len(df[df['status_regua'].apply(lambda x: x[3] >= 0 and x[3] <= 3)])
    
    faturamento_bruto = df['mensalidade'].sum()
    custos_totais = df['custo'].sum()
    faturamento_liquido = faturamento_bruto - custos_totais
else:
    total_clientes = em_dia = vencidos = vencendo_3_dias = faturamento_bruto = custos_totais = faturamento_liquido = 0

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["👤CLIENTES", "➕ADD CLIENTE", "🚨COBRANÇA", "📡➕ ADD SERV"])

with tab1:
    st.subheader("📊 LEVANTAMENTO")
    d1, d2 , d3 , d4 = st.columns(4)
    d1.metric("TOTAL DE CLIENTES", f"{total_clientes}")
    d2.metric("EM DIA", f"{em_dia}")
    d3.metric("VENCIDOS", f"{vencidos}")
    d4.metric("VENCE EM 3️⃣ DIAS", f"{vencendo_3_dias}")

    st.markdown("#### 📈 FINANCEIRO")
    f1, f2, f3 = st.columns(3)
    f1.metric("BRUTO", f"R$ {faturamento_bruto:,.2f}")
    f2.metric("LÍQUIDO", f"R$ {faturamento_liquido:,.2f}")
    f3.metric("CUSTOS", f"R$ {custos_totais:,.2f}")
    
    st.divider()
    
    busca = st.text_input("🔍 BUSCAR CLIENTE...")
    
    servs_at = get_servidores()
    if not df.empty:
        for _, r in df.iterrows():
            if busca.lower() in str(r['nome']).lower():
                status, _, icon, _ = obter_regua(r['vencimento'])
                edit_key = f"ed_{r['id']}"
                if edit_key not in st.session_state: st.session_state[edit_key] = False
                
                with st.expander(f"{icon} {r['nome']} | {r['sistema']} | {status}"):
                    if not st.session_state[edit_key]:
                        col1, col2, col3 = st.columns([1, 2, 2])
                        with col1:
                            if r['logo']: st.image(r['logo'], width=100)
                            else: st.write("🚫 SEM LOGO ")
                        with col2:
                            # Ajuste na descrição de Usuário e Senha conforme solicitado
                            st.write(f"**USUARIO:** `{r['usuario']}`")
                            st.write(f"**SENHA:** `{r['senha']}`")
                            st.write(f"**WHATSAPP:** {r['whatsapp']}")
                            st.write(f"**VENCIMENTO:** {r['vencimento']}")
                        with col3:
                            # Adição das informações financeiras no card
                            st.write(f"**SERVIDOR:** {r['servidor']}")
                            st.write(f"**MENSALIDADE:** R$ {r['mensalidade']:.2f}")
                            st.write(f"**CUSTO:** R$ {r['custo']:.2f}")
                            st.write(f"**OBS:** {r['observacao']}")
                        st.divider()
                        b1, b2, b3 = st.columns([1,1,2])
                        if b1.button("📝 EDITAR", key=f"be_{r['id']}"):
                            st.session_state[edit_key] = True; st.rerun()
                        if b2.button("🗑️ EXCLUIR", key=f"bd_{r['id']}"):
                            c = sqlite3.connect('supertv_gestao.db'); c.execute("DELETE FROM clientes WHERE id=?", (r['id'],)); c.commit(); st.rerun()
                        d_add = b3.number_input("Dias", value=30, step=1, key=f"n{r['id']}")
                        if b3.button(f"🔄 RENOVAR +{d_add} dias", key=f"br_{r['id']}"):
                            nova = (datetime.strptime(str(r['vencimento']), '%Y-%m-%d') + pd.Timedelta(days=d_add)).date()
                            c = sqlite3.connect('supertv_gestao.db'); c.execute("UPDATE clientes SET vencimento=? WHERE id=?", (str(nova), r['id'])); c.commit(); st.rerun()
                    else:
                        with st.form(f"fe_{r['id']}"):
                            up_l = st.file_uploader("Trocar Logo", type=['png', 'jpg'], key=f"ul_{r['id']}")
                            ed_n = st.text_input("Nome", value=r['nome'])
                            ce1, ce2 = st.columns(2); ed_u = ce1.text_input("USUARIO", value=r['usuario']); ed_p = ce2.text_input("SENHA", value=r['senha'])
                            ce3, ce4 = st.columns(2); ed_s = ce3.radio("SISTEMA", ["IPTV", "P2P"], index=0 if r['sistema']=="IPTV" else 1, horizontal=True); ed_srv = ce4.selectbox("Servidor", servs_at, index=servs_at.index(r['servidor']) if r['servidor'] in servs_at else 0)
                            
                            # Novos campos de edição
                            ce5, ce6 = st.columns(2)
                            ed_mens = ce5.number_input("MENSALIDADE (R$)", value=float(r['mensalidade']))
                            ed_custo = ce6.number_input("CUSTO (R$)", value=float(r['custo']))
                            
                            ed_v = st.date_input("VENCIMENTo", value=datetime.strptime(str(r['vencimento']), '%Y-%m-%d').date())
                            ed_o = st.text_area("OBSERVAÇÃO", value=r['observacao'])
                            
                            if st.form_submit_button("SALVAR"):
                                l_b = up_l.read() if up_l else r['logo']
                                c = sqlite3.connect('supertv_gestao.db')
                                c.execute("""UPDATE clientes SET 
                                            nome=?, usuario=?, senha=?, sistema=?, servidor=?, 
                                            vencimento=?, observacao=?, logo=?, mensalidade=?, custo=? 
                                            WHERE id=?""", 
                                         (ed_n, ed_u, ed_p, ed_s, ed_srv, str(ed_v), ed_o, l_b, ed_mens, ed_custo, r['id']))
                                c.commit()
                                st.session_state[edit_key] = False
                                st.rerun()

with tab2:
    with st.form("novo", clear_on_submit=True):
        st.subheader("➕NOVO CLIENTE")
        n_c = st.text_input("NOME")
        w_c = st.text_input("WHATSAPP (Ex: 5511999999999)")
        c1, c2 = st.columns(2); u_c = c1.text_input("USUÁRIO"); s_c = c2.text_input("SENHA")
        c3, c4 = st.columns(2); srv_c = c3.selectbox("SERVIDOR", get_servidores()); sis_c = c4.radio("SISTEMA", ["IPTV", "P2P"], horizontal=True)
        v_c = st.date_input("VENCIMENTO", value=datetime.now() + pd.Timedelta(days=30))
        c5, c6 = st.columns(2); cu_c = c5.number_input("CUSTO (R$)", value=0.0); me_c = c6.number_input("MENSALIDADE (R$)", value=35.0)
        o_c = st.text_area("OBSERVAÇÃO")
        l_c = st.file_uploader("LOGO DO SERVIDOR (Opcional)", type=['png', 'jpg'])
        
        if st.form_submit_button("🚀 CADASTRAR"):
            if n_c and w_c:
                lb = l_c.read() if l_c else None
                c = sqlite3.connect('supertv_gestao.db')
                c.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, observacao, logo) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (n_c, w_c, u_c, s_c, srv_c, sis_c, str(v_c), cu_c, me_c, o_c, lb))
                c.commit()
                st.success("CADASTRADO COM SUCESSO")
                st.rerun()
            else:
                st.error("PREENCHA NOME E WHATSAPP")

with tab3:
    st.subheader("📢 FILTRO DE COBRANÇA")
    if not df.empty:
        cobranca_list = [r for _, r in df.iterrows() if obter_regua(r['vencimento'])[2] != "🟩"]
        if cobranca_list:
            sel_todos = st.checkbox("MARCAR TODOS")
            selecionados = []
            for r in cobranca_list:
                status, msg, icon, _ = obter_regua(r['vencimento'])
                col_sel, col_inf = st.columns([0.5, 9.5])
                with col_sel:
                    if st.checkbox("", value=sel_todos, key=f"chk_{r['id']}"): selecionados.append(r)
                with col_inf: st.write(f"{icon} **{r['nome']}** | {status}")
            
            if selecionados:
                if st.button("🔗 GERAR LINKS"):
                    for s in selecionados:
                        _, msg_f, _, _ = obter_regua(s['vencimento'])
                        link = f"https://wa.me/{s['whatsapp']}?text={urllib.parse.quote(msg_f)}"
                        st.link_button(f"Enviar para: {s['nome']}", link)
        else: st.success("Nenhum cliente vencido ou próximo do vencimento!")

with tab4:
    c_fin, c_srv = st.columns(2)
    with c_fin:
        st.subheader("⚖️ Exportação")
        if not df.empty:
            buf = io.BytesIO()
            try:
                with pd.ExcelWriter(buf, engine='openpyxl') as wr: df.to_excel(wr, index=False)
                st.download_button("📥 BACKUP EXCEL", buf.getvalue(), "gestao.xlsx")
            except: st.warning("Instale 'openpyxl' para backup.")
    with c_srv:
        st.subheader("📡 SERVIDORES")
        ns = st.text_input("NOVO NOME")
        if st.button("ADD"):
            c = sqlite3.connect('supertv_gestao.db'); c.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (ns,)); c.commit(); st.rerun()
        rs = st.selectbox("Remover", get_servidores())
        if st.button("Remover"):
            c = sqlite3.connect('supertv_gestao.db'); c.execute("DELETE FROM lista_servidores WHERE nome=?", (rs,)); c.commit(); st.rerun()
