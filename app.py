import streamlit as st
import numpy as np
import math
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from odds_predictor import simulacion_monte_carlo_extendida, calcular_kelly, calcular_poisson_partido
from data_scraper import obtener_datos_liga_fbref, LIGAS_DISPONIBLES

@st.cache_data(show_spinner=False)
def obtener_simulacion_monte_carlo(xg_local, xg_visita, num_simulaciones=10000):
    return simulacion_monte_carlo_extendida(xg_local, xg_visita, num_simulaciones)

# Configuración de página
st.set_page_config(page_title="Odds Predictor", page_icon="⚽", layout="centered")

# Inicializar Base de Datos en Memoria (Session State)
if 'historial' not in st.session_state:
    st.session_state.historial = []
if 'datos_liga_actual' not in st.session_state:
    st.session_state.datos_liga_actual = None
if 'xg_local_auto' not in st.session_state:
    st.session_state.xg_local_auto = 1.96
if 'xga_local_auto' not in st.session_state:
    st.session_state.xga_local_auto = 1.35
if 'xg_visita_auto' not in st.session_state:
    st.session_state.xg_visita_auto = 1.52
if 'xga_visita_auto' not in st.session_state:
    st.session_state.xga_visita_auto = 1.24

st.title("⚽ Calculadora Profesional de Apuestas")
st.markdown("Basada en el modelo de Poisson y Criterio de Kelly. **Perfecta para usar desde tu móvil.📱**")

with st.expander("ℹ️ ¿Cómo funciona?"):
    st.write("Esta app cruza los Goles Esperados (xG) y promedios de córners a favor y en contra de cada equipo para proyectar escenarios de partido.")
    st.write("Genera probabilidades reales, encuentra valor en las cuotas de la casa de apuestas y simula partidos para predecir mercados secundarios.")

st.markdown("---")
st.header("📡 0. Asistente de Datos Automáticos (FBref)")
st.write("¿No quieres ingresar los xG a mano? Selecciona tu liga y partido, y el asistente lo hará por ti.")

col_lg1, col_lg2 = st.columns([1, 2])
with col_lg1:
    liga_seleccionada = st.selectbox("Seleccionar Liga", list(LIGAS_DISPONIBLES.keys()))

with col_lg2:
    if st.button("⬇️ Descargar Datos de la Liga", type="secondary", use_container_width=True):
        with st.spinner(f"Obteniendo datos frescos de {liga_seleccionada}..."):
            url = LIGAS_DISPONIBLES[liga_seleccionada]
            df_liga = obtener_datos_liga_fbref(url)
            if df_liga is not None and not df_liga.empty:
                st.session_state.datos_liga_actual = df_liga
                st.success("✅ Base de datos actualizada con éxito.")
            else:
                st.error("❌ Error al descargar datos. FBref podría estar bloqueando el acceso. Por favor, usa el ingreso manual.")

if st.session_state.datos_liga_actual is not None:
    df = st.session_state.datos_liga_actual
    equipos = df['Equipo'].tolist()
    
    col_sel1, col_sel2, col_sel3 = st.columns([3, 3, 2])
    with col_sel1:
        equipo_local = st.selectbox("🏠 Equipo Local", equipos, index=0)
    with col_sel2:
        equipo_visita = st.selectbox("✈️ Equipo Visitante", equipos, index=1 if len(equipos)>1 else 0)
    with col_sel3:
        st.write("") # Espaciador
        st.write("") # Espaciador
        if st.button("⚡ Cargar Partido", type="primary", use_container_width=True):
            if equipo_local == equipo_visita:
                st.warning("Selecciona dos equipos diferentes.")
            else:
                st.session_state.xg_local_auto = float(df[df['Equipo'] == equipo_local]['xG_Favor_Avg'].values[0])
                st.session_state.xga_local_auto = float(df[df['Equipo'] == equipo_local]['xG_Contra_Avg'].values[0])
                
                st.session_state.xg_visita_auto = float(df[df['Equipo'] == equipo_visita]['xG_Favor_Avg'].values[0])
                st.session_state.xga_visita_auto = float(df[df['Equipo'] == equipo_visita]['xG_Contra_Avg'].values[0])
                st.rerun()

st.markdown("---")
st.header("1. Ingresar Datos xG (Goles Esperados)")
col_loc, col_vis = st.columns(2)

with col_loc:
    st.subheader("🏠 Equipo Local")
    xg_f_l = st.number_input("xG a Favor (Local)", min_value=0.0, step=0.1, value=st.session_state.xg_local_auto)
    xg_c_l = st.number_input("xG en Contra (Local)", min_value=0.0, step=0.1, value=st.session_state.xga_local_auto)

