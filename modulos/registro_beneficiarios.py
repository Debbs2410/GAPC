import streamlit as st
from modulos.config.conexion import obtener_conexion
import hashlib
import pandas as pd

def ver_todos_miembros():
    """Vista para que la Administradora vea todos los miembros de todos los distritos."""
    st.subheader("👥 Ver Todos los Miembros del Sistema")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Obtener todos los miembros con información del grupo y distrito
        cursor.execute("""
            SELECT m.id, m.nombre, m.sexo, m.grupo_id, m.distrito_id, m.creado_en,
                   g.Nombre AS nombre_grupo, d.Nombre AS nombre_distrito
            FROM miembros m
            LEFT JOIN Grupos g ON m.grupo_id = g.Id_grupo
            LEFT JOIN Distritos d ON m.distrito_id = d.Id_distrito
            ORDER BY m.distrito_id, m.grupo_id, m.nombre
        """)
        
        miembros = cursor.fetchall()
        
        if not miembros:
            st.info("📭 No hay miembros registrados aún.")
        else:
            # Convertir a DataFrame para mejor presentación
            df = pd.DataFrame(miembros)
            
            # Renombrar columnas para mejor legibilidad
            df = df.rename(columns={
                'id': 'ID',
                'nombre': 'Nombre',
                'sexo': 'Sexo',
                'grupo_id': 'Grupo ID',
                'distrito_id': 'Distrito ID',
                'nombre_grupo': 'Nombre Grupo',
                'nombre_distrito': 'Nombre Distrito',
                'creado_en': 'Fecha Creación'
            })
            
            # Mostrar tabla interactiva
            st.dataframe(df, use_container_width=True)
            
            # Estadísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Miembros", len(miembros))
            with col2:
                st.metric("Distritos Activos", df['Distrito ID'].nunique())
            with col3:
                st.metric("Grupos Activos", df['Grupo ID'].nunique())
    
    finally:
        conexion.close()


def crear_miembro():
    """Formulario para que la Administradora cree nuevos miembros."""
    st.subheader("➕ Crear Nuevo Miembro")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Obtener lista de distritos
        cursor.execute("SELECT Id_distrito, Nombre FROM Distritos ORDER BY Id_distrito")
        distritos = cursor.fetchall()
        
        if not distritos:
            st.error("❌ No hay distritos registrados en el sistema.")
            return
        
        # Formulario en columnas
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("🔤 Nombre Completo del Miembro")
            sexo = st.selectbox("👤 Sexo", ["M", "F", "O"])
        
        with col2:
            # Selector de distrito
            distritos_dict = {d['Nombre']: d['Id_distrito'] for d in distritos}
            distrito_nombre = st.selectbox("📍 Distrito", list(distritos_dict.keys()))
            distrito_id = distritos_dict[distrito_nombre]
            
            # Cargar grupos del distrito seleccionado
            cursor.execute(
                "SELECT Id_grupo, Nombre FROM Grupos WHERE Id_distrito = %s ORDER BY Nombre",
                (distrito_id,)
            )
            grupos = cursor.fetchall()
            
            if not grupos:
                st.warning(f"⚠️ No hay grupos en el distrito '{distrito_nombre}'")
                return
            
            grupos_dict = {g['Nombre']: g['Id_grupo'] for g in grupos}
            grupo_nombre = st.selectbox("👥 Grupo", list(grupos_dict.keys()))
            grupo_id = grupos_dict[grupo_nombre]
        
        if st.button("✅ Registrar Miembro", type="primary"):
            if not nombre:
                st.warning("⚠️ Completa el nombre del miembro.")
                return
            
            # Validar que no exista duplicado
            cursor.execute(
                "SELECT COUNT(*) AS total FROM miembros WHERE nombre = %s AND grupo_id = %s",
                (nombre, grupo_id)
            )
            existe = cursor.fetchone()["total"]
            
            if existe > 0:
                st.error(f"❌ Ya existe un miembro con el nombre '{nombre}' en este grupo.")
                return
            
            # Insertar nuevo miembro
            try:
                sql = """
                INSERT INTO miembros (nombre, sexo, grupo_id, distrito_id)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (nombre, sexo, grupo_id, distrito_id))
                conexion.commit()
                st.success(f"✅ Miembro '{nombre}' registrado correctamente en {grupo_nombre}.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al registrar: {str(e)}")
    
    finally:
        conexion.close()


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
