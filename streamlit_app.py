with tab1:
    busca = st.text_input("🔍 PESQUISAR")
    if not df.empty:
        for _, r in df.sort_values(by='nome').iterrows():
            if busca.lower() in r['nome'].lower() or busca.lower() in str(r['usuario']).lower():
                try:
                    dt_v = datetime.strptime(r['vencimento'], '%Y-%m-%d %H:%M:%S')
                    d_txt = f"{r['dias_res']} DIAS" if r['dias_res'] >= 0 else "VENCIDO"
                except: 
                    dt_v = datetime.now()
                    d_txt = "Erro Data"
                
                status_ico = "🟢" if r['dias_res'] >= 0 else "🔴"
                
                # Título simplificado para evitar erro de renderização no expander
                titulo_botao = f"{status_ico} {r['servidor']} | {r['nome'].upper()} | VENCE EM: {d_txt}"

                with st.expander(titulo_botao):
                    # Criamos o layout visual com a logo dentro do expander aberto
                    col_logo, col_info = st.columns([1, 4])
                    
                    with col_logo:
                        img_src = f"data:image/png;base64,{r['logo_blob']}" if r['logo_blob'] else "https://i.imgur.com/vH9XvI0.png"
                        st.markdown(f'<img src="{img_src}" style="width:100%; border-radius:10px; border:1px solid #444;">', unsafe_allow_html=True)
                    
                    with col_info:
                        st.markdown(f"""
                        **USUÁRIO:** `{r['usuario']}`  |  **SENHA:** `{r['senha']}`  
                        **SERVIDOR:** {r['servidor']}  |  **SISTEMA:** {r['sistema']}
                        """, unsafe_allow_html=True)

                    st.divider()
                    
                    # Formulário de edição original abaixo
                    with st.form(key=f"ed_{r['id']}"):
                        en = st.text_input("NOME DO CLIENTE", value=r['nome'])
                        eu = st.text_input("USUÁRIO", value=r['usuario'])
                        es = st.text_input("SENHA", value=r['senha'])
                        esrv = st.selectbox("SERVIDOR", get_servidores(), key=f"srv_ed_{r['id']}")
                        esis = st.selectbox("SISTEMA", ["P2P", "IPTV"], index=0 if r['sistema']=="P2P" else 1)
                        
                        c_vd, c_vh = st.columns(2)
                        ev_d = c_vd.date_input("DATA VENC.", value=dt_v.date(), format="DD/MM/YYYY", key=f"d_{r['id']}")
                        ev_h = c_vh.time_input("HORA VENC.", value=dt_v.time(), key=f"t_{r['id']}")
                        
                        ew = st.text_input("WHATSAPP", value=r['whatsapp'])
                        e_img = st.file_uploader("ALTERAR LOGO", type=['png','jpg','jpeg'], key=f"img_{r['id']}")
                        
                        col_b1, col_b2 = st.columns(2)
                        if col_b1.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                            vf = datetime.combine(ev_d, ev_h).strftime('%Y-%m-%d %H:%M:%S')
                            l_f = image_to_base64(e_img) if e_img else r['logo_blob']
                            c = sqlite3.connect('supertv_gestao.db')
                            c.execute("UPDATE clientes SET nome=?, usuario=?, senha=?, servidor=?, sistema=?, vencimento=?, whatsapp=?, logo_blob=? WHERE id=?", 
                                     (en, eu, es, esrv, esis, vf, ew, l_f, r['id']))
                            c.commit(); st.rerun()
                        if col_b2.form_submit_button("🗑️ EXCLUIR"):
                            c = sqlite3.connect('supertv_gestao.db')
                            c.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                            c.commit(); st.rerun()