with col_vis:
    st.subheader("✈️ Equipo Visita")
    xg_f_v = st.number_input("xG a Favor (Visita)", min_value=0.0, step=0.1, value=st.session_state.xg_visita_auto)
    xg_c_v = st.number_input("xG en Contra (Visita)", min_value=0.0, step=0.1, value=st.session_state.xga_visita_auto)

st.header("2. Ingresar Datos de Córners")
col_cor_l, col_cor_v = st.columns(2)
with col_cor_l:
    cor_f_l = st.number_input("Córners a Favor (Local)", min_value=0.0, step=0.5, value=5.5)
with col_cor_v:
    cor_f_v = st.number_input("Córners a Favor (Visita)", min_value=0.0, step=0.5, value=4.8)

st.header("3. Cuotas de la Casa de Apuestas")
st.subheader("Mercado Principal (1X2)")
col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    cuota_l = st.number_input("Cuota Local", min_value=1.00, step=0.01, value=1.83)
with col_c2:
    cuota_e = st.number_input("Cuota Empate", min_value=1.00, step=0.01, value=4.10)
with col_c3:
    cuota_v = st.number_input("Cuota Visita", min_value=1.00, step=0.01, value=3.90)

st.subheader("Mercados de Goles")
col_g1, col_g2, col_g3 = st.columns(3)
with col_g1:
    cuota_btts_si = st.number_input("Ambos Anotan (Sí)", min_value=1.00, step=0.01, value=1.80)
    cuota_btts_no = st.number_input("Ambos Anotan (No)", min_value=1.00, step=0.01, value=1.95)
with col_g2:
    cuota_o15 = st.number_input("Más de 1.5 Goles", min_value=1.00, step=0.01, value=1.25)
    cuota_u15 = st.number_input("Menos de 1.5 Goles", min_value=1.00, step=0.01, value=3.50)
with col_g3:
    cuota_o25 = st.number_input("Más de 2.5 Goles", min_value=1.00, step=0.01, value=1.75)
    cuota_u25 = st.number_input("Menos de 2.5 Goles", min_value=1.00, step=0.01, value=2.05)

st.subheader("Mercados de Córners")
col_cor1, col_cor2, col_cor3 = st.columns(3)
with col_cor1:
    linea_corners = st.number_input("Línea de Córners (Ej. 9.5)", min_value=0.5, step=0.5, value=9.5)
with col_cor2:
    cuota_o_cor = st.number_input("Más Córners", min_value=1.00, step=0.01, value=1.85)
with col_cor3:
    cuota_u_cor = st.number_input("Menos Córners", min_value=1.00, step=0.01, value=1.85)

st.header("4. Gestión de Bankroll")
col_b1, col_b2 = st.columns(2)
with col_b1:
    bankroll = st.number_input("Bankroll Total (S/)", min_value=1.0, step=10.0, value=100.0)
with col_b2:
    fraccion_kelly = st.slider("Fracción de Kelly", 0.1, 1.0, 0.25, 0.05, help="0.25 recomendado para seguridad.")

