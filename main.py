import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsbombpy import sb
from mplsoccer import Pitch
import warnings

warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(page_title="StatsBomb - Análisis de Pases", layout="wide")
st.title("⚽ Visualizador de Pases - FIFA World Cup 2022")

# Carga de datos con caché para optimizar Streamlit Cloud
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

# Cargar eventos del partido seleccionado (Match ID: 3857255 - Japón)
with st.spinner("Cargando datos del partido..."):
    final = load_match_events(3857255)

st.success("¡Datos cargados correctamente!")

# Sección de vista previa de datos
if st.checkbox("Mostrar tabla de datos de pases"):
    st.dataframe(final.head(10))

# Control interactivo con barra deslizante en Streamlit
max_min = int(final['minute'].max())
minuto = st.slider("Selecciona el minuto del partido:", min_value=0, max_value=max_min, value=0)

# Renderizado de la gráfica en Streamlit
fig, ax = plt.subplots(figsize=(10, 7))
pitch = Pitch(pitch_color='grass', line_color='white', stripe=True)
pitch.draw(ax=ax)

# Filtrar por el minuto seleccionado
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
