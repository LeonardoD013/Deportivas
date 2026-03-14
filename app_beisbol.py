import streamlit as st
import numpy as np
import math
from scipy.stats import poisson

def simulacion_beisbol(xr_local, xr_visita, num_simulaciones=10000):
    # Simular 9 entradas
    carreras_local = np.random.poisson(xr_local, num_simulaciones)
    carreras_visita = np.random.poisson(xr_visita, num_simulaciones)
    
    # Simular F5 (Primeras 5 entradas) aproximadamente (5/9 del total)
    c_loc_f5 = np.random.poisson(xr_local * (5/9), num_simulaciones)
    c_vis_f5 = np.random.poisson(xr_visita * (5/9), num_simulaciones)
    
    vic_loc_f5 = np.sum(c_loc_f5 > c_vis_f5) / num_simulaciones
    vic_vis_f5 = np.sum(c_vis_f5 > c_loc_f5) / num_simulaciones
    emp_f5 = np.sum(c_loc_f5 == c_vis_f5) / num_simulaciones

    # Extra innings
    empates = (carreras_local == carreras_visita)
    num_empates = np.sum(empates)
    
    # Resolviendo empates simulando entradas extra
    if num_empates > 0:
        carreras_extra_l = np.random.poisson(xr_local / 9, num_empates)
        carreras_extra_v = np.random.poisson(xr_visita / 9, num_empates)
        
        # Evitar bucles infinitos simplificando: si empatan en el 1er extra, sumamos 1 al local (ventaja de casa en extra inning)
        nuevos_empates = (carreras_extra_l == carreras_extra_v)
        carreras_extra_l[nuevos_empates] += 1 
        
        carreras_local[empates] += carreras_extra_l
        carreras_visita[empates] += carreras_extra_v

    victorias_local = np.sum(carreras_local > carreras_visita) / num_simulaciones
    victorias_visita = np.sum(carreras_visita > carreras_local) / num_simulaciones
    
    # Run Line (-1.5 / +1.5)
    # Suponiendo que el favorito es el que tiene más xR (normalmente el Local tiene la cuota -1.5 si es favorito, dejaremos que el usuario asigne el favorito mentalmente, aquí calculamos el -1.5 para el Local y el +1.5 para la Visita)
    rl_loc_menos15 = np.sum((carreras_local - carreras_visita) >= 2) / num_simulaciones
    rl_vis_mas15 = 1 - rl_loc_menos15 # La visita pierde por 1 o gana
    
    return carreras_local, carreras_visita, victorias_local, victorias_visita, vic_loc_f5, vic_vis_f5, emp_f5, rl_loc_menos15, rl_vis_mas15

# Configuración de página
st.set_page_config(page_title="MLB Odds Predictor", page_icon="⚾", layout="centered")

st.title("⚾ Calculadora Profesional de Apuestas - Béisbol")
st.markdown("Basada en proyecciones de Carreras y Criterio de Kelly. **Perfecta para usar desde tu móvil.📱**")

with st.expander("ℹ️ ¿Cómo funciona?"):
    st.write("Esta app utiliza las Carreras Esperadas (xR) de cada equipo (promedios anotados y concedidos considerando a los pitchers) para proyectar escenarios del partido.")
    st.write("Simula 10,000 partidos mediante Monte Carlo para evitar empates (resolviendo extra innings) y encuentra valor en las cuotas de la casa de apuestas.")

st.header("1. Ingresar Datos xR (Carreras Esperadas)")
col_loc, col_vis = st.columns(2)

with col_loc:
    st.subheader("🏠 Equipo Local")
    xr_f_l = st.number_input("Carreras a Favor (Local)", min_value=0.0, step=0.1, value=4.5)
    xr_c_l = st.number_input("Carreras en Contra (Local)", min_value=0.0, step=0.1, value=4.0)

with col_vis:
    st.subheader("✈️ Equipo Visita")
    xr_f_v = st.number_input("Carreras a Favor (Visita)", min_value=0.0, step=0.1, value=4.2)
    xr_c_v = st.number_input("Carreras en Contra (Visita)", min_value=0.0, step=0.1, value=4.1)

st.header("2. Cuotas de la Casa de Apuestas")
st.subheader("Moneyline (Ganador)")
col_c1, col_c2 = st.columns(2)
with col_c1:
    cuota_l = st.number_input("Cuota Local", min_value=1.00, step=0.01, value=1.85)
with col_c2:
    cuota_v = st.number_input("Cuota Visita", min_value=1.00, step=0.01, value=1.95)

