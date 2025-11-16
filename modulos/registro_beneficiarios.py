import streamlit as st
from modulos.config.conexion import obtener_conexion

import pandas as pd
def ver_todos_miembros():
    """Vista para que la Administradora vea todos los miembros del sistema, sin lógica de distrito."""
    
    import streamlit as st
    from modulos.config.conexion import obtener_conexion
    import pandas as pd 
    
    st.subheader("👥 Ver Todos los Miembros del Sistema")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # CONSULTA SQL CORREGIDA: Solo usa la tabla Miembros y Grupos (JOIN)
        cursor.execute("""
            SELECT m.id, m.nombre, m.sexo, m.Dui, m.Numero_Telefono, m.Direccion, 
                   m.grupo_id, m.creado_en, 
                   g.Nombre AS nombre_grupo
            FROM Miembros m
            LEFT JOIN Grupos g ON m.grupo_id = g.Id_grupo
            ORDER BY m.grupo_id, m.nombre
        """)
        
        miembros = cursor.fetchall()
        
        if not miembros:
            st.info("📭 No hay miembros registrados aún.")
        else:
            df = pd.DataFrame(miembros)
            
            # RENOMBRADO: Se eliminan las columnas relacionadas con Distrito
            df = df.rename(columns={
                'id': 'ID',
                'nombre': 'Nombre',
                'sexo': 'Sexo',
                'Dui': 'Dui',
                'Numero_Telefono': 'Teléfono',          
                'Direccion': 'Dirección',               
                'grupo_id': 'Grupo ID',
                'nombre_grupo': 'Nombre Grupo',
                'creado_en': 'Fecha Creación'
            })
            
            # ORDEN DE COLUMNAS SOLICITADO
            columnas_ordenadas = [
                'ID',
                'Grupo ID',     
                'Nombre',
                'Sexo',
                'Dui',
                'Teléfono',
                'Dirección',
                'Nombre Grupo',
                'Fecha Creación' 
            ]
            
            df = df[columnas_ordenadas]

            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # ESTADÍSTICAS CORREGIDAS
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total de Miembros", len(miembros))
            with col2:
                st.metric("Grupos Activos", df['Grupo ID'].nunique())
    
    finally:
        conexion.close()

def crear_miembro():
    """Formulario simplificado para la Administradora que crea nuevos miembros sin usar la lógica de distrito."""
    
    import streamlit as st
    from modulos.config.conexion import obtener_conexion
    
    st.subheader("➕ Crear Nuevo Miembro")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Obtener lista de GRUPOS directamente
        cursor.execute("SELECT Id_grupo, Nombre FROM Grupos ORDER BY Nombre")
        grupos = cursor.fetchall()
        
        if not grupos:
            st.error("❌ No hay grupos registrados en el sistema.")
            return
        
        # Formulario en columnas
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("🔤 Nombre Completo del Miembro")
            sexo = st.selectbox("👤 Sexo", ["M", "F", "O"])
            dui = st.text_input("🆔 Dui (Documento Único de Identidad)")
            
        with col2:
            num_telefono = st.text_input("📞 Número de Teléfono")
            
            # Selector de Grupo
            grupos_dict = {g['Nombre']: g['Id_grupo'] for g in grupos}
            grupo_nombre = st.selectbox("👥 Grupo", list(grupos_dict.keys()))
            grupo_id = grupos_dict[grupo_nombre]
            
        # Dirección
        direccion = st.text_area("🏠 Dirección Completa")
        
        if st.button("✅ Registrar Miembro", type="primary"):
            # Validación de campos obligatorios
            if not nombre or not dui or not num_telefono or not direccion:
                st.warning("⚠️ Completa todos los campos obligatorios.")
                return
            
            # Validación: Verificar que el Dui no esté duplicado
            cursor.execute("SELECT COUNT(*) AS total FROM Miembros WHERE Dui = %s", (dui,))
            if cursor.fetchone()["total"] > 0:
                st.error("❌ El Dui ingresado ya se encuentra registrado en el sistema.")
                return
                
            # Validar que no exista duplicado de nombre en el grupo
            cursor.execute(
                "SELECT COUNT(*) AS total FROM Miembros WHERE nombre = %s AND grupo_id = %s",
                (nombre, grupo_id)
            )
            existe = cursor.fetchone()["total"]
            
            if existe > 0:
                st.error(f"❌ Ya existe un miembro con el nombre '{nombre}' en este grupo.")
                return
            
            # INSERT: Se omite la columna distrito_id
            try:
                sql = """
                INSERT INTO Miembros (nombre, sexo, Dui, Numero_Telefono, Direccion, grupo_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (nombre, sexo, dui, num_telefono, direccion, grupo_id))

                conexion.commit()
                st.success(f"✅ Miembro '{nombre}' registrado correctamente en {grupo_nombre}.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al registrar: {str(e)}")
    
    finally:
        conexion.close()
    
    finally:
        conexion.close()

def registrar_beneficiario(id_grupo):
    import streamlit as st
    from modulos.config.conexion import obtener_conexion
    # hashlib ya no es necesario
    
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

        # --- CAMBIO CLAVE 1: Eliminación del HASH ---
        # Usamos la contraseña en texto plano para el INSERT
        contrasena_plana = contrasena
        # La línea del hash fue eliminada: contrasena_hash = hashlib.sha256(...)

        # --- CAMBIO CLAVE 2: Eliminación de id_distrito en SQL ---
        sql = """
        INSERT INTO usuarios (nombre, correo, contrasena, rol, id_grupo)
        VALUES (%s, %s, %s, 'Beneficiario', %s)
        """
        # La tupla de valores ya no incluye el hash ni referencias a id_distrito
        cursor.execute(sql, (nombre, correo, contrasena_plana, id_grupo))
        
        conexion.commit()
        conexion.close()

        st.success("Beneficiario registrado correctamente ✅")
