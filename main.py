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

# 1. Cargar ediciones de la Copa del Mundo
@st.cache_data
def load_world_cups():
    competitions = sb.competitions()
    wc_editions = competitions[
        (competitions['competition_name'] == 'FIFA World Cup')
    ].copy()
    wc_editions['edition_label'] = wc_editions['season_name'] + " (" + wc_editions['competition_gender'] + ")"
    return wc_editions.sort_values(by='season_name', ascending=False)

# 2. Cargar todos los partidos de una edición (CORREGIDO)
@st.cache_data
def load_matches(comp_id, season_id):
    matches = sb.matches(competition_id=comp_id, season_id=season_id)
    
    # Manejar nombres de columnas de StatsBomb
    stage_col = 'competition_stage' if 'competition_stage' in matches.columns else 'stage'
    matches['stage_display'] = matches[stage_col]
    
    matches['match_label'] = (
        matches['home_team'] + " vs " + 
        matches['away_team'] + " (" + 
        matches['home_score'].fillna(0).astype(int).astype(str) + "-" + 
        matches['away_score'].fillna(0).astype(int).astype(str) + ")"
    )
    
    # Detectar empate
    matches['is_draw'] = matches['home_score'] == matches['away_score']
    return matches.sort_values(by='match_date')

# 3. Cargar eventos de pases
@st.cache_data
def load_match_events(match_id):
    events = sb.events(match_id=match_id)
    
    variables = ['minute', 'second', 'period', 'location', 'pass_end_location',
                 'player', 'pass_recipient', 'team', 'type']
    
    # Verificar columnas existentes
    available_vars = [col for col in variables if col in events.columns]
    passes = events[available_vars]
    
    final = passes[passes['type'] == 'Pass'].copy()
    final.reset_index(drop=True, inplace=True)
    
    final['x0'] = final.location.apply(lambda x: x[0] if isinstance(x, list) else np.nan)
    final['y0'] = final.location.apply(lambda x: x[1] if isinstance(x, list) else np.nan)
    final['x1'] = final.pass_end_location.apply(lambda x: x[0] if isinstance(x, list) else np.nan)
    final['y1'] = final.pass_end_location.apply(lambda x: x[1] if isinstance(x, list) else np.nan)
    final.drop(columns=['location', 'pass_end_location'], inplace=True, errors='ignore')
    
    return final

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros de Selección")

world_cups = load_world_cups()
selected_wc_label = st.sidebar.selectbox(
    "1. Edición del Mundial:",
    options=world_cups['edition_label'].tolist()
)

selected_wc_row = world_cups[world_cups['edition_label'] == selected_wc_label].iloc[0]
comp_id = selected_wc_row['competition_id']
season_id = selected_wc_row['season_id']

raw_matches = load_matches(comp_id, season_id)

# 2. Etapa del torneo (Usando la columna corregida)
available_stages = ["Todas las etapas"] + sorted(raw_matches['stage_display'].dropna().unique().tolist())
selected_stage = st.sidebar.selectbox(
    "2. Etapa del Torneo:",
    options=available_stages
)

# 3. Filtro de Empates
draw_option = st.sidebar.selectbox(
    "3. Resultado del Partido:",
    options=["Todos los partidos", "Solo empatados", "Solo no empatados (Victorias)"]
)

# --- FILTRADO EN CASCADA ---
filtered_matches = raw_matches.copy()

if selected_stage != "Todas las etapas":
    filtered_matches = filtered_matches[filtered_matches['stage_display'] == selected_stage]

if draw_option == "Solo empatados":
    filtered_matches = filtered_matches[filtered_matches['is_draw'] == True]
elif draw_option == "Solo no empatados (Victorias)":
    filtered_matches = filtered_matches[filtered_matches['is_draw'] == False]

# 4. Selector de Partido
if not filtered_matches.empty:
    selected_match_label = st.sidebar.selectbox(
        "4. Selecciona el partido:",
        options=filtered_matches['match_label'].tolist()
    )

    selected_match_id = filtered_matches[filtered_matches['match_label'] == selected_match_label]['match_id'].values[0]

    st.subheader(f"Mundial {selected_wc_label} — {selected_match_label}")

    with st.spinner("Cargando pases del partido..."):
        final = load_match_events(selected_match_id)

    if st.checkbox("Mostrar datos de pases en tabla"):
        st.dataframe(final.head(10))

    max_min = int(final['minute'].max()) if not final.empty else 90
    minuto = st.slider("Selecciona el minuto del partido:", min_value=0, max_value=max_min, value=0)

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
else:
    st.warning("No hay partidos que coincidan con la combinación de filtros seleccionada.")