if st.button("🚀 CALCULAR PRONÓSTICO", use_container_width=True, type="primary"):
    # Cálculos Goles
    xg_local_proyectado = (xg_f_l + xg_c_v) / 2
    xg_visita_proyectado = (xg_f_v + xg_c_l) / 2
    
    # Cálculos Córners
    cor_local_proyectado = cor_f_l
    cor_visita_proyectado = cor_f_v
    total_corners_proyectado = cor_local_proyectado + cor_visita_proyectado
    
    st.markdown("---")
    st.subheader("📊 Análisis del Partido y la Casa de Apuestas")
    
    # Overround 1X2
    margen_casa = (1 / cuota_l + 1 / cuota_e + 1 / cuota_v) - 1
    
    col_inf1, col_inf2 = st.columns(2)
    with col_inf1:
        st.info(f"**Goles Esperados (xG):** Local {xg_local_proyectado:.2f} | Visita {xg_visita_proyectado:.2f}\n*(Ajuste Dixon-Coles aplicado para empates)*")
        st.info(f"**Córners Proyectados:** L. {cor_local_proyectado:.2f} | V. {cor_visita_proyectado:.2f} | T. {total_corners_proyectado:.2f}")
    with col_inf2:
        if margen_casa > 0.08:
            st.error(f"💀 **Margen de la Casa:** {margen_casa*100:.1f}%\nMercado con mucha comisión, difícil hallar rentabilidad.")
        elif margen_casa > 0.05:
            st.warning(f"⚠️ **Margen de la Casa:** {margen_casa*100:.1f}%\nComisión moderada, apuesta con cautela.")
        else:
            st.success(f"✅ **Margen de la Casa:** {margen_casa*100:.1f}%\nBuena línea, baja comisión de la casa.")
    
    # Poisson Goles
    prob_local, prob_empate, prob_visita = calcular_poisson_partido(xg_local_proyectado, xg_visita_proyectado)

    # Kelly Principal
    apuesta_l, c_justa_l, vent_l = calcular_kelly(prob_local, cuota_l, bankroll, fraccion_kelly)
    apuesta_v, c_justa_v, vent_v = calcular_kelly(prob_visita, cuota_v, bankroll, fraccion_kelly)
    c_justa_e = 1/prob_empate if prob_empate > 0 else float('inf')

    # Simulacion Mercados Secundarios (Goles)
    prob_btts_si, prob_btts_no, prob_o15, prob_u15, prob_o25, prob_u25 = obtener_simulacion_monte_carlo(xg_local_proyectado, xg_visita_proyectado)
    
    # Probabilidades Córners
    prob_u_cor = poisson.cdf(math.floor(linea_corners), total_corners_proyectado)
    prob_o_cor = 1 - prob_u_cor

    # Kelly Secundarios
    ap_btts_si, cj_btts_si, v_btts_si = calcular_kelly(prob_btts_si, cuota_btts_si, bankroll, fraccion_kelly)
    ap_btts_no, cj_btts_no, v_btts_no = calcular_kelly(prob_btts_no, cuota_btts_no, bankroll, fraccion_kelly)
    
    ap_o15, cj_o15, v_o15 = calcular_kelly(prob_o15, cuota_o15, bankroll, fraccion_kelly)
    ap_u15, cj_u15, v_u15 = calcular_kelly(prob_u15, cuota_u15, bankroll, fraccion_kelly)
    
    ap_o25, cj_o25, v_o25 = calcular_kelly(prob_o25, cuota_o25, bankroll, fraccion_kelly)
    ap_u25, cj_u25, v_u25 = calcular_kelly(prob_u25, cuota_u25, bankroll, fraccion_kelly)
    
    ap_o_cor, cj_o_cor, v_o_cor = calcular_kelly(prob_o_cor, cuota_o_cor, bankroll, fraccion_kelly)
    ap_u_cor, cj_u_cor, v_u_cor = calcular_kelly(prob_u_cor, cuota_u_cor, bankroll, fraccion_kelly)

    st.subheader("📈 Mercado Principal (1X2)")
    st.markdown(f'''
    | Selección | Prob. Real | Cuota Justa | Cuota Casa | Valor (Ventaja) | Apuesta Sugerida |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | **Local** | {prob_local*100:.1f}% | {c_justa_l:.2f} | {cuota_l:.2f} | {vent_l:.1f}% | S/ {apuesta_l:.2f} |
    | **Visita** | {prob_visita*100:.1f}% | {c_justa_v:.2f} | {cuota_v:.2f} | {vent_v:.1f}% | S/ {apuesta_v:.2f} |
    | **Empate** | {prob_empate*100:.1f}% | {c_justa_e:.2f} | {cuota_e:.2f} | - | - |
    ''')

    st.subheader("⚽ Mercados de Goles")
    st.markdown(f'''
    | Selección | Prob. Real | Cuota Justa | Cuota Casa | Valor (Ventaja) | Apuesta Sugerida |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | **Ambos Anotan (Sí)** | {prob_btts_si*100:.1f}% | {cj_btts_si:.2f} | {cuota_btts_si:.2f} | {v_btts_si:.1f}% | S/ {ap_btts_si:.2f} |
    | **Ambos Anotan (No)** | {prob_btts_no*100:.1f}% | {cj_btts_no:.2f} | {cuota_btts_no:.2f} | {v_btts_no:.1f}% | S/ {ap_btts_no:.2f} |
    | **Más de 1.5** | {prob_o15*100:.1f}% | {cj_o15:.2f} | {cuota_o15:.2f} | {v_o15:.1f}% | S/ {ap_o15:.2f} |
    | **Menos de 1.5** | {prob_u15*100:.1f}% | {cj_u15:.2f} | {cuota_u15:.2f} | {v_u15:.1f}% | S/ {ap_u15:.2f} |
    | **Más de 2.5** | {prob_o25*100:.1f}% | {cj_o25:.2f} | {cuota_o25:.2f} | {v_o25:.1f}% | S/ {ap_o25:.2f} |
    | **Menos de 2.5** | {prob_u25*100:.1f}% | {cj_u25:.2f} | {cuota_u25:.2f} | {v_u25:.1f}% | S/ {ap_u25:.2f} |
    ''')

    st.subheader("🚩 Mercados de Córners")
    st.markdown(f'''
    | Selección | Prob. Real | Cuota Justa | Cuota Casa | Valor (Ventaja) | Apuesta Sugerida |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | **Más de {linea_corners}** | {prob_o_cor*100:.1f}% | {cj_o_cor:.2f} | {cuota_o_cor:.2f} | {v_o_cor:.1f}% | S/ {ap_o_cor:.2f} |
    | **Menos de {linea_corners}** | {prob_u_cor*100:.1f}% | {cj_u_cor:.2f} | {cuota_u_cor:.2f} | {v_u_cor:.1f}% | S/ {ap_u_cor:.2f} |
    ''')

    st.markdown("---")
    st.subheader("📊 Gráfico Comparativo: Cuota Justa vs Casa de Apuestas")
    # Generar comparativa para el mercado Principal
    df_chart = pd.DataFrame({
        "Mercado": ["Local", "Visita", "Empate"],
        "Cuota Justa (Real)": [c_justa_l, c_justa_v, c_justa_e],
        "Cuota Casa": [cuota_l, cuota_v, cuota_e]
    })
    
    # Prevenir que la cuota de empate distorsione el gráfico si es muy alta
    if c_justa_e > 20: df_chart.loc[2, "Cuota Justa (Real)"] = 20
    
    fig = go.Figure(data=[
        go.Bar(name='Cuota Justa (Nuestro Modelo)', x=df_chart['Mercado'], y=df_chart['Cuota Justa (Real)'], marker_color='#1f77b4'),
        go.Bar(name='Cuota de la Casa', x=df_chart['Mercado'], y=df_chart['Cuota Casa'], marker_color='#ff7f0e')
    ])
    fig.update_layout(barmode='group', title="Comparativa 1X2 (Las cuotas de la casa DEBEN ser mayores a nuestra cuota justa)")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("💡 Recomendaciones Destacadas")
    
    apuestas = [
        {"desc": "Local", "vent": vent_l, "apuesta": apuesta_l},
        {"desc": "Visita", "vent": vent_v, "apuesta": apuesta_v},
        {"desc": "Ambos Anotan (Sí)", "vent": v_btts_si, "apuesta": ap_btts_si},
        {"desc": "Ambos Anotan (No)", "vent": v_btts_no, "apuesta": ap_btts_no},
        {"desc": "Más de 1.5 Goles", "vent": v_o15, "apuesta": ap_o15},
        {"desc": "Menos de 1.5 Goles", "vent": v_u15, "apuesta": ap_u15},
        {"desc": "Más de 2.5 Goles", "vent": v_o25, "apuesta": ap_o25},
        {"desc": "Menos de 2.5 Goles", "vent": v_u25, "apuesta": ap_u25},
        {"desc": f"Más de {linea_corners} Córners", "vent": v_o_cor, "apuesta": ap_o_cor},
        {"desc": f"Menos de {linea_corners} Córners", "vent": v_u_cor, "apuesta": ap_u_cor},
    ]

    recomendaciones = [ap for ap in apuestas if ap["vent"] > 0 and ap["apuesta"] > 0]
    
    if not recomendaciones:
        st.warning("No hay valor en ninguno de los mercados analizados. No arriesgar dinero.")
    else:
        # Ordenar por ventaja (mayor a menor)
        recomendaciones.sort(key=lambda x: x["vent"], reverse=True)
        for rec in recomendaciones:
            st.success(f"🔥 **{rec['desc']}**: Apostar S/ {rec['apuesta']:.2f} (Ventaja: {rec['vent']:.1f}%)")
            # Añadir al historial si no existe
            st.session_state.historial.append(rec)
            
        if any(rec["vent"] > 50 for rec in recomendaciones):
            st.error("⚠️ RIESGO EXTREMO: Hay ventajas anómalas (>50%). Revisa bien los datos ingresados o posibles lesiones.")

if len(st.session_state.historial) > 0:
    st.markdown("---")
    st.header("🛒 Tu Historial de Apuestas Sugeridas")
    df_historial = pd.DataFrame(st.session_state.historial)
    df_historial.columns = ['Mercado', 'Ventaja (%)', 'Apuesta (S/)']
    st.dataframe(df_historial, use_container_width=True)
    
    csv = df_historial.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Reporte Completo (CSV)",
        data=csv,
        file_name='reporte_apuestas_kelly.csv',
        mime='text/csv',
    )
    
    if st.button("🗑️ Limpiar Historial"):
        st.session_state.historial = []
        st.rerun()
