import streamlit as st
from modulos.config.conexion import obtener_conexion
import hashlib
import pandas as pd
def ver_todos_miembros():
    """Vista para que la Administradora vea todos los miembros del sistema."""
    
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
        # La consulta SQL permanece igual
        cursor.execute("""
            SELECT m.id, m.nombre, m.sexo, m.Dui, m.Numero_Telefono, m.Direccion,
                   m.grupo_id, m.distrito_id, m.creado_en,
                   g.Nombre AS nombre_grupo, d.Nombre AS nombre_distrito
            FROM Miembros m
            LEFT JOIN Grupos g ON m.grupo_id = g.Id_grupo
            LEFT JOIN Distritos d ON m.distrito_id = d.Id_distrito
            ORDER BY m.distrito_id, m.grupo_id, m.nombre
        """)
        
        miembros = cursor.fetchall()
        
        if not miembros:
            st.info("📭 No hay miembros registrados aún.")
        else:
            df = pd.DataFrame(miembros)
            
            # 1. Renombrar columnas para mejor legibilidad y estilo
            df = df.rename(columns={
                'id': 'ID',
                'nombre': 'Nombre',
                'sexo': 'Sexo',
                'Dui': 'Dui',                          
                'Numero_Telefono': 'Teléfono',          
                'Direccion': 'Dirección',               
                'grupo_id': 'Grupo ID',
                'distrito_id': 'Distrito ID',
                'nombre_grupo': 'Nombre Grupo',
                'nombre_distrito': 'Nombre Distrito',
                'creado_en': 'Fecha Creación'
            })
            
            # 2. DEFINIR EL NUEVO ORDEN DE COLUMNAS
            columnas_ordenadas = [
                'ID',
                'Grupo ID',      # Nuevo orden
                'Distrito ID',   # Nuevo orden
                'Nombre',
                'Sexo',
                'Dui',
                'Teléfono',
                'Dirección',
                'Nombre Grupo',
                'Nombre Distrito',
                'Fecha Creación' 
            ]
            
            # Aplicar el nuevo orden
            df = df[columnas_ordenadas]

            # 3. Mostrar tabla interactiva (quitando el índice de Pandas)
            # 👇 CAMBIO CLAVE: index=False para ocultar la columna '0'
            st.dataframe(df, use_container_width=True, hide_index=True)
            
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
    
    import streamlit as st
    from modulos.config.conexion import obtener_conexion
    
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
            # CAMPO CORREGIDO: Dui
            dui = st.text_input("🆔 Dui (Documento Único de Identidad)")
            
        with col2:
            # Selector de distrito
            distritos_dict = {d['Nombre']: d['Id_distrito'] for d in distritos}
            distrito_nombre = st.selectbox("📍 Distrito", list(distritos_dict.keys()))
            distrito_id = distritos_dict[distrito_nombre]
            
            # Número de Teléfono
            num_telefono = st.text_input("📞 Número de Teléfono")
            
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
        
        # Dirección (Full width)
        direccion = st.text_area("🏠 Dirección Completa")
        
        if st.button("✅ Registrar Miembro", type="primary"):
            # Validación de campos obligatorios
            if not nombre or not dui or not num_telefono or not direccion:
                st.warning("⚠️ Completa todos los campos obligatorios (Nombre, Dui, Teléfono y Dirección).")
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
            
            # Insertar nuevo miembro CON LA COLUMNA CORREGIDA
            try:
                sql = """
                INSERT INTO Miembros (nombre, sexo, Dui, Numero_Telefono, Direccion, grupo_id, distrito_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                # La tupla debe coincidir con el orden de las columnas del INSERT
                cursor.execute(sql, (nombre, sexo, dui, num_telefono, direccion, grupo_id, distrito_id))
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
