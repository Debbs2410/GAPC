import streamlit as st
from modulos.config.conexion import obtener_conexion
import hashlib

def registrar_usuario():
    st.subheader("Registro de usuario")

    nombre = st.text_input("Nombre completo")
    correo = st.text_input("Correo electrónico")
    contrasena = st.text_input("Contraseña", type="password")
    rol = st.selectbox("Rol", ["Beneficiario", "Directiva", "Promotora","Administradora"])
    Id_distrito = st.number_input("Distrito", min_value=1, max_value=7 step=1)
    Id_grupo= st.number_input("Grupo", min_value=1, step=1)

    if st.button("Registrar"):
        if not nombre or not correo or not contrasena:
            st.warning("Completa todos los campos.")
            return

        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor(dictionary=True)

            # Verificar si el grupo ya tiene 50 miembros (solo para beneficiarios)
            if rol == "beneficiario":
                cursor.execute("SELECT COUNT(*) AS total FROM usuarios WHERE id_grupo = %s", (id_grupo,))
                total = cursor.fetchone()["total"]
                if total >= 50:
                    st.error("Este grupo ya tiene el máximo de 50 beneficiarios.")
                    return

            contrasena_hash = hashlib.sha256(contrasena.encode()).hexdigest()

            sql = """INSERT INTO usuarios (nombre, correo, contrasena, rol, id_distrito, id_grupo)
                     VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (nombre, correo, contrasena_hash, rol, id_distrito, id_grupo))
            conexion.commit()
            conexion.close()
            st.success("Usuario registrado correctamente.")
