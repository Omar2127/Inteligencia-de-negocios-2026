import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsbombpy import sb
from mplsoccer import Pitch
import warnings

warnings.filterwarnings('ignore')

st.set_page_config(page_title="StatsBomb - Visualizador de Pases", layout="wide")
st.title("⚽ Visualizador de Pases por Copa del Mundo")

# 1. Cargar todas las ediciones de la Copa del Mundo disponibles
@st.cache_data
def load_world_cups():
    competitions = sb.competitions()
    # Filtrar únicamente los torneos masculinos de la FIFA World Cup
    wc_editions = competitions[
        (competitions['competition_name'] == 'FIFA World Cup')
    ].copy()
    
    # Crear etiqueta legible para el selector (ej. "2022 - Qatar")
    wc_editions['edition_label'] = wc_editions['season_name'] + " (" + wc_editions['competition_gender'] + ")"
    return wc_editions.sort_values(by='season_name', ascending=False)

# 2. Cargar partidos según el competition_id y season_id seleccionados
@st.cache_data
def load_matches(comp_id, season_id):
    matches = sb.matches(competition_id=comp_id, season_id=season_id)
    matches['match_label'] = (
        matches['home_team'] + " vs " + 
        matches['away_team'] + " (" + 
        matches['home_score'].astype(str) + "-" + 
        matches['away_score'].astype(str) + ")"
    )
    return matches.sort_values(by='match_date')

# 3. Cargar eventos de pases del partido seleccionado
@st.cache_data
def load_match_events(match_id):
    events = sb.events(match_id=match_id)
    
    variables = ['minute', 'second', 'period', 'location', 'pass_end_location',
                 'player', 'pass_recipient', 'team', 'type']
    
    passes = events[variables]
    final = passes[passes['type'] == 'Pass'].copy()
    final.reset_index(drop=True, inplace=True)
    
    # Transformación de coordenadas
    final['x0'] = final.location.apply(lambda x: x[0])
    final['y0'] = final.location.apply(lambda x: x[1])
    final['x1'] = final.pass_end_location.apply(lambda x: x[0])
    final['y1'] = final.pass_end_location.apply(lambda x: x[1])
    final.drop(columns=['location', 'pass_end_location'], inplace=True)
    
    return final

# --- BARRA LATERAL (CONTROLES) ---
st.sidebar.header("Filtros de Selección")

# Cargar ediciones disponibles del Mundial
world_cups = load_world_cups()

# Menú desplegable 1: Edición del Mundial
selected_wc_label = st.sidebar.selectbox(
    "1. Selecciona la edición del Mundial:",
    options=world_cups['edition_label'].tolist()
)

# Obtener IDs de la edición elegida
selected_wc_row = world_cups[world_cups['edition_label'] == selected_wc_label].iloc[0]
comp_id = selected_wc_row['competition_id']
season_id = selected_wc_row['season_id']

# Cargar partidos de la edición elegida
matches = load_matches(comp_id, season_id)

# Menú desplegable 2: Partido
selected_match_label = st.sidebar.selectbox(
    "2. Selecciona el partido:",
    options=matches['match_label'].tolist()
)

# Obtener ID del partido seleccionado
selected_match_id = matches[matches['match_label'] == selected_match_label]['match_id'].values[0]

# --- VISTA PRINCIPAL ---
st.subheader(f"Mundial {selected_wc_label} — {selected_match_label}")

# Cargar eventos del partido
with st.spinner("Cargando pases del partido..."):
    final = load_match_events(selected_match_id)

if st.checkbox("Mostrar datos de pases en tabla"):
    st.dataframe(final.head(10))

# Control deslizante del minuto
max_min = int(final['minute'].max()) if not final.empty else 90
minuto = st.slider("Selecciona el minuto del partido:", min_value=0, max_value=max_min, value=0)

# Graficar el campo y los pases
fig, ax = plt.subplots(figsize=(10, 7))
pitch = Pitch(pitch_color='grass', line_color='white', stripe=True)
pitch.draw(ax=ax)

data_minuto = final[final.minute == minuto]

if not data_minuto.empty:
    sns.scatterplot(
        data=data_minuto, 
        x='x0', 
        y='y0', 
        ax=ax, 
        hue='team', 
        s=100
    )
    plt.legend(loc='upper center', ncol=2)
    st.pyplot(fig)
else:
    st.info(f"No hay pases registrados en el minuto {minuto}.")
