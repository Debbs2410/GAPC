import streamlit as st
from modulos.config.conexion import obtener_conexion
import hashlib

def registrar_usuario():
    st.title("🧾 Registro de Usuarios del Sistema")

    nombre = st.text_input("Nombre completo")
    correo = st.text_input("Correo electrónico")
    contrasena = st.text_input("Contraseña", type="password")
    rol = st.selectbox("Rol", ["Administradora", "Promotora", "Directiva"])
    id_distrito = None
    id_grupo = None

    # Si es promotora o directiva, mostrar campos adicionales
    if rol == "Promotora":
        id_distrito = st.number_input("Distrito", min_value=1, max_value=7, step=1)
    elif rol == "Directiva":
        id_distrito = st.number_input("Distrito al que pertenece", min_value=1, max_value=7, step=1)
        id_grupo = st.number_input("Número de grupo", min_value=1, step=1)

    if st.button("Registrar usuario"):
        if not nombre or not correo or not contrasena:
            st.warning("⚠️ Completa todos los campos.")
            return

        conexion = obtener_conexion()
        if not conexion:
            st.error("❌ No se pudo conectar con la base de datos.")
            return

        cursor = conexion.cursor(dictionary=True)
        contrasena_hash = hashlib.sha256(contrasena.encode()).hexdigest()

        # --- Reglas de negocio ---
        if rol == "Administradora":
            cursor.execute("SELECT COUNT(*) AS total FROM usuarios WHERE rol = 'Administradora'")
            total_admin = cursor.fetchone()["total"]
            if total_admin >= 1:
                st.error("❌ Solo puede haber una administradora en el sistema.")
                conexion.close()
                return

        elif rol == "Promotora":
            if not id_distrito:
                st.warning("⚠️ Debes indicar un distrito.")
                conexion.close()
                return
            cursor.execute("SELECT COUNT(*) AS total FROM usuarios WHERE rol = 'Promotora' AND id_distrito = %s", (id_distrito,))
            total_prom = cursor.fetchone()["total"]
            if total_prom >= 1:
                st.error(f"❌ Ya existe una promotora registrada en el distrito {id_distrito}.")
                conexion.close()
                return

        elif rol == "Directiva":
            if not id_distrito or not id_grupo:
                st.warning("⚠️ Debes indicar distrito y grupo.")
                conexion.close()
                return
            cursor.execute("SELECT COUNT(*) AS total FROM usuarios WHERE rol = 'Directiva' AND id_grupo = %s", (id_grupo,))
            total_dir = cursor.fetchone()["total"]
            if total_dir >= 1:
                st.error(f"❌ Ya existe una directiva registrada para el grupo {id_grupo}.")
                conexion.close()
                return

        # --- Inserción del usuario ---
        sql = """
        INSERT INTO usuarios (nombre, correo, contrasena, rol, id_distrito, id_grupo)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (nombre, correo, contrasena_hash, rol, id_distrito, id_grupo))
        conexion.commit()
        conexion.close()

        st.success(f"✅ Usuario {rol} registrado correctamente.")
