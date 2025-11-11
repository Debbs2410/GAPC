import streamlit as st
from modulos.registro_beneficiarios import registrar_beneficiario
from modulos.registro_usuarios import registrar_usuario  # 🔹 Importamos el nuevo registro de usuarios

def mostrar_panel():
    usuario = st.session_state["usuario"]
    rol = usuario["rol"]

    # --- Menú lateral ---
    st.sidebar.title("📋 Menú de navegación")
    st.sidebar.write(f"👤 {usuario['nombre']} ({rol})")

    # --- ADMINISTRADORA ---
    if rol == "Administradora":
        st.title("Panel de Administradora")
        st.sidebar.success("✅ Control total del sistema.")
        st.write("Acceso completo


