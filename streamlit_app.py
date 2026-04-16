import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SUPERTv4k GESTÃO PRO", layout="wide")

# --- 2. ESTILIZAÇÃO CSS (PADRÃO ORIGINAL) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-bottom: 30px; }
    .logo-gestao { width: 450px; margin-bottom: -20px !important; }
    .logo-supertv { width: 380px; }
    
    .metric-card { 
        background-color: #161b22; padding: 15px; border-radius: 12px; 
        text-align: center; border: 1px solid #30363d; margin-bottom: 10px; 
    }
    .metric-label { font-size: 11px; font-weight: bold; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 22px; font-weight: bold; color: #ff0000; margin-top: 5px; }

    div.stFormSubmitButton > button[data-testid="baseButton-primaryFormSubmit"] {
        background: linear-gradient(135deg, #0052D4 0%, #929ED1 50%, #E0EAFC 100%) !important;
        color: #1e1e1e !important; font-weight: 900 !important; border-radius: 10px !important;
    }
    div.stFormSubmitButton > button[data-testid="baseButton-secondaryFormSubmit"] {
        background: linear-gradient(135deg, #FF0000 0%, #8B0000 100%) !important;
        color: white !important; font-weight: 900 !important; border-radius: 10px !important;
    }

    div.stButton > button:has(div[data-testid="stMarkdownContainer"] p:contains("ADICIONAR SERVIDOR")),
    div.stButton > button:contains("ADICIONAR SERVIDOR") {
        background: linear-gradient(135deg, #ff0000 0%, #c0c0c0 100%) !important;
        color: white !important; font-weight: 900 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.7) !important;
        border-radius: 10px !important;
    }

    .stExpander > details > summary { 
        background: linear-gradient(135deg, #ff0000 0%, #c0c0c0 100%) !important; 
        color: #ffffff !important; padding: 15px !important; border-radius: 10px !important; 
        font-weight: 800 !important; font-size: 18px !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BANCO DE DADOS E CARGA DA LISTA FORNECIDA ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento DATE, custo REAL, mensalidade REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    
    # LISTA COMPLETA DOS CLIENTES ENVIADOS
    clientes_para_inserir = [
        ('FATIMA8626', '', 'FATIMA8626', 'USUARIO udpdru SENHA fatct2', 'UNITV', 'P2P', '2026-04-18', 10.0, 35.0),
        ('Renatop3975', '', 'Renatop3975', 'SENHA 356743dgty', '', 'IPTV', '2026-06-26', 10.0, 35.0),
        ('Taiane1152', '', 'Taiane1152', 'SENHA 3585ukpo1', '', 'P2P', '2026-04-17', 10.0, 35.0),
        ('Carlos6065', '', 'Carlos6065', 'SENHA Adg5680', 'P2BRAZ', 'IPTV', '2026-04-21', 10.0, 35.0),
        ('Anarib7119', '', 'Anarib7119', 'SENHA 4938369', '', 'P2P', '2026-04-30', 10.0, 35.0),
        ('Zantonio1132 C1', '', 'Zantonio1132 C1', 'SENHA x5894148', '', 'IPTV', '2026-04-21', 10.0, 30.0),
        ('Thiago6555', '', 'Thiago6555', 'SENHA 658627390', '', 'P2P', '2026-04-25', 10.0, 30.0),
        ('Adriana3700', '', 'Adriana3700', 'USUARIO n5drrq SENHA dri700', 'UNITV', 'P2P', '2026-03-25', 10.0, 35.0),
        ('Ualas8896', '', 'Ualas8896', 'SENHA tszm1awg', '', 'P2P', '2026-04-25', 10.0, 35.0),
        ('Fernando Vt225', '', 'Fernando Vt225', 'SENHA 342543Azd', '', 'P2P', '2026-04-27', 10.0, 35.0),
        ('Edinho7131 C2', '', 'Edinho7131 C2', '2Edinho7131. SENHA 1462452', 'UNIPLAY', 'P2P', '2026-05-10', 10.0, 30.0),
        ('Vitor1267579', '', 'Vitor1267579', 'SENHA 1267579', '', 'IPTV', '2026-04-16', 10.0, 35.0),
        ('Fatima5071', '', 'Fatima5071', 'SENHA 450428628', 'PLAY TV', 'IPTV', '2026-04-22', 10.0, 35.0),
        ('Vitor9935', '', 'Vitor9935', 'SENHA 76045952', '', 'P2P', '2026-02-16', 10.0, 35.0),
        ('Lucas6839', '', 'Lucas6839', 'SENHA yvbnxhw1', '', 'P2P', '2026-04-07', 10.0, 35.0),
        ('Kelly8158', '', 'Kelly8158', 'SENHA 68346955', 'MUNDO GF', 'P2P', '2026-04-20', 10.0, 35.0),
        ('Maykon6920', '', 'Maykon6920', 'SENHA 86867041', '', 'IPTV', '2026-04-23', 10.0, 35.0),
        ('Irineu7533', '', 'Irineu7533', 'SENHA 26874569', '', 'IPTV', '2026-05-06', 10.0, 35.0),
        ('Bianca 3051', '', 'Bianca 3051', 'SENHA 81990017', '', 'IPTV', '2026-05-01', 10.0, 35.0),
        ('Louise3414', '', 'Louise3414', 'SENHA 70968211', '', 'P2P', '2026-04-12', 10.0, 35.0),
        ('Tabatha0694', '', 'Tabatha0694', 'SENHA 85344375', '', 'P2P', '2026-04-20', 10.0, 35.0),
        ('Tatiane2302', '', 'Tatiane2302', 'SENHA 67045390', '', 'P2P', '2026-04-27', 10.0, 35.0),
        ('Erivelton6236', '', 'Erivelton6236', 'SENHA 98808928', '', 'IPTV', '2026-05-01', 10.0, 35.0),
        ('Sandro5162', '', 'Sandro5162', 'SENHA 8602895', '', 'P2P', '2026-05-05', 10.0, 35.0),
        ('Andreh7760 C1', '', 'Andreh7760 C1', 'SENHA 3352aerw', '', 'IPTV', '2026-05-02', 10.0, 10.0),
        ('Tati7269 C Sandra5430', '', 'Tati7269 C Sandra5430', 'Sandra 5430 SENHA 50087556', '', 'P2P', '2026-04-06', 10.0, 30.0),
        ('Jvitor9873', '', 'Jvitor9873', 'SENHA 62690933', '', 'IPTV', '2026-05-06', 10.0, 35.0),
        ('Angela1214', '', 'Angela1214', 'SENHA 3193260', '', 'P2P', '2026-05-04', 10.0, 35.0),
        ('Tati7269 C1', '', 'Tati7269 C1', 'SENHA 374895unp', '', 'P2P', '2026-04-06', 10.0, 30.0),
        ('Fabiana8459', '', 'Fabiana8459', '640473818 SENHA 992192288', '', 'IPTV', '2026-05-08', 10.0, 35.0),
        ('Alberto4357', '', 'Alberto4357', 'SENHA 31565267', '', 'P2P', '2026-05-08', 10.0, 35.0),
        ('Karinam9461', '', 'Karinam9461', '2Karinam9461 SENHA 3975989', '', 'P2P', '2026-05-04', 10.0, 35.0),
        ('Ricardo4002', '', 'Ricardo4002', 'SENHA Conta2ricardo', '', 'P2P', '2026-04-21', 10.0, 35.0),
        ('Gabriel3195', '', 'Gabriel3195', 'SENHA 64501260', '', 'IPTV', '2026-03-10', 10.0, 35.0),
        ('Eliana4270', '', 'Eliana4270', 'SENHA Dsa3467', '', 'P2P', '2026-05-10', 10.0, 35.0),
        ('Jeferson6137', '', 'Jeferson6137', '1616137 SENHA y334u5705T', '', 'IPTV', '2026-04-16', 10.0, 35.0),
        ('Antonio7651', '', 'Antonio7651', 'SENHA 945422919', '', 'IPTV', '2026-04-09', 10.0, 35.0),
        ('Valdinei9917 Bar', '', 'Valdinei9917 Bar', 'SENHA 951940211', '', 'IPTV', '2026-03-03', 10.0, 35.0),
        ('Zeroberto9835', '', 'Zeroberto9835', 'ynkqy6 SENHA zr9835', '', 'P2P', '2026-05-07', 10.0, 35.0),
        ('Ederp4178 2 Telas', '', 'Ederp4178 2 Telas', '534018373. SENHA 329194184', '', 'IPTV', '2026-05-05', 10.0, 20.0),
        ('Robson326209', '', 'Robson326209', 'SENHA 326209', '', 'IPTV', '2026-04-16', 10.0, 30.0),
        ('Alexandre3922', '', 'Alexandre3922', 'SENHA Xdr3575', '', 'P2P', '2026-02-12', 10.0, 35.0),
        ('Ronaldo3117', '', 'Ronaldo3117', 'SENHA 435472754', '', 'IPTV', '2026-03-10', 10.0, 35.0),
        ('Dr Marco Marina', '', 'Dr Marco Marina', 'Marina500102 SENHA 21792778', '', 'IPTV', '2026-04-12', 10.0, 30.0),
        ('Samuel5968', '', 'Samuel5968', 'SENHA anap1929', '', 'P2P', '2026-04-02', 10.0, 35.0),
        ('Dr Marco. Marquinho', '', 'Dr Marco. Marquinho', 'Marquinho9488 SENHA 32739008', '', 'IPTV', '2026-04-16', 10.0, 30.0),
        ('JoseD641115', '', 'JoseD641115', 'SENHA 804378944', '', 'IPTV', '2026-04-16', 10.0, 35.0),
        ('JoseC847776', '', 'JoseC847776', 'SENHA 7464577sup', '', 'IPTV', '2026-04-16', 10.0, 35.0),
        ('Giane6673', '', 'Giane6673', 'SENHA 26331390', '', 'P2P', '2026-04-12', 10.0, 30.0),
        ('Talison709508', '', 'Talison709508', 'SENHA 897091373', '', 'IPTV', '2026-03-06', 10.0, 35.0)
    ]
    
    # Inserção inteligente: Apenas insere se o usuário ainda não existir no banco
    for cli in clientes_para_inserir:
        c.execute("SELECT 1 FROM clientes WHERE usuario = ?", (cli[2],))
        if not c.fetchone():
            c.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, sistema, vencimento, custo, mensalidade) VALUES (?,?,?,?,?,?,?,?,?)", cli)
        
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

# Inicializar banco e carregar dados
init_db()

# --- 4. CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

if 'selecionados' not in st.session_state: st.session_state.selecionados = []

# --- 5. HEADER ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

# --- 6. MÉTRICAS ---
if not df.empty:
    hoje = datetime.now().date()
    df['venc_dt'] = pd.to_datetime(df['vencimento']).dt.date
    df['dias_res'] = (df['venc_dt'] - hoje).apply(lambda x: x.days)
    bruto, custos = df['mensalidade'].sum(), df['custo'].sum()
    liquido = bruto - custos
    c1, c2, c3 = st.columns(3); c4, c5, c6 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL CLIENTES</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value">{len(df[df["dias_res"] < 0])}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">VENCEM EM 3 DIAS</div><div class="metric-value">{len(df[(df["dias_res"] >= 0) & (df["dias_res"] <= 3)])}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO BRUTO</div><div class="metric-value">R$ {bruto:,.2f}</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO LÍQUIDO</div><div class="metric-value">R$ {liquido:,.2f}</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="metric-card"><div class="metric-label">CUSTO CRÉDITOS</div><div class="metric-value">R$ {custos:,.2f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 7. ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADD CLIENTE", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔍 PESQUISAR")
    if not df.empty:
        # Ordenar por nome para facilitar
        df_sorted = df.sort_values(by='nome')
        for _, r in df_sorted.iterrows():
            if busca.lower() in r['nome'].lower() or busca.lower() in str(r['usuario']).lower():
                # Cor do status no expander
                status_color = "🔴" if r['dias_res'] < 0 else "🟢"
                with st.expander(f"{status_color} {r['nome'].upper()} / {r['usuario']}"):
                    with st.form(key=f"ed_{r['id']}"):
                        col1, col2 = st.columns(2)
                        en, ew = col1.text_input("NOME", value=r['nome']), col2.text_input("WHATSAPP", value=r['whatsapp'])
                        eu, es = col1.text_input("USUÁRIO", value=r['usuario']), col2.text_input("SENHA", value=r['senha'])
                        srvs = get_servidores()
                        esrv = st.selectbox("SERVIDOR", srvs, index=srvs.index(r['servidor']) if r['servidor'] in srvs else 0)
                        col3, col4 = st.columns(2)
                        ev, em = col3.date_input("VENCIMENTO", value=pd.to_datetime(r['vencimento']).date()), col4.number_input("Valor", value=float(r['mensalidade']))
                        st.write("---")
                        b_col1, b_col2 = st.columns(2)
                        if b_col1.form_submit_button("💾 SALVAR"):
                            c = sqlite3.connect('supertv_gestao.db'); c.execute("UPDATE clientes SET nome=?, whatsapp=?, usuario=?, senha=?, servidor=?, vencimento=?, mensalidade=? WHERE id=?", (en, ew, eu, es, esrv, str(ev), em, r['id'])); c.commit(); st.rerun()
                        if b_col2.form_submit_button("🗑️ EXCLUIR"):
                            c = sqlite3.connect('supertv_gestao.db'); c.execute("DELETE FROM clientes WHERE id=?", (r['id'],)); c.commit(); st.rerun()

with tab2:
    st.subheader("🚀 Cadastro")
    with st.form("form_novo", clear_on_submit=True):
        f1, f2 = st.columns(2)
        n_n, w_n = f1.text_input("NOME"), f2.text_input("WHATSAPP")
        u_n, s_n = f1.text_input("USUÁRIO"), f2.text_input("SENHA")
        srv_n = st.selectbox("SERVIDOR", get_servidores())
        v_n = st.date_input("VENCIMENTO", value=datetime.now() + timedelta(days=30))
        f3, f4 = st.columns(2)
        c_n, m_n = f3.number_input("CUSTO", 10.0), f4.number_input("VALOR", 35.0)
        if st.form_submit_button("🚀 CADASTRAR"):
            if n_n and u_n:
                conn = sqlite3.connect('supertv_gestao.db'); conn.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, vencimento, custo, mensalidade) VALUES (?,?,?,?,?,?,?,?)", (n_n, w_n, u_n, s_n, srv_n, str(v_n), c_n, m_n)); conn.commit(); conn.close(); st.rerun()

with tab3:
    st.subheader("🚨 COBRANÇA")
    pix_chave = "62.326.879/0001-13"
    if not df.empty:
        df_aviso = df[df['dias_res'] <= 3].copy()
        c_s, c_l = st.columns(2)
        if c_s.button("✅ SELECIONAR TODOS"): st.session_state.selecionados = df_aviso['id'].tolist(); st.rerun()
        if c_l.button("❌ LIMPAR SELEÇÃO"): st.session_state.selecionados = []; st.rerun()
        for _, cl in df_aviso.iterrows():
            dias = cl['dias_res']
            status = "VENCE HOJE" if dias == 0 else (f"VENCE EM {dias} DIAS" if dias > 0 else f"VENCIDO HÁ {abs(dias)} DIAS")
            check = st.checkbox(f"🔔 {cl['nome']} | {status}", value=(cl['id'] in st.session_state.selecionados), key=f"cob_{cl['id']}")
            if check and cl['id'] not in st.session_state.selecionados: st.session_state.selecionados.append(cl['id'])
            elif not check and cl['id'] in st.session_state.selecionados: st.session_state.selecionados.remove(cl['id'])
        if st.session_state.selecionados:
            st.divider()
            for sid in st.session_state.selecionados:
                cli = df[df['id'] == sid].iloc[0]
                msg = f"Olá {cli['nome']}! Sua assinatura Supertv4k vence em {pd.to_datetime(cli['vencimento']).strftime('%d/%m/%Y')}. Renove via Pix: {pix_chave}"
                st.link_button(f"ENVIAR PARA {cli['nome']}", f"https://wa.me/{cli['whatsapp']}?text={urllib.parse.quote(msg)}")

with tab4:
    st.subheader("⚙️ AJUSTES")
    ns = st.text_input("NOVO SERVIDOR")
    if st.button("ADICIONAR SERVIDOR"):
        if ns:
            c = sqlite3.connect('supertv_gestao.db'); c.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (ns,)); c.commit(); st.rerun()
    st.divider()
    col_up, col_down = st.columns(2)
    with col_up:
        st.write("📥 **IMPORTAR**")
        f_up = st.file_uploader("Arquivo .xlsx", type=["xlsx"])
        if f_up and st.button("PROCESSAR"):
            pd.read_excel(f_up).to_sql('clientes', sqlite3.connect('supertv_gestao.db'), if_exists='append', index=False); st.rerun()
    with col_down:
        st.write("📤 **BACKUP**")
        if not df.empty:
            tow = io.BytesIO(); df.to_excel(tow, index=False)
            st.download_button(label="📥 DOWNLOAD EXCEL", data=tow.getvalue(), file_name="backup_supertv4k.xlsx")
