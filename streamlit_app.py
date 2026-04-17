with tab4:
    st.subheader("⚙️ AJUSTES E MANUTENÇÃO")
    c_limp1, c_limp2 = st.columns(2)
    
    with c_limp1:
        st.markdown("### 🧹 Limpeza Profunda")
        if st.button("🗑️ REMOVER REGISTROS 'NONE' (LIMPAR LISTA)", use_container_width=True):
            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("DELETE FROM clientes WHERE nome IS NULL OR nome = '' OR nome = 'None' OR nome = 'nan'")
            conn.commit(); conn.close(); st.success("Registros fantasmas removidos!"); st.rerun()

        if st.button("🚨 LIMPEZA TOTAL (RESETAR BANCO)", type="primary", use_container_width=True):
            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("DELETE FROM clientes")
            conn.commit(); conn.close(); st.success("Banco de dados resetado com sucesso!"); st.rerun()

    with c_limp2:
        st.markdown("### 📥 Importação Blindada")
        f_up = st.file_uploader("Subir Excel corrigido", type=["xlsx"])
        if f_up and st.button("🚀 IMPORTAR AGORA"):
            try:
                # Carrega o Excel
                imp = pd.read_excel(f_up, engine='openpyxl')
                # Padroniza títulos: remove espaços e coloca em maiúsculo
                imp.columns = [str(c).strip().upper() for c in imp.columns]
                
                # Remove linhas totalmente vazias
                imp = imp.dropna(how='all')

                # Mapeamento para os nomes do banco de dados
                mapeamento = {
                    'CLIENTE': 'nome', 'USUÁRIO': 'usuario', 'SENHA': 'senha',
                    'SERVIDOR': 'servidor', 'SISTEMA': 'sistema', 'VENCIMENTO': 'vencimento',
                    'CUSTO': 'custo', 'VALOR COBRADO': 'mensalidade', 'INÍCIOU DIA': 'inicio',
                    'WHATSAPP': 'whatsapp', 'OBSERVAÇÃO': 'observacao'
                }
                
                # Renomeia o que encontrar
                imp = imp.rename(columns=mapeamento)
                
                # Colunas necessárias no banco
                cols_banco = ['nome', 'usuario', 'senha', 'servidor', 'sistema', 'vencimento', 'custo', 'mensalidade', 'inicio', 'whatsapp', 'observacao']
                
                # Cria colunas que faltarem como vazias
                for c in cols_banco:
                    if c not in imp.columns:
                        imp[c] = None

                # Filtra para aceitar apenas nomes válidos
                if 'nome' in imp.columns:
                    imp = imp[imp['nome'].notnull()]
                    imp = imp[imp['nome'].astype(str).lower() != 'none']
                    imp = imp[imp['nome'].astype(str).strip() != '']
                
                df_final = imp[cols_banco]
                
                if not df_final.empty:
                    conn = sqlite3.connect('supertv_gestao.db')
                    df_final.to_sql('clientes', conn, if_exists='append', index=False)
                    conn.close()
                    st.success(f"✅ {len(df_final)} Clientes importados!")
                    st.rerun()
                else:
                    st.warning("⚠️ Nenhuma linha válida com nome foi encontrada.")

            except Exception as e:
                st.error(f"Erro na Importação: {e}")
