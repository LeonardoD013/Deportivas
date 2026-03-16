import requests, io
import pandas as pd
import streamlit as st

# football-data.co.uk libera CSVs con resultados de cada liga.
# Campos clave: HomeTeam, AwayTeam, FTHG (goles local), FTAG (goles visita)
# Usaremos el promedio de goles como estimador de xG cuando no hay fuente de xG disponible.

_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/123.0.0.0'}

LIGAS_DISPONIBLES = {
    "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿": "https://www.football-data.co.uk/mmz4281/2425/E0.csv",
    "La Liga 🇪🇸":              "https://www.football-data.co.uk/mmz4281/2425/SP1.csv",
    "Serie A 🇮🇹":              "https://www.football-data.co.uk/mmz4281/2425/I1.csv",
    "Bundesliga 🇩🇪":           "https://www.football-data.co.uk/mmz4281/2425/D1.csv",
    "Ligue 1 🇫🇷":              "https://www.football-data.co.uk/mmz4281/2425/F1.csv",
}

@st.cache_data(ttl=3600, show_spinner=False)  # refresco cada hora
def obtener_datos_liga_fbref(url_liga: str) -> pd.DataFrame | None:
    """
    Descarga un CSV de resultados desde football-data.co.uk y calcula
    el promedio de goles a favor (xG proxy) y en contra (xGA proxy)
    por partido para cada equipo.
    Retorna DataFrame con columnas: Equipo, xG_Favor_Avg, xG_Contra_Avg
    """
    try:
        resp = requests.get(url_liga, headers=_HEADERS, timeout=15)
        resp.raise_for_status()

        # Detectar encoding del CSV (a veces latin-1)
        try:
            df_raw = pd.read_csv(io.StringIO(resp.content.decode('utf-8')))
        except UnicodeDecodeError:
            df_raw = pd.read_csv(io.StringIO(resp.content.decode('latin-1')))

        # Columnas requeridas
        for col in ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']:
            if col not in df_raw.columns:
                return None

        df_raw = df_raw.dropna(subset=['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG'])

        equipos = sorted(set(df_raw['HomeTeam'].tolist() + df_raw['AwayTeam'].tolist()))

        rows = []
        for equipo in equipos:
            como_local   = df_raw[df_raw['HomeTeam'] == equipo]
            como_visita  = df_raw[df_raw['AwayTeam']  == equipo]

            total_goles_fav  = como_local['FTHG'].sum()  + como_visita['FTAG'].sum()
            total_goles_con  = como_local['FTAG'].sum()  + como_visita['FTHG'].sum()
            total_partidos   = len(como_local) + len(como_visita)

            if total_partidos == 0:
                continue

            rows.append({
                'Equipo':          equipo,
                'xG_Favor_Avg':    round(total_goles_fav  / total_partidos, 2),
                'xG_Contra_Avg':   round(total_goles_con  / total_partidos, 2),
            })

        return pd.DataFrame(rows).sort_values('Equipo').reset_index(drop=True) or None

    except Exception as e:
        print(f"[data_scraper] Error: {e}")
        return None
