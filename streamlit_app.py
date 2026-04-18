with tab1:
    busca = st.text_input("🔎 Buscar cliente")

    if not df.empty:
        df_f = df.copy()
        if busca:
            df_f = df_f[df_f["nome"].str.contains(busca, case=False, na=False)]

        for _, r in df_f.iterrows():

            col1, col2 = st.columns([4, 1])

            with col1:
                st.write(f"👤 {r['nome']} | {r['usuario']} | 📅 {r['vencimento']}")

            with col2:
                if st.button("⚙️ EDITAR", key=f"edit_{r['id']}"):
                    st.session_state["edit_id"] = r["id"]

# =========================
# PAINEL DE EDIÇÃO
# =========================
if "edit_id" in st.session_state:
    cliente = df[df["id"] == st.session_state["edit_id"]].iloc[0]

    st.subheader("✏️ Editar Cliente")

    with st.form("edit_form"):
        nome = st.text_input("Cliente", value=cliente["nome"])
        user = st.text_input("Usuário", value=cliente["usuario"])
        senha = st.text_input("Senha", value=cliente["senha"])
        servidor = st.text_input("Servidor", value=cliente["servidor"])
        sistema = st.selectbox("Sistema", ["IPTV", "P2P"], index=0 if cliente["sistema"] == "IPTV" else 1)
        venc = st.date_input("Vencimento", datetime.strptime(cliente["vencimento"], "%Y-%m-%d"))

        col1, col2 = st.columns(2)

        salvar = st.form_submit_button("💾 Salvar")
        renovar = col1.form_submit_button("🔁 Renovar +30 dias")
        excluir = col2.form_submit_button("🗑️ Excluir")

        conn = get_conn()

        if salvar:
            conn.execute("""
                UPDATE clientes SET nome=?, usuario=?, senha=?, servidor=?, sistema=?, vencimento=?
                WHERE id=?
            """, (nome, user, senha, servidor, sistema, venc.strftime("%Y-%m-%d"), cliente["id"]))
            conn.commit()
            st.success("Atualizado!")
            st.session_state.pop("edit_id")

        if renovar:
            novo_venc = (venc + timedelta(days=30)).strftime("%Y-%m-%d")
            conn.execute("UPDATE clientes SET vencimento=? WHERE id=?", (novo_venc, cliente["id"]))
            conn.commit()
            st.success("Renovado!")

        if excluir:
            conn.execute("DELETE FROM clientes WHERE id=?", (cliente["id"],))
            conn.commit()
            st.warning("Cliente removido")
            st.session_state.pop("edit_id")

        conn.close()
