with tab1:
    st.subheader("🔍 Filtros Rápidos")
    
    # 1. LINHA DE BOTÕES DE FILTRO
    # Criamos colunas para os botões ficarem lado a lado
    c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
    
    # Inicializa o estado do filtro se não existir
    if 'filtro_atual' not in st.session_state:
        st.session_state.filtro_atual = "Todos"

    # Estilização específica para os botões de filtro
    if c_btn1.button("👥 Todos", use_container_width=True):
        st.session_state.filtro_atual = "Todos"
    if c_btn2.button("🔴 Vencidos", use_container_width=True):
        st.session_state.filtro_atual = "Vencidos"
    if c_btn3.button("🟡 A Vencer (3d)", use_container_width=True):
        st.session_state.filtro_atual = "A Vencer"
    if c_btn4.button("🟢 Ativos", use_container_width=True):
        st.session_state.filtro_atual = "Ativos"

    st.markdown(f"**Filtro Ativo:** `{st.session_state.filtro_atual}`")

    # 2. BARRA DE PESQUISA POR NOME/USER (Logo abaixo dos botões)
    busca = st.text_input("🔎 Pesquisar por Nome ou Usuário...", placeholder="Digite para filtrar a lista abaixo")

    if not df.empty:
        # --- LÓGICA DE FILTRAGEM ---
        df_f = df.copy()

        # Aplicar Filtro dos Botões
        if st.session_state.filtro_atual == "Vencidos":
            df_f = df_f[df_f['dias_res'] < 0]
        elif st.session_state.filtro_atual == "A Vencer":
            df_f = df_f[(df_f['dias_res'] >= 0) & (df_f['dias_res'] <= 3)]
        elif st.session_state.filtro_atual == "Ativos":
            df_f = df_f[df_f['dias_res'] >= 0]

        # Aplicar Busca por texto
        if busca:
            df_f = df_f[
                df_f['nome'].str.contains(busca, case=False, na=False) | 
                df_f['usuario'].str.contains(busca, case=False, na=False)
            ]

        st.write(f"📋 Exibindo {len(df_f)} registro(s)")

        # --- EXIBIÇÃO DA LISTA (O SEU DESIGN DE CARDS COM LOGO) ---
        for _, r in df_f.sort_values(by='dias_res').iterrows():
            dt_v = pd.to_datetime(r['vencimento'])
            status_cor = "destaque-verde" if r['dias_res'] >= 0 else "destaque-vermelho"
            dias_txt = f"{r['dias_res']} DIAS" if r['dias_res'] >= 0 else "VENCIDO"
            img_data = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"

            st.markdown(f"""
            <div class="cliente-row">
                <img src="{img_data}" class="logo-externa">
                <div class="info-container">
                    <div class="info-txt">👤 <b>CLIENTE:</b> {r['nome'].upper()}</div>
                    <div class="info-txt">📅 <b>STATUS:</b> <span class="{status_cor}">{dias_txt}</span></div>
                    <div class="info-txt">🔑 <b>USER:</b> {r['usuario']}</div>
                    <div class="info-txt">📶 <b>SISTEMA:</b> {r['servidor']} ({r['sistema']})</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("⚙️ CLIQUE PARA EDITAR"):
                with st.form(key=f"ed_{r['id']}"):
                    col1, col2 = st.columns(2)
                    en = col1.text_input("NOME", value=r['nome'])
                    eu = col2.text_input("USUÁRIO", value=r['usuario'])
                    es = col1.text_input("SENHA", value=r['senha'])
                    esrv = col2.selectbox("SERVIDOR", get_servidores(), key=f"srv_ed_{r['id']}")
                    esis = col1.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if r['sistema']=="P2P" else 1)
                    evd = col2.date_input("VENCIMENTO", value=dt_v.date(), format="DD/MM/YYYY", key=f"d_ed_{r['id']}")
                    ew = col1.text_input("WHATSAPP", value=r['whatsapp'])
                    e_img = col2.file_uploader("TROCAR LOGO", type=['png','jpg','jpeg'], key=f"img_ed_{r['id']}")
                    
                    b1, b2 = st.columns(2)
                    if b1.form_submit_button("💾 SALVAR"):
                        vf = datetime.combine(evd, dt_v.time()).strftime('%Y-%m-%d %H:%M:%S')
                        l_f = image_to_base64(e_img) if e_img else r['logo_blob']
                        c = sqlite3.connect('supertv_gestao.db')
                        c.execute("UPDATE clientes SET nome=?, usuario=?, senha=?, servidor=?, sistema=?, vencimento=?, whatsapp=?, logo_blob=? WHERE id=?", 
                                 (en, eu, es, esrv, esis, vf, ew, l_f, r['id']))
                        c.commit(); st.rerun()
                    if b2.form_submit_button("🗑️ EXCLUIR"):
                        c = sqlite3.connect('supertv_gestao.db')
                        c.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                        c.commit(); st.rerun()
