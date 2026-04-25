import streamlit as st
import pandas as pd
import urllib.parse
import time

# --- (Mantendo seu CSS e conexão GSheets) ---

    with tab3:
        st.subheader("🚨 CENTRAL DE COBRANÇA (MODO CELULAR)")
        
        # Filtros de busca rápida
        filtro = st.radio("Filtrar por:", ["Vencidos", "Vencem Hoje", "Todos"], horizontal=True)
        
        df_c = df
        if filtro == "Vencidos": df_c = df[df['dias_res'] < 0]
        elif filtro == "Vencem Hoje": df_c = df[df['dias_res'] == 0]

        if not df_c.empty:
            st.info(f"📱 {len(df_c)} clientes encontrados para cobrança.")
            
            # Texto padrão de cobrança (Com seu PIX)
            pix_info = "\n\n💠 PIX CNPJ\n62.326.879/0001-13\n\n⚠️ Envie o comprovante!"
            
            for _, r in df_c.iterrows():
                # Mensagem personalizada
                if r['dias_res'] < 0:
                    msg = f"🚨 Olá {r['nome']}, sua assinatura SUPERTV4K VENCEU!{pix_info}"
                else:
                    msg = f"⚠️ Olá {r['nome']}, sua assinatura SUPERTV4K VENCE HOJE!{pix_info}"
                
                # Link otimizado para Android (LG K41S)
                # O formato 'whatsapp://send' costuma abrir direto o app sem passar pelo navegador
                url_android = f"whatsapp://send?phone=55{r['whatsapp']}&text={urllib.parse.quote(msg)}"
                
                with st.container():
                    # Criamos um "Card de Disparo" menor para caber na tela do LG
                    col_info, col_btn = st.columns([2, 1])
                    
                    with col_info:
                        st.markdown(f"**{r['nome']}**")
                        st.caption(f"Vencimento: {r['vencimento']}")
                    
                    with col_btn:
                        # No Android, usamos o link_button que aciona o protocolo do WhatsApp
                        st.link_button("🚀 ENVIAR", url_android, use_container_width=True)
                st.divider()
        else:
            st.success("Tudo em dia! Nenhum cliente para cobrar neste filtro.")
