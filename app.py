import requests
import pandas as pd
from bs4 import BeautifulSoup
import streamlit as st

@st.cache_data(ttl=86400) # Cachear por 24 horas (86400 segundos) para no banear la IP
def obtener_datos_liga_fbref(url_liga):
    """
    Descarga la tabla de estadísticas avanzadas de una liga desde FBref.
    Retorna un DataFrame o None si hay error.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    
    try:
        response = requests.get(url_liga, headers=headers)
        response.raise_for_status()
        
        # Parseamos el HTML con BeautifulSoup
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Buscamos la tabla de la temporada regular
        # FBref suele tener el id "results{año}X{id_liga}_overall"
        # Para ser más genéricos buscamos la primera tabla de stats
        tablas = soup.find_all('table', {'class': 'stats_table'})
        
        if not tablas:
            return None
            
        tabla_principal = tablas[0]
        
        # Convertimos la tabla a un DataFrame de Pandas
        df = pd.read_html(str(tabla_principal))[0]
        
        # Limpieza de Pandas tras leer FBref (MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            # Aplanamos el MultiIndex de la cabecera
            df.columns = ['_'.join(col).strip() for col in df.columns.values]
            
        # Nombres de columnas mapeados (FBref usa niveles, así que "Expected_xG" suele ser el estándar, 
        # pero para asegurarnos buscamos en nombres de forma flexible)
        
        nombres_equipos = []
        xg_favor = []
        xg_contra = []
        
        for index, row in df.iterrows():
            # Buscando columnas clave (varía un poco si es MultiIndex o no)
            equipo = row.filter(regex='(?i)squad').values[0] if len(row.filter(regex='(?i)squad')) > 0 else None
            
            # Buscando expected goals
            # FBref pone "Expected_xG" y "Expected_xGA" si es MultiIndex
            col_xg = row.filter(regex='(?i)xG$').values
            col_xga = row.filter(regex='(?i)xGA').values
            
            if equipo and len(col_xg) > 0 and len(col_xga) > 0:
                nombres_equipos.append(equipo)
                xg_favor.append(float(col_xg[0]))
                xg_contra.append(float(col_xga[0]))
                
        if not nombres_equipos:
            return None
            
        df_limpio = pd.DataFrame({
            'Equipo': nombres_equipos,
            'xG_Favor': xg_favor,
            'xG_Contra': xg_contra
        })
        
        partidos_jugados = row.filter(regex='(?i)MP').values[0]
        
        # Calculamos el promedio por partido (por los general FBref muestra el acumulativo de la temporada)
        df_limpio['xG_Favor_Avg'] = round(df_limpio['xG_Favor'] / partidos_jugados, 2)
        df_limpio['xG_Contra_Avg'] = round(df_limpio['xG_Contra'] / partidos_jugados, 2)
        
        # Limpiamos prefijos extraños en los nombres si existen (ej: "1. Arsenal" -> "Arsenal", "eng Arsenal" -> "Arsenal")
        df_limpio['Equipo'] = df_limpio['Equipo'].str.replace(r'^[a-z]{2,3}\s', '', regex=True)
        df_limpio['Equipo'] = df_limpio['Equipo'].str.replace(r'^\d+\.\s', '', regex=True)
        
        return df_limpio.sort_values('Equipo').reset_index(drop=True)
        
    except Exception as e:
        print(f"Error extrayendo datos: {e}")
        return None

# URLs base de ligas principales para la temporada 2024-2025
LIGAS_DISPONIBLES = {
    "Premier League": "https://fbref.com/en/comps/9/Premier-League-Stats",
    "La Liga 🇪🇸": "https://fbref.com/en/comps/12/La-Liga-Stats",
    "Serie A 🇮🇹": "https://fbref.com/en/comps/11/Serie-A-Stats",
    "Bundesliga 🇩🇪": "https://fbref.com/en/comps/20/Bundesliga-Stats",
    "Ligue 1 🇫🇷": "https://fbref.com/en/comps/13/Ligue-1-Stats"
}
