import streamlit as st
from modulos.solo_lectura import es_administradora
from modulos.config.conexion import obtener_conexion
# hashlib ya no es necesario

def registrar_usuario():
    st.title("🧾 Registro de Usuarios del Sistema")

    nombre = st.text_input("Nombre completo")
    correo = st.text_input("Correo electrónico")
    contrasena = st.text_input("Contraseña", type="password")

    rol = st.selectbox("Rol", ["Administradora", "Promotora", "Directiva"])
    id_grupo = None
    Id_distrito = 0
    rol_directiva = None

    # Si es Promotora, pedir distrito
    if rol == "Promotora":
        # Obtener distritos de la base de datos
        conexion_tmp = obtener_conexion()
        distritos_opciones = []
        if conexion_tmp:
            cursor_tmp = conexion_tmp.cursor(dictionary=True)
            cursor_tmp.execute("SELECT distrito_id, nombre_distrito FROM Distrito ORDER BY nombre_distrito")
            distritos_opciones = cursor_tmp.fetchall()
            conexion_tmp.close()
        if distritos_opciones:
            distritos_dict = {d['nombre_distrito']: d['distrito_id'] for d in distritos_opciones}
            distrito_nombre = st.selectbox("Distrito", list(distritos_dict.keys()))
            Id_distrito = distritos_dict[distrito_nombre]
        else:
            Id_distrito = st.number_input("ID de Distrito (escribe el número)", min_value=1, step=1)

    # Si es Directiva, pedir solo grupo y obtener distrito automáticamente (sin mostrar selección de distrito)

    if rol == "Directiva":
        conexion_tmp = obtener_conexion()
        grupos_opciones = []
        if conexion_tmp:
            cursor_tmp = conexion_tmp.cursor(dictionary=True)
            cursor_tmp.execute("SELECT Id_grupo, Nombre, distrito_id FROM Grupos ORDER BY Nombre")
            grupos_opciones = cursor_tmp.fetchall()
            conexion_tmp.close()
        if grupos_opciones:
            grupos_dict = {f"{g['Nombre']} (ID:{g['Id_grupo']})": (g['Id_grupo'], g['distrito_id']) for g in grupos_opciones}
            grupo_nombre = st.selectbox("Grupo", list(grupos_dict.keys()))
            id_grupo, Id_distrito = grupos_dict[grupo_nombre]
        else:
            id_grupo = st.number_input("ID de Grupo (escribe el número)", min_value=1, step=1)
            if id_grupo:
                conexion_tmp = obtener_conexion()
                if conexion_tmp:
                    cursor_tmp = conexion_tmp.cursor(dictionary=True)
                    cursor_tmp.execute("SELECT distrito_id FROM Grupos WHERE Id_grupo = %s", (id_grupo,))
                    grupo_row = cursor_tmp.fetchone()
                    if grupo_row and grupo_row['distrito_id']:
                        Id_distrito = grupo_row['distrito_id']
                    conexion_tmp.close()
        # El distrito se asume automáticamente del grupo, no se muestra al usuario
        rol_directiva = st.selectbox("Rol de directiva", ["Presidenta", "Secretaria", "Tesorero"])
        
    if st.button("Registrar usuario"):
        # Validación de campos obligatorios según rol
        if not nombre or not correo or not contrasena:
            st.warning("⚠️ Completa todos los campos.")
            return
        if rol == "Promotora" and not Id_distrito:
            st.warning("⚠️ Debes seleccionar un distrito para Promotora.")
            return
        if rol == "Directiva" and (not Id_distrito or not id_grupo):
            st.warning("⚠️ Debes seleccionar un grupo válido para Directiva.")
            return

        conexion = obtener_conexion()
        if not conexion:
            st.error("❌ No se pudo conectar con la base de datos.")
            return

        cursor = conexion.cursor(dictionary=True)
        contrasena_plana = contrasena

        # Validar correo único
        cursor.execute("SELECT 1 FROM Usuarios WHERE Correo = %s", (correo,))
        if cursor.fetchone():
            st.error("Ya existe un usuario con ese correo.")
            conexion.close()
            return

        # --- Reglas de negocio (Validaciones simplificadas) ---
        if rol == "Administradora":
            cursor.execute("SELECT COUNT(*) AS total FROM Usuarios WHERE rol = 'Administradora'")
            total_admin = cursor.fetchone()["total"]
            if total_admin >= 1:
                st.error("❌ Solo puede haber una administradora en el sistema.")
                conexion.close()
                return


        elif rol == "Directiva":
            # Validar que no exista ya ese rol de directiva para el grupo en Usuarios
            cursor.execute("""
                SELECT COUNT(*) AS total FROM Usuarios WHERE Id_grupo = %s AND Rol_Directiva = %s
            """, (id_grupo, rol_directiva))
            total_dir = cursor.fetchone()["total"]
            if total_dir >= 1:
                st.error(f"❌ Ya existe una persona registrada como {rol_directiva} para el grupo {id_grupo}.")
                conexion.close()
                return

        # --- Inserción del usuario ---
        try:
            if rol == "Promotora":
                sql = """
                INSERT INTO Usuarios (Nombre_Usuario, Correo, Contraseña, Rol, Id_distrito)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (nombre, correo, contrasena_plana, rol, Id_distrito))
            elif rol == "Directiva":
                # Insertar usuario con Rol_Directiva
                sql = """
                INSERT INTO Usuarios (Nombre_Usuario, Correo, Contraseña, Rol, Id_grupo, Id_distrito, Rol_Directiva)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (nombre, correo, contrasena_plana, rol, id_grupo, Id_distrito, rol_directiva))
            else:  # Administradora
                sql = """
                INSERT INTO Usuarios (Nombre_Usuario, Correo, Contraseña, Rol)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (nombre, correo, contrasena_plana, rol))
            conexion.commit()
            st.success(f"✅ Usuario {rol} registrado correctamente.")
        except Exception as e:
            st.error(f"❌ Error al registrar en la DB: {str(e)}.")
        finally:
            conexion.close()
