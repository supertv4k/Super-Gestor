# --- ESTILIZAÇÃO CSS (FOCO NO ALINHAMENTO LATERAL FIXO) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    
    /* Container que força a Logo e o Botão a ficarem lado a lado */
    .client-row {
        display: flex;
        align-items: center;
        width: 100%;
        gap: 15px; /* Espaço fixo entre a logo e o botão */
        margin-bottom: 12px;
    }

    /* Logo Fixa com tamanho controlado */
    .img-servidor-fixa {
        width: 60px !important;
        height: 60px !important;
        border-radius: 10px;
        object-fit: cover;
        border: 1px solid #30363d;
        flex-shrink: 0; /* Não deixa a imagem diminuir */
    }

    /* O Botão Retangular e Alongado */
    div.stButton > button {
        width: 100% !important;
        height: 60px !important; /* Mesma altura da imagem para alinhar */
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: white !important;
        border-radius: 10px !important; /* Retangular com cantos leves */
        text-align: left !important;
        padding-left: 20px !important;
        display: flex !important;
        align-items: center !important;
        transition: 0.3s;
    }

    div.stButton > button:hover {
        border-color: #00d4ff !important;
        background-color: #1c2128 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- NA ABA CLIENTES (TAB 1) ---
with tab1:
    # ... (Seu código de busca aqui) ...
    
    for _, r in df_f.sort_values(by='dias_res').iterrows():
        img_src = f"data:image/png;base64,{r['logo_blob']}" if r.get('logo_blob') else "https://i.imgur.com/vH9XvI0.png"
        venc_br = format_data_br(r.get('vencimento'))
        
        # Criamos a linha manualmente para garantir que a imagem fique na esquerda
        st.markdown(f'<div class="client-row">', unsafe_allow_html=True)
        
        # 1. Coluna da Esquerda: Logo Fixa
        col_logo, col_info = st.columns([1, 8]) # Usamos proporção fixa
        
        with col_logo:
            st.markdown(f'<img src="{img_src}" class="img-servidor-fixa">', unsafe_allow_html=True)
        
        with col_info:
            # 2. Coluna da Direita: Informações em formato de botão longo
            txt_btn = f"{str(r.get('nome')).upper()} | 🔑 {r.get('usuario')} | 📅 {venc_br}"
            if st.button(txt_btn, key=f"btn_{r['id']}"):
                st.session_state.cliente_selecionado = r.to_dict()
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
