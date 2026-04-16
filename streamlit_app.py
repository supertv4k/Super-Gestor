# --- 6. DASHBOARD DE MÉTRICAS ---
if not df.empty:
    hoje = datetime.now().date()
    # Converte para data, forçando 'NaT' (Not a Time) em caso de erro
    df['dt_venc_calc'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    
    # Cálculo seguro: se for nulo, assume 0 dias
    def calcular_dias(venc):
        if pd.isnull(venc):
            return 0
        return (venc - hoje).days

    df['dias_res'] = df['dt_venc_calc'].apply(calcular_dias)
    
    bruto, custos = df['mensalidade'].sum(), df['custo'].sum()
    liquido = bruto - custos
    vencidos = len(df[df["dias_res"] < 0])
    vencendo_3 = len(df[(df["dias_res"] >= 0) & (df["dias_res"] <= 3)])

    c1, c2, c3 = st.columns(3); c4, c5, c6 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL CLIENTES</div><div class="metric-value" style="color: #ffffff;">{len(df)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">VENCIDOS</div><div class="metric-value" style="color: #ff4b4b;">{vencidos}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">VENCEM EM 3 DIAS</div><div class="metric-value" style="color: #ffff00;">{vencendo_3}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO BRUTO</div><div class="metric-value" style="color: #00ff00;">R$ {bruto:,.2f}</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-label">LUCRO LÍQUIDO</div><div class="metric-value" style="color: #00d4ff;">R$ {liquido:,.2f}</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="metric-card"><div class="metric-label">CUSTO CRÉDITOS</div><div class="metric-value" style="color: #8b949e;">R$ {custos:,.2f}</div></div>', unsafe_allow_html=True)
