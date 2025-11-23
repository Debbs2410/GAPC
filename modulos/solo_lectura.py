import streamlit as st

def es_administradora():
    """Devuelve True si el usuario actual es administradora (solo lectura)."""
    usuario = st.session_state.get("usuario")
    if not usuario:
        return False
    rol = (usuario.get("rol") or usuario.get("Rol") or "").strip().lower()
    return rol == "administradora"
