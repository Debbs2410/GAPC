import streamlit as st
from modulos.config.conexion import obtener_conexion
# hashlib ya no es necesario

def registrar_usuario():
    st.title("🧾 Registro de Usuarios del Sistema")

    nombre = st.text_input("Nombre completo")
    correo = st.text_input("Correo electrónico")
    contrasena = st.text_input("Contraseña", type="password")
    rol = st.selectbox("Rol", ["Administradora", "Promotora", "Directiva"])
    
    id_grupo = None

    # Si es Directiva, mostrar campo de grupo
    if rol == "Directiva":
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
        
        # --- CAMBIO CLAVE: Se usa la contraseña en texto plano (contrasena_plana) ---
        contrasena_plana = contrasena
        # La lógica de hashing se ha ELIMINADO

        # --- Reglas de negocio (Validaciones simplificadas) ---
        if rol == "Administradora":
            cursor.execute("SELECT COUNT(*) AS total FROM usuarios WHERE rol = 'Administradora'")
            total_admin = cursor.fetchone()["total"]
            if total_admin >= 1:
                st.error("❌ Solo puede haber una administradora en el sistema.")
                conexion.close()
                return

        elif rol == "Directiva":
            if not id_grupo:
                st.warning("⚠️ Debes indicar el número de grupo.")
                conexion.close()
                return
            
            # Validar que solo exista 1 Directiva por grupo
            cursor.execute("SELECT COUNT(*) AS total FROM usuarios WHERE rol = 'Directiva' AND id_grupo = %s", (id_grupo,))
            total_dir = cursor.fetchone()["total"]
            if total_dir >= 1:
                st.error(f"❌ Ya existe una directiva registrada para el grupo {id_grupo}.")
                conexion.close()
                return

        # --- Inserción del usuario ---
        try:
            # SENTENCIA SQL: Se omite 'id_distrito'
            sql = """
            INSERT INTO usuarios (nombre, correo, contrasena, rol, id_grupo)
            VALUES (%s, %s, %s, %s, %s)
            """
            # Se usa contrasena_plana en la tupla de valores
            cursor.execute(sql, (nombre, correo, contrasena_plana, rol, id_grupo))
            
            conexion.commit()
            st.success(f"✅ Usuario {rol} registrado correctamente.")
        
        except Exception as e:
            st.error(f"❌ Error al registrar en la DB: {str(e)}.")

        finally:
            conexion.close()
