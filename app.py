import streamlit as st
from modulos.login import login
from modulos.panel import mostrar_panel
# --- EN EL ARCHIVO app.py ---

import sys
import os

# Obtiene la ruta del directorio de trabajo actual donde se encuentra app.py
current_dir = os.path.dirname(os.path.abspath(__file__))

# Agrega la carpeta 'modulos' al camino de búsqueda de Python
# ESTA LÍNEA DEBE RESOLVER EL ERROR DE IMPORTACIÓN
sys.path.append(os.path.join(current_dir, 'modulos'))

# ... El resto de tu código de app.py ...

st.set_page_config(page_title="Cooperativa GAPC", layout="wide")

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    login()
else:
    mostrar_panel()
