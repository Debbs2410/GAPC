import streamlit as st
from modulos.config.conexion import obtener_conexion
# import hashlib  <-- YA NO ES NECESARIA ESTA LIBRERÍA

def login():
    st.title("🔐 Inicio de Sesión - Cooperativa GAPC")

    correo = st.text_input("Correo electrónico")
    contrasena = st.text_input("Contraseña", type="password")

    if st.button("Iniciar sesión"):
        if not correo or not contrasena:
            st.warning("Completa todos los campos.")
            return

        conexion = obtener_conexion()
        if not conexion:
            st.error("No se pudo conectar a la base de datos.")
            return

        cursor = conexion.cursor(dictionary=True)
        contrasena_plana = contrasena
        
        # Usando 'Usuarios', 'Correo', y 'Contraseña'
        cursor.execute("SELECT * FROM Usuarios WHERE Correo = %s AND Contraseña = %s",  )

        usuario = cursor.fetchone()
        conexion.close()

        if usuario:
            st.session_state["usuario"] = usuario
            st.success(f"Bienvenido/a, {usuario['Nombre_Usuario']}") 
            st.session_state["autenticado"] = True
            st.rerun()  
        else:
            st.error("Credenciales incorrectas.")
       
