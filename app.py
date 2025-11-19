import streamlit as st
from modulos.panel import mostrar_panel
def login():
    pass
# Lógica de flujo de la aplicación
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    from modulos.login import login
    login()
else:
    # Esta es la línea que fallaba y ahora debe funcionar
    mostrar_panel()
