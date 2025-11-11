import streamlit as st
from modulos.login import login
from modulos.panel import mostrar_panel

st.set_page_config(page_title="Cooperativa GAPC", layout="wide")

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    login()
else:
    mostrar_panel()