st.subheader("Mercados de Totales (Carreras)")
col_g1, col_g2, col_g3 = st.columns(3)
with col_g1:
    linea_totales = st.number_input("Línea de Carreras (Ej. 8.5)", min_value=0.5, step=0.5, value=8.5)
with col_g2:
    cuota_over = st.number_input("Más de la Línea", min_value=1.00, step=0.01, value=1.90)
with col_g3:
    cuota_under = st.number_input("Menos de la Línea", min_value=1.00, step=0.01, value=1.90)

st.subheader("Run Line (-1.5 / +1.5)")
col_rl1, col_rl2 = st.columns(2)
with col_rl1:
    cuota_rl_loc = st.number_input("Local -1.5", min_value=1.00, step=0.01, value=2.40)
with col_rl2:
    cuota_rl_vis = st.number_input("Visita +1.5", min_value=1.00, step=0.01, value=1.60)

st.subheader("Primeras 5 Entradas (F5)")
col_f5_1, col_f5_2, col_f5_3 = st.columns(3)
with col_f5_1:
    cuota_f5_loc = st.number_input("Local F5", min_value=1.00, step=0.01, value=1.85)
with col_f5_2:
    cuota_f5_emp = st.number_input("Empate F5", min_value=1.00, step=0.01, value=4.50)
with col_f5_3:
    cuota_f5_vis = st.number_input("Visita F5", min_value=1.00, step=0.01, value=2.00)

st.header("3. Gestión de Bankroll")
col_b1, col_b2 = st.columns(2)
with col_b1:
    bankroll = st.number_input("Bankroll Total (S/)", min_value=1.0, step=10.0, value=100.0)
with col_b2:
    fraccion_kelly = st.slider("Fracción de Kelly", 0.1, 1.0, 0.25, 0.05, help="0.25 recomendado para seguridad.")

