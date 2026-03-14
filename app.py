import streamlit as st
import numpy as np
from scipy.stats import poisson

def simulacion_monte_carlo(xg_local, xg_visita, num_simulaciones=10000):
    goles_local = np.random.poisson(xg_local, num_simulaciones)
    goles_visita = np.random.poisson(xg_visita, num_simulaciones)
    
    ambos_marcan = np.sum((goles_local > 0) & (goles_visita > 0)) / num_simulaciones
    over_1_5 = np.sum((goles_local + goles_visita) > 1.5) / num_simulaciones
    over_2_5 = np.sum((goles_local + goles_visita) > 2.5) / num_simulaciones
    
    return ambos_marcan, over_1_5, over_2_5

# Configuración de página
st.set_page_config(page_title="Odds Predictor", page_icon="⚽", layout="centered")

st.title("⚽ Calculadora Profesional de Apuestas")
st.markdown("Basada en el modelo de Poisson y Criterio de Kelly. **Perfecta para usar desde tu móvil.📱**")

with st.expander("ℹ️ ¿Cómo funciona?"):
    st.write("Esta app cruza los Goles Esperados (xG) a favor y en contra de cada equipo para proyectar escenarios de partido.")
    st.write("Genera probabilidades reales, encuentra valor en las cuotas de la casa de apuestas y simula 10,000 partidos para predecir mercados secundarios.")

st.header("1. Ingresar Datos xG (Goles Esperados)")
col_loc, col_vis = st.columns(2)

with col_loc:
    st.subheader("🏠 Equipo Local")
    xg_f_l = st.number_input("xG a Favor (Local)", min_value=0.0, step=0.1, value=1.96)
    xg_c_l = st.number_input("xG en Contra (Local)", min_value=0.0, step=0.1, value=1.35)

with col_vis:
    st.subheader("✈️ Equipo Visita")
    xg_f_v = st.number_input("xG a Favor (Visita)", min_value=0.0, step=0.1, value=1.52)
    xg_c_v = st.number_input("xG en Contra (Visita)", min_value=0.0, step=0.1, value=1.24)

st.header("2. Cuotas de la Casa de Apuestas")
col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    cuota_l = st.number_input("Cuota Local", min_value=1.01, step=0.1, value=1.83)
with col_c2:
    cuota_e = st.number_input("Cuota Empate", min_value=1.01, step=0.1, value=4.10)
with col_c3:
    cuota_v = st.number_input("Cuota Visita", min_value=1.01, step=0.1, value=3.90)

st.header("3. Gestión de Bankroll")
col_b1, col_b2 = st.columns(2)
with col_b1:
    bankroll = st.number_input("Bankroll Total (S/)", min_value=1.0, step=10.0, value=100.0)
with col_b2:
    fraccion_kelly = st.slider("Fracción de Kelly", 0.1, 1.0, 0.25, 0.05, help="0.25 recomendado para seguridad.")

if st.button("🚀 CALCULAR PRONÓSTICO", use_container_width=True, type="primary"):
    # Cálculos
    xg_local_proyectado = (xg_f_l + xg_c_v) / 2
    xg_visita_proyectado = (xg_f_v + xg_c_l) / 2
    
    st.markdown("---")
    st.subheader("📊 Análisis de Goles (xG Proyectado)")
    st.info(f"**Local:** {xg_local_proyectado:.2f} goles | **Visita:** {xg_visita_proyectado:.2f} goles")
    
    # Poisson
    prob_local = 0
    prob_visita = 0
    prob_empate = 0
    max_goles = 7
    for g_l in range(max_goles):
        for g_v in range(max_goles):
            prob = poisson.pmf(g_l, xg_local_proyectado) * poisson.pmf(g_v, xg_visita_proyectado)
            if g_l > g_v: prob_local += prob
            elif g_v > g_l: prob_visita += prob
            else: prob_empate += prob

    def calcular_kelly(p, cuota_casa):
        if p == 0: return 0, float('inf'), 0
        q = 1 - p
        b = cuota_casa - 1
        c_justa = 1 / p
        kelly = ((b * p) - q) / b
        apuesta = max(0, bankroll * kelly * fraccion_kelly)
        ventaja = (cuota_casa / c_justa - 1) * 100
        return apuesta, c_justa, ventaja

    apuesta_l, c_justa_l, vent_l = calcular_kelly(prob_local, cuota_l)
    apuesta_v, c_justa_v, vent_v = calcular_kelly(prob_visita, cuota_v)
    
    c_justa_e = 1/prob_empate if prob_empate > 0 else float('inf')
    margen_casa = (1/cuota_l + 1/cuota_e + 1/cuota_v) * 100 - 100

    st.subheader("📈 Mercado Principal")
    
    # Tabla usando markdown
    st.markdown(f"""
    | Selección | Prob. Real | Cuota Justa | Cuota Casa | Valor (Ventaja) |
    | :--- | :--- | :--- | :--- | :--- |
    | **Local** | {prob_local*100:.1f}% | {c_justa_l:.2f} | {cuota_l:.2f} | {vent_l:.1f}% |
    | **Visita** | {prob_visita*100:.1f}% | {c_justa_v:.2f} | {cuota_v:.2f} | {vent_v:.1f}% |
    | **Empate** | {prob_empate*100:.1f}% | {c_justa_e:.2f} | {cuota_e:.2f} | - |
    """)
    st.caption(f"Margen de la Casa (Overround): **{margen_casa:.1f}%**")

    st.subheader("💡 Recomendación Final")
    if vent_l > 50 or vent_v > 50:
        st.error("⚠️ RIESGO EXTREMO: La diferencia entre cuotas es anómala. Revisa lesiones o alineaciones.")
        
    recomendado = False
    if vent_l > 0:
        st.success(f"🔥 LOCAL: Apostar S/{apuesta_l:.2f}")
        recomendado = True
    if vent_v > 0:
        st.success(f"🔥 VISITA: Apostar S/{apuesta_v:.2f}")
        recomendado = True
    
    if not recomendado:
        st.warning("No hay valor en este partido. No arriesgar dinero.")

    # Monte Carlo
    st.markdown("---")
    st.subheader("🎲 Monte Carlo: Mercados Secundarios")
    with st.spinner("Simulando 10,000 partidos..."):
        prob_btts, prob_o15, prob_o25 = simulacion_monte_carlo(xg_local_proyectado, xg_visita_proyectado)
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Ambos Marcan", f"{prob_btts*100:.1f}%", f"Cuota Mín: {1/prob_btts:.2f}")
    col_m2.metric("Más 1.5", f"{prob_o15*100:.1f}%", f"Cuota Mín: {1/prob_o15:.2f}")
    col_m3.metric("Más 2.5", f"{prob_o25*100:.1f}%", f"Cuota Mín: {1/prob_o25:.2f}")
