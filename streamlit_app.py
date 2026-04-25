    # COBRANÇA (DENTRO DA TAB 3)
    with tab3:
        st.subheader("🚨 COBRANÇAS")
        c_cols = st.columns(6)
        filtros = ["vencidos", "hoje", "1dia", "2dias", "3dias", "todos"]
        labels = ["❌ Vencidos", "📅 Hoje", "🌅 Amanhã", "⏳ 2 Dias", "⏳ 3 Dias", "🗓️ Todos"]
        for i, f in enumerate(filtros):
            if c_cols[i].button(labels[i]): st.session_value.filtro_f = f
        
        filtro = st.session_state.filtro_f
        cnpj_pix = "\n\n💠PIX CNPJ\n62.326.879/0001-13\n\n⚠️ NÃO ESQUEÇA DE ENVIAR O COMPROVANTE NO WHATSAPP!!!"
        msg_map = {
            "vencidos": "🚨SUA ASSINATURA DE TV VENCEU !" + cnpj_pix,
            "hoje": "⚠️SUA ASSINATURA DE TV VENCE HOJE ⏰!" + cnpj_pix,
            "1dia": "⚠️SUA ASSINATURA DE TV VENCE AMANHÃ ⏰!" + cnpj_pix,
            "2dias": "⚠️SUA ASSINATURA DE TV VENCE EM 2️⃣ DIAS ⏰!" + cnpj_pix,
            "3dias": "⚠️SUA ASSINATURA DE TV VENCE EM 3️⃣ DIAS ⏰!" + cnpj_pix,
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
            # --- LOGICA DE SELEÇÃO E DISPARO EM MASSA ---
            col_sel, col_btn = st.columns([1, 2])
            with col_sel:
                sel_all = st.checkbox(f"✅ Selecionar todos ({len(df_c)})", key=f"sel_all_{filtro}")
            
            # Criamos uma lista para armazenar os IDs dos selecionados
            lista_para_disparo = []

            # Exibição dos cards com checkbox individual
            for _, r in df_c.iterrows():
                img = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
                cor = get_cor_classe(r['dias_res'])
                with st.container():
                    c1, c2, c3 = st.columns([0.5, 4.3, 1.2])
                    
                    # Se o "Selecionar Todos" estiver ativo, o valor padrão é True
                    selecionado = c1.checkbox("", value=sel_all, key=f"chk_{r['id']}")
                    if selecionado:
                        lista_para_disparo.append({"whats": r['whatsapp'], "msg": msg_atual, "nome": r['nome']})

                    c2.markdown(f'<div class="cliente-card-html"><img src="{img}" class="img-servidor-card"><div class="info-container"><div class="nome-c">{r["nome"]}</div><span style="color:#8b949e;">{r["sistema"]}</span></div><div class="dias-box"><span class="{cor}">{r["dias_res"]} DIAS</span></div></div>', unsafe_allow_html=True)
                    url_whats = f"https://wa.me/55{r['whatsapp']}?text={urllib.parse.quote(msg_atual)}"
                    c3.link_button("📲 COBRAR", url_whats)

            st.divider()

            # --- BOTÃO DE DISPARO EM MASSA (Abaixo da lista) ---
            if lista_para_disparo:
                if st.button(f"🚀 DISPARAR MENSAGENS PARA {len(lista_para_disparo)} CLIENTES", use_container_width=True, type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, cliente in enumerate(lista_para_disparo):
                        texto_encoded = urllib.parse.quote(cliente['msg'])
                        link = f"https://wa.me/55{cliente['whats']}?text={texto_encoded}"
                        
                        # Comando para abrir o link em nova aba via JavaScript
                        js = f"window.open('{link}', '_blank').focus();"
                        st.components.v1.html(f"<script>{js}</script>", height=0)
                        
                        # Atualiza barra de progresso
                        progresso = (i + 1) / len(lista_para_disparo)
                        progress_bar.progress(progresso)
                        status_text.text(f"Enviando para: {cliente['nome']}...")
                        
                        # Delay para não travar o navegador e evitar bloqueios
                        time.sleep(1.2)
                    
                    st.success("✅ Processo concluído! Verifique as abas abertas no seu navegador.")