if st.button("🚀 CALCULAR PRONÓSTICO", use_container_width=True, type="primary"):
    # Cálculos Carreras
    xr_local_proyectado = (xr_f_l + xr_c_v) / 2
    xr_visita_proyectado = (xr_f_v + xr_c_l) / 2
    
    st.markdown("---")
    st.subheader("📊 Análisis de Carreras")
    st.info(f"**Carreras Esperadas (xR):** Local {xr_local_proyectado:.2f} | Visita {xr_visita_proyectado:.2f}")
    
    with st.spinner("Simulando partidos..."):
        c_loc, c_vis, prob_local, prob_visita, prob_loc_f5, prob_vis_f5, prob_emp_f5, prob_rl_loc, prob_rl_vis = simulacion_beisbol(xr_local_proyectado, xr_visita_proyectado)
        
        # Totales
        total_carreras = c_loc + c_vis
        prob_over = np.sum(total_carreras > linea_totales) / 10000
        prob_under = 1 - prob_over

    def calcular_kelly(p, cuota_casa):
        if p <= 0 or cuota_casa <= 1.0: return 0.0, float('inf'), 0.0
        q = 1 - p
        b = cuota_casa - 1
        c_justa = 1 / p
        kelly = ((b * p) - q) / b
        apuesta = max(0, bankroll * kelly * fraccion_kelly)
        ventaja = (cuota_casa / c_justa - 1) * 100
        return apuesta, c_justa, ventaja

    # Kelly Principal
    apuesta_l, c_justa_l, vent_l = calcular_kelly(prob_local, cuota_l)
    apuesta_v, c_justa_v, vent_v = calcular_kelly(prob_visita, cuota_v)

    # Kelly Totales
    ap_over, cj_over, v_over = calcular_kelly(prob_over, cuota_over)
    ap_under, cj_under, v_under = calcular_kelly(prob_under, cuota_under)
    
    # Kelly Run Line
    ap_rl_loc, cj_rl_loc, v_rl_loc = calcular_kelly(prob_rl_loc, cuota_rl_loc)
    ap_rl_vis, cj_rl_vis, v_rl_vis = calcular_kelly(prob_rl_vis, cuota_rl_vis)

    # Kelly F5
    ap_f5_loc, cj_f5_loc, v_f5_loc = calcular_kelly(prob_loc_f5, cuota_f5_loc)
    ap_f5_vis, cj_f5_vis, v_f5_vis = calcular_kelly(prob_vis_f5, cuota_f5_vis)
    ap_f5_emp, cj_f5_emp, v_f5_emp = calcular_kelly(prob_emp_f5, cuota_f5_emp)

    st.subheader("📈 Moneyline")
    st.markdown(f'''
    | Selección | Prob. Real | Cuota Justa | Cuota Casa | Valor (Ventaja) | Apuesta Sugerida |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | **Local** | {prob_local*100:.1f}% | {c_justa_l:.2f} | {cuota_l:.2f} | {vent_l:.1f}% | S/ {apuesta_l:.2f} |
    | **Visita** | {prob_visita*100:.1f}% | {c_justa_v:.2f} | {cuota_v:.2f} | {vent_v:.1f}% | S/ {apuesta_v:.2f} |
    ''')
    
    st.subheader("💨 Run Line")
    st.markdown(f'''
    | Selección | Prob. Real | Cuota Justa | Cuota Casa | Valor (Ventaja) | Apuesta Sugerida |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | **Local -1.5** | {prob_rl_loc*100:.1f}% | {cj_rl_loc:.2f} | {cuota_rl_loc:.2f} | {v_rl_loc:.1f}% | S/ {ap_rl_loc:.2f} |
    | **Visita +1.5** | {prob_rl_vis*100:.1f}% | {cj_rl_vis:.2f} | {cuota_rl_vis:.2f} | {v_rl_vis:.1f}% | S/ {ap_rl_vis:.2f} |
    ''')

    st.subheader("⚾ Mercados de Totales")
    st.markdown(f'''
    | Selección | Prob. Real | Cuota Justa | Cuota Casa | Valor (Ventaja) | Apuesta Sugerida |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | **Más de {linea_totales}** | {prob_over*100:.1f}% | {cj_over:.2f} | {cuota_over:.2f} | {v_over:.1f}% | S/ {ap_over:.2f} |
    | **Menos de {linea_totales}** | {prob_under*100:.1f}% | {cj_under:.2f} | {cuota_under:.2f} | {v_under:.1f}% | S/ {ap_under:.2f} |
    ''')

    st.subheader("🥇 Primeras 5 Entradas (F5)")
    st.markdown(f'''
    | Selección | Prob. Real | Cuota Justa | Cuota Casa | Valor (Ventaja) | Apuesta Sugerida |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | **Local (F5)** | {prob_loc_f5*100:.1f}% | {cj_f5_loc:.2f} | {cuota_f5_loc:.2f} | {v_f5_loc:.1f}% | S/ {ap_f5_loc:.2f} |
    | **Empate (F5)** | {prob_emp_f5*100:.1f}% | {cj_f5_emp:.2f} | {cuota_f5_emp:.2f} | {v_f5_emp:.1f}% | S/ {ap_f5_emp:.2f} |
    | **Visita (F5)** | {prob_vis_f5*100:.1f}% | {cj_f5_vis:.2f} | {cuota_f5_vis:.2f} | {v_f5_vis:.1f}% | S/ {ap_f5_vis:.2f} |
    ''')

    st.markdown("---")
    st.subheader("💡 Recomendaciones Destacadas")
    
    apuestas = [
        {"desc": "Local (Ganador)", "vent": vent_l, "apuesta": apuesta_l},
        {"desc": "Visita (Ganador)", "vent": vent_v, "apuesta": apuesta_v},
        {"desc": f"Más de {linea_totales} Carreras", "vent": v_over, "apuesta": ap_over},
        {"desc": f"Menos de {linea_totales} Carreras", "vent": v_under, "apuesta": ap_under},
        {"desc": "Local -1.5 (Run Line)", "vent": v_rl_loc, "apuesta": ap_rl_loc},
        {"desc": "Visita +1.5 (Run Line)", "vent": v_rl_vis, "apuesta": ap_rl_vis},
        {"desc": "Local (Primeras 5)", "vent": v_f5_loc, "apuesta": ap_f5_loc},
        {"desc": "Visita (Primeras 5)", "vent": v_f5_vis, "apuesta": ap_f5_vis},
        {"desc": "Empate (Primeras 5)", "vent": v_f5_emp, "apuesta": ap_f5_emp},
    ]

    recomendaciones = [ap for ap in apuestas if ap["vent"] > 0 and ap["apuesta"] > 0]
    
    if not recomendaciones:
        st.warning("No hay valor en ninguno de los mercados analizados. No arriesgar dinero.")
    else:
        # Ordenar por ventaja (mayor a menor)
        recomendaciones.sort(key=lambda x: x["vent"], reverse=True)
        for rec in recomendaciones:
            st.success(f"🔥 **{rec['desc']}**: Apostar S/ {rec['apuesta']:.2f} (Ventaja: {rec['vent']:.1f}%)")
            
        if any(rec["vent"] > 50 for rec in recomendaciones):
            st.error("⚠️ RIESGO EXTREMO: Hay ventajas anómalas (>50%). Revisa bien los datos ingresados o a los pitchers abridores.")
