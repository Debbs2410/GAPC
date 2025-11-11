import streamlit as st
from modulos.config.conexion import obtener_conexion
import hashlib

def registrar_beneficiario(id_grupo):
    st.subheader("👥 Registro de Beneficiarios")

    nombre = st.text_input("Nombre completo del beneficiario")
    correo = st.text_input("Correo electrónico")
    contrasena = st.text_input("Contraseña", type="password")

    if st.button("Registrar beneficiario"):
        if not nombre or not correo or not contrasena:
            st.warning("Completa todos los campos.")
            return

        conexion = obtener_conexion()
        if not conexion:
            st.error("Error de conexión.")
            return

        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total FROM usuarios WHERE id_grupo = %s AND rol = 'Beneficiario'", (id_grupo,))
        total = cursor.fetchone()["total"]

        if total >= 50:
            st.error("Este grupo ya tiene 50 beneficiarios.")
            conexion.close()
            return

        contrasena_hash = hashlib.sha256(contrasena.encode()).hexdigest()

        sql = """
        INSERT INTO usuarios (nombre, correo, contrasena, rol, id_distrito, id_grupo)
        VALUES (%s, %s, %s, 'Beneficiario',
            (SELECT id_distrito FROM usuarios WHERE id_grupo = %s LIMIT 1), %s)
        """
        cursor.execute(sql, (nombre, correo, contrasena_hash, id_grupo, id_grupo))
        conexion.commit()
        conexion.close()

        st.success("Beneficiario registrado correctamente ✅")
