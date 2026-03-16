import math
from scipy.stats import poisson
import numpy as np

def calcular_cuotas_justas(xg_local, xg_visitante, max_goles=5):
    """
    xg_local: Goles esperados del equipo local (Ej. 1.8)
    xg_visitante: Goles esperados del equipo visitante (Ej. 1.2)
    max_goles: Límite de goles a calcular para la matriz (por defecto 5)
    """
    prob_local_gana = 0
    prob_empate = 0
    prob_visitante_gana = 0

    print(f"--- ANÁLISIS DEL PARTIDO ---")
    print(f"xG Local: {xg_local} | xG Visitante: {xg_visitante}\n")

    # Generamos una matriz cruzando los posibles goles de ambos equipos
    for goles_local in range(max_goles + 1):
        for goles_visitante in range(max_goles + 1):
            
            # Calculamos la probabilidad de este marcador exacto
            prob_marcador = poisson.pmf(goles_local, xg_local) * poisson.pmf(goles_visitante, xg_visitante)
            
            # Sumamos a la probabilidad general según quién gane el partido
            if goles_local > goles_visitante:
                prob_local_gana += prob_marcador
            elif goles_local == goles_visitante:
                prob_empate += prob_marcador
            else:
                prob_visitante_gana += prob_marcador

    # Mostramos las probabilidades en porcentaje
    print(f"Probabilidad Local Gana:  {prob_local_gana * 100:.2f}%")
    print(f"Probabilidad Empate:      {prob_empate * 100:.2f}%")
    print(f"Probabilidad Visita Gana: {prob_visitante_gana * 100:.2f}%\n")

    # Convertimos esas probabilidades en "Cuotas Justas" (1 / Probabilidad)
    cuota_local = 1 / prob_local_gana
    cuota_empate = 1 / prob_empate
    cuota_visita = 1 / prob_visitante_gana

    print("--- CUOTAS JUSTAS (Lo mínimo que deberías aceptar) ---")
    print(f"Cuota Local: {cuota_local:.2f}")
    print(f"Cuota Empate: {cuota_empate:.2f}")
    print(f"Cuota Visita: {cuota_visita:.2f}")

def simulacion_monte_carlo_extendida(xg_local, xg_visita, num_simulaciones=10000):
    """
    Simula miles de partidos usando la distribución de Poisson para encontrar 
    la probabilidad de diferentes mercados secundarios (extendido para la app).
    """
    goles_local = np.random.poisson(xg_local, num_simulaciones)
    goles_visita = np.random.poisson(xg_visita, num_simulaciones)
    
    ambos_marcan = np.sum((goles_local > 0) & (goles_visita > 0)) / num_simulaciones
    ambos_no_marcan = 1 - ambos_marcan
    
    over_1_5 = np.sum((goles_local + goles_visita) > 1.5) / num_simulaciones
    under_1_5 = 1 - over_1_5
    
    over_2_5 = np.sum((goles_local + goles_visita) > 2.5) / num_simulaciones
    under_2_5 = 1 - over_2_5
    
    return ambos_marcan, ambos_no_marcan, over_1_5, under_1_5, over_2_5, under_2_5

def calcular_kelly(probabilidad, cuota_casa, bankroll, fraccion_kelly):
    if probabilidad <= 0 or cuota_casa <= 1.0: 
        return 0.0, float('inf'), 0.0
    q = 1 - probabilidad
    b = cuota_casa - 1
    c_justa = 1 / probabilidad
    kelly = ((b * probabilidad) - q) / b
    apuesta = max(0, bankroll * kelly * fraccion_kelly)
    ventaja = (cuota_casa / c_justa - 1) * 100
    return apuesta, c_justa, ventaja

def calcular_poisson_partido(xg_local_proyectado, xg_visita_proyectado, max_goles=7, rho=0.15):
    prob_local = 0
    prob_visita = 0
    prob_empate = 0
    
    for g_l in range(max_goles):
        for g_v in range(max_goles):
            prob = poisson.pmf(g_l, xg_local_proyectado) * poisson.pmf(g_v, xg_visita_proyectado)
            
            # Ajuste de Dixon-Coles para empates/marcadores bajos
            if g_l == 0 and g_v == 0:
                prob *= max(0, 1 - xg_local_proyectado * xg_visita_proyectado * rho)
            elif g_l == 0 and g_v == 1:
                prob *= max(0, 1 + xg_local_proyectado * rho)
            elif g_l == 1 and g_v == 0:
                prob *= max(0, 1 + xg_visita_proyectado * rho)
            elif g_l == 1 and g_v == 1:
                prob *= max(0, 1 - rho)
                
            if g_l > g_v: prob_local += prob
            elif g_v > g_l: prob_visita += prob
            else: prob_empate += prob

    # Normalización para sumar siempre 1
    total_prob = prob_local + prob_visita + prob_empate
    if total_prob > 0:
        prob_local /= total_prob
        prob_visita /= total_prob
        prob_empate /= total_prob
        
    return prob_local, prob_empate, prob_visita
