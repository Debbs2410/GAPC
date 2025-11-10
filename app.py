import streamlit as st
from modulos.login import login
from modulos.registro import registrar_usuario
from modulos.panel import panel

st.set_page_config(page_title="Cooperativa", layout="centered")

if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False

menu = st.sidebar.selectbox("Menú", ["Iniciar sesión", "Registrar usuario"])

if not st.session_state["sesion_iniciada"]:
    if menu == "Iniciar sesión":
        login()
    else:
        registrar_usuario()
else:
    panel()
