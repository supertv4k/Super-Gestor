    with c_limp2:
        st.markdown("### 📥 Importação Blindada")
        f_up = st.file_uploader("Subir Excel corrigido", type=["xlsx"])
        if f_up and st.button("🚀 IMPORTAR AGORA"):
            try:
                # Carrega o Excel e limpa espaços vazios nos títulos das colunas
                imp = pd.read_excel(f_up, engine='openpyxl')
                imp.columns = [str(c).strip().upper() for c in imp.columns] # Padroniza para MAIÚSCULO
                
                # Remove linhas totalmente vazias
                imp = imp.dropna(how='all')

                # Mapeamento seguro: procura o nome que você usa no Excel
                # Se não existir a coluna 'CLIENTE', ele cria uma vazia para não dar erro
                mapeamento = {
                    'CLIENTE': 'nome', 'USUÁRIO': 'usuario', 'SENHA': 'senha',
                    'SERVIDOR': 'servidor', 'SISTEMA': 'sistema', 'VENCIMENTO': 'vencimento',
                    'CUSTO': 'custo', 'VALOR COBRADO': 'mensalidade', 'INÍCIOU DIA': 'inicio',
                    'WHATSAPP': 'whatsapp', 'OBSERVAÇÃO': 'observacao'
                }
                
                # Executa a renomeação apenas das colunas que existem no arquivo
                imp = imp.rename(columns=mapeamento)
                
                # Lista oficial de colunas do banco de dados
                cols_banco = ['nome', 'usuario', 'senha', 'servidor', 'sistema', 'vencimento', 'custo', 'mensalidade', 'inicio', 'whatsapp', 'observacao']
                
                # Garante que todas as colunas do banco existam no DataFrame, mesmo que vazias
                for c in cols_banco:
                    if c not in imp.columns:
                        imp[c] = None

                # --- FILTRO ANTI-ERRO ---
                # Verifica se a coluna 'nome' existe após o mapeamento
                if 'nome' in imp.columns:
                    # Remove quem tem nome nulo ou escrito 'None'
                    imp = imp[imp['nome'].notnull()]
                    imp = imp[imp['nome'].astype(str).lower() != 'none']
                    imp = imp[imp['nome'].astype(str) != '']
                
                df_final = imp[cols_banco]
                
                if not df_final.empty:
                    conn = sqlite3.connect('supertv_gestao.db')
                    df_final.to_sql('clientes', conn, if_exists='append', index=False)
                    conn.close()
                    st.success(f"✅ {len(df_final)} Clientes importados com sucesso!")
                    st.rerun()
                else:
                    st.warning("⚠️ Nenhuma linha válida encontrada no Excel.")

            except Exception as e:
                st.error(f"Erro na Importação: Certifique-se que a primeira coluna do seu Excel se chama CLIENTE. (Detalhe técnico: {e})")