def calculadora_profesional(xg_favor_local, xg_contra_local, xg_favor_visita, xg_contra_visita, cuota_casa_local, cuota_casa_empate, cuota_casa_visita, bankroll, fraccion_kelly=0.25):
    # 0. Cálculo de xG Proyectado (Promediando ataque de uno y defensa de otro)
    xg_local_proyectado = (xg_favor_local + xg_contra_visita) / 2
    xg_visita_proyectado = (xg_favor_visita + xg_contra_local) / 2
    
    # 1. Cálculo de Probabilidades (Poisson)
    prob_local_gana = 0
    prob_visita_gana = 0
    prob_empate = 0
    max_goles = 7 # Aumentamos a 7 para mayor precisión en partidos de muchos goles
    
    for g_l in range(max_goles):
        for g_v in range(max_goles):
            prob_marcador = poisson.pmf(g_l, xg_local_proyectado) * poisson.pmf(g_v, xg_visita_proyectado)
            if g_l > g_v:
                prob_local_gana += prob_marcador
            elif g_v > g_l:
                prob_visita_gana += prob_marcador
            else:
                prob_empate += prob_marcador

    # 2. Función interna para calcular Kelly y Valor
    def analizar_lado(nombre, p, cuota_casa):
        q = 1 - p
        b = cuota_casa - 1
        cuota_justa = 1 / p
        kelly_full = ((b * p) - q) / b
        apuesta = max(0, bankroll * kelly_full * fraccion_kelly)
        ventaja = (cuota_casa / cuota_justa - 1) * 100
        return cuota_justa, ventaja, apuesta

    # Analizamos ambos lados
    c_justa_l, vent_l, apuesta_l = analizar_lado("LOCAL", prob_local_gana, cuota_casa_local)
    c_justa_v, vent_v, apuesta_v = analizar_lado("VISITA", prob_visita_gana, cuota_casa_visita)

    # 3. Reporte de Resultados
    print("="*45)
    print("ANÁLISIS DE GOLES PROYECTADOS (xG)")
    print(f"-> xG Esperado Local:  {xg_local_proyectado:.2f} goles")
    print(f"-> xG Esperado Visita: {xg_visita_proyectado:.2f} goles")
    print("="*45)
    print(f"{'MERCADO':<10} | {'PROB':<7} | {'C.JUSTA':<8} | {'C.CASA':<7} | {'VALOR'}")
    print("-"*45)
    print(f"{'LOCAL':<10} | {prob_local_gana*100:>6.2f}% | {c_justa_l:>8.2f} | {cuota_casa_local:>7.2f} | {vent_l:>6.2f}%")
    print(f"{'VISITA':<10} | {prob_visita_gana*100:>6.2f}% | {c_justa_v:>8.2f} | {cuota_casa_visita:>7.2f} | {vent_v:>6.2f}%")
    c_justa_e = 1 / prob_empate if prob_empate > 0 else float('inf')
    margen_casa = (1 / cuota_casa_local + 1 / cuota_casa_empate + 1 / cuota_casa_visita) * 100 - 100

    print(f"{'EMPATE':<10} | {prob_empate*100:>6.2f}% | {c_justa_e:>8.2f} | {cuota_casa_empate:>7.2f} | {'-'}")
    print("-" * 45)
    print(f"MARGEN DE LA CASA (Overround): {margen_casa:.2f}%")
    print("="*45)

    print(f"RECOMENDACIÓN (Bankroll: S/ {bankroll}):")
    # Alerta de seguridad para diferencias grandes (>50%)
    if vent_l > 50 or vent_v > 50:
        print("!!! RIESGO EXTREMO: La diferencia entre la cuota justa y la de la casa es anómala.")
        print("    -> Revisar posibles lesiones de última hora, rotaciones o motivación del equipo.")
        
    if vent_l > 0:
        print(f"-> LOCAL:  Apostar S/ {apuesta_l:.2f}")
    if vent_v > 0:
        print(f"-> VISITA: Apostar S/ {apuesta_v:.2f}")
    if vent_l <= 0 and vent_v <= 0:
        print("-> NO HAY VALOR EN ESTE PARTIDO. No arriesgar dinero.")
    print("="*45)

    # 4. Simulación de Monte Carlo (10,000 partidos)
    print("INICIANDO SIMULACIÓN DE MONTE CARLO (10,000 Partidos)...")
    prob_btts, prob_o15, prob_o25 = simulacion_monte_carlo(xg_local_proyectado, xg_visita_proyectado)
    
    print("="*45)
    print("MERCADOS SECUNDARIOS (Probabilidad Real vs Cuota Mínima)")
    print("-"*45)
    print(f"Ambos Marcan (BTTS) : {prob_btts*100:>6.2f}% | Cuota Min: {1/prob_btts if prob_btts > 0 else float('inf'):.2f}")
    print(f"Más de 1.5 Goles    : {prob_o15*100:>6.2f}% | Cuota Min: {1/prob_o15 if prob_o15 > 0 else float('inf'):.2f}")
    print(f"Más de 2.5 Goles    : {prob_o25*100:>6.2f}% | Cuota Min: {1/prob_o25 if prob_o25 > 0 else float('inf'):.2f}")
    print("="*45)

# Ejemplo práctico: Un partido clásico donde el Local es ligeramente superior

#calcular_cuotas_justas(xg_local=0.93, xg_visitante=1.45)

# --- CONFIGURACIÓN DE TU PARTIDO ---
calculadora_profesional(
    xg_favor_local=1.96,     # Cuánto ataca el local
    xg_contra_local=1.35,    # Cuánto le marcan al local

    xg_favor_visita=1.52,    # Cuánto ataca la visita
    xg_contra_visita=1.24,   # Cuánto le marcan a la visita

    cuota_casa_local=1.83, 
    cuota_casa_empate=4.10,
    cuota_casa_visita=3.90,

    bankroll=2.50,        # Tu dinero total disponible
    fraccion_kelly=0.25   # Recomendado: 0.25 para seguridad
)
