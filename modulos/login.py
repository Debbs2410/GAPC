import streamlit as st
from modulos.config.conexion import obtener_conexion
import hashlib

def login():
    st.subheader("Inicio de sesión")

    correo = st.text_input("Correo electrónico")
    contrasena = st.text_input("Contraseña", type="password")

    if st.button("Iniciar sesión"):
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor(dictionary=True)
            contrasena_hash = hashlib.sha256(contrasena.encode()).hexdigest()

            cursor.execute("SELECT * FROM usuarios WHERE correo=%s AND contrasena=%s", (correo, contrasena_hash))
            usuario = cursor.fetchone()

            if usuario:
                st.session_state["usuario"] = usuario
                st.session_state["sesion_iniciada"] = True
                st.success(f"Bienvenido, {usuario['nombre']} ({usuario['rol']})")
                st.experimental_rerun()
            else:
                st.error("Correo o contraseña incorrectos.")

