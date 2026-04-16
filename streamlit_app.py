import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta, time
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

    div.stFormSubmitButton > button {
        background: linear-gradient(135deg, #0052D4 0%, #929ED1 50%, #E0EAFC 100%) !important;
        color: #1e1e1e !important; font-weight: 900 !important; border-radius: 10px !important;
        width: 100%; height: 50px;
    }
    
    .stExpander > details > summary { 
        background: linear-gradient(135deg, #ff0000 0%, #c0c0c0 100%) !important; 
        color: #ffffff !important; padding: 15px !important; border-radius: 10px !important; 
        font-weight: 800 !important; font-size: 18px !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BANCO DE DADOS (SUPORTE A DATA E HORA) ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento TEXT, custo REAL, mensalidade REAL, 
                  inicio TEXT, observacao TEXT)''')
    conn.commit()
    conn.close()

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    try:
        lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    except: lista = []
    conn.close()
    return lista if lista else ["UNITV", "UNIPLAY", "P2BRAZ", "MUNDOGF", "PLAY TV"]

init_db()

# --- 4. CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- 5. HEADER ---
st.markdown("""<div class="header-container"><img src="https://i.imgur.com/CKq9BVx.png" class="logo-gestao"><img src="https://i.imgur.com/OkUAPQa.png" class="logo-supertv"></div>""", unsafe_allow_html=True)

# --- 6. ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👤 CLIENTES", "➕ ADD CLIENTE", "🚨 COBRANÇA", "⚙️ AJUSTES"])

with tab1:
    busca = st.text_input("🔍 PESQUISAR")
    if not df.empty:
        for _, r in df.sort_values(by='nome').iterrows():
            if busca.lower() in r['nome'].lower() or busca.lower() in str(r['usuario']).lower():
                # Formata a exibição da data/hora para o usuário (Dia/Mês/Ano Hora:Min)
                try:
                    dt_venc = datetime.strptime(r['vencimento'], '%Y-%m-%d %H:%M:%S')
                    venc_formatado = dt_venc.strftime('%d/%m/%Y %H:%M')
                except:
                    venc_formatado = r['vencimento']

                with st.expander(f"👤 {r['nome'].upper()} | VENCE: {venc_formatado}"):
                    with st.form(key=f"ed_{r['id']}"):
                        en = st.text_input("CLIENTE", value=r['nome'])
                        eu = st.text_input("USUÁRIO", value=r['usuario'])
                        es = st.text_input("SENHA", value=r['senha'])
                        esrv = st.selectbox("SERVIDOR", get_servidores())
                        esis = st.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if r['sistema']=="P2P" else 1)
                        
                        # EDIÇÃO DE DATA E HORA DE VENCIMENTO
                        st.write("**VENCIMENTO (DATA E HORA)**")
                        col_v1, col_v2 = st.columns(2)
                        ev_d = col_v1.date_input("DATA", value=dt_venc.date(), key=f"d_{r['id']}", format="DD/MM/YYYY")
                        ev_t = col_v2.time_input("HORÁRIO", value=dt_venc.time(), key=f"t_{r['id']}")
                        venc_final = datetime.combine(ev_d, ev_t)

                        ec = st.number_input("CUSTO", value=float(r['custo'] or 0.0))
                        em = st.number_input("VALOR COBRADO", value=float(r['mensalidade'] or 0.0))
                        
                        # EDIÇÃO DE DATA E HORA DE INÍCIO
                        st.write("**INICIOU DIA (DATA E HORA)**")
                        try:
                            dt_ini = datetime.strptime(r['inicio'], '%Y-%m-%d %H:%M:%S')
                        except:
                            dt_ini = datetime.now()
                        col_i1, col_i2 = st.columns(2)
                        ei_d = col_i1.date_input("DATA INÍCIO", value=dt_ini.date(), key=f"id_{r['id']}", format="DD/MM/YYYY")
                        ei_t = col_i2.time_input("HORÁRIO INÍCIO", value=dt_ini.time(), key=f"it_{r['id']}")
                        ini_final = datetime.combine(ei_d, ei_t)

                        ew = st.text_input("WHATSAPP", value=r['whatsapp'])
                        eobs = st.text_area("OBSERVAÇÃO", value=r['observacao'] or "")
                        
                        if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                            c = sqlite3.connect('supertv_gestao.db')
                            c.execute("""UPDATE clientes SET nome=?, usuario=?, senha=?, servidor=?, sistema=?, 
                                      vencimento=?, custo=?, mensalidade=?, inicio=?, whatsapp=?, observacao=? WHERE id=?""", 
                                     (en, eu, es, esrv, esis, venc_final.strftime('%Y-%m-%d %H:%M:%S'), ec, em, ini_final.strftime('%Y-%m-%d %H:%M:%S'), ew, eobs, r['id']))
                            c.commit(); st.rerun()

with tab2:
    st.subheader("🚀 Cadastro de Novo Assinante")
    with st.form("form_novo", clear_on_submit=True):
        n_cliente = st.text_input("CLIENTE")
        n_usuario = st.text_input("USUÁRIO")
        n_senha = st.text_input("SENHA")
        n_servidor = st.selectbox("SERVIDOR", get_servidores())
        n_sistema = st.selectbox("SISTEMA", ["P2P", "IPTV"])
        
        st.write("---")
        st.write("**DATA E HORA DE VENCIMENTO**")
        col1, col2 = st.columns(2)
        n_venc_data = col1.date_input("DIA VENCIMENTO", value=datetime.now() + timedelta(days=30), format="DD/MM/YYYY")
        n_venc_hora = col2.time_input("HORA VENCIMENTO", value=time(12, 0)) # Padrão meio-dia
        
        n_custo = st.number_input("CUSTO", value=10.0)
        n_valor = st.number_input("VALOR COBRADO", value=35.0)
        
        st.write("---")
        st.write("**DATA E HORA DE INÍCIO**")
        col3, col4 = st.columns(2)
        n_ini_data = col3.date_input("DIA INÍCIO", value=datetime.now().date(), format="DD/MM/YYYY")
        n_ini_hora = col4.time_input("HORA INÍCIO", value=datetime.now().time())
        
        n_whatsapp = st.text_input("WHATSAPP")
        n_obs = st.text_area("OBSERVAÇÃO")
        
        if st.form_submit_button("🚀 CADASTRAR AGORA"):
            if n_cliente and n_usuario:
                # Combina data e hora antes de salvar
                venc_completo = datetime.combine(n_venc_data, n_venc_hora).strftime('%Y-%m-%d %H:%M:%S')
                ini_completo = datetime.combine(n_ini_data, n_ini_hora).strftime('%Y-%m-%d %H:%M:%S')
                
                conn = sqlite3.connect('supertv_gestao.db')
                conn.execute("""INSERT INTO clientes 
                    (nome, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, inicio, whatsapp, observacao) 
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""", 
                    (n_cliente, n_usuario, n_senha, n_servidor, n_sistema, venc_completo, n_custo, n_valor, ini_completo, n_whatsapp, n_obs))
                conn.commit(); conn.close()
                st.success("Cliente cadastrado com sucesso!")
                st.rerun()

with tab4:
    st.subheader("⚙️ AJUSTES")
    if st.button("🗑️ LIMPAR TODOS OS DADOS (CUIDADO)"):
        c = sqlite3.connect('supertv_gestao.db')
        c.execute("DELETE FROM clientes")
        c.commit(); st.rerun()
