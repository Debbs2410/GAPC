import streamlit as st
from modulos.solo_lectura import es_administradora
from modulos.config.conexion import obtener_conexion

import pandas as pd
def ver_todos_miembros(id_distrito=None, id_grupo=None):
    """
    Vista para que la Administradora vea todos los miembros del sistema, y la Promotora solo los de su distrito.
    Si id_distrito es None, muestra todos; si se pasa, filtra por distrito.
    """
    
    import streamlit as st
    from modulos.config.conexion import obtener_conexion
    import pandas as pd 
    
    if id_grupo:
        st.subheader("👥 Miembros de mi grupo")
    elif id_distrito:
        st.subheader("👥 Miembros de mi distrito")
    else:
        st.subheader("👥 Ver Todos los Miembros del Sistema")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Filtrado por grupo (Directiva)
        if id_grupo:
            cursor.execute("""
                SELECT m.id, m.nombre, m.sexo, m.Dui, m.Numero_Telefono, m.Direccion, 
                       m.grupo_id, m.creado_en, 
                       g.Nombre AS nombre_grupo
                FROM Miembros m
                LEFT JOIN Grupos g ON m.grupo_id = g.Id_grupo
                WHERE m.grupo_id = %s
                ORDER BY m.nombre
            """, (id_grupo,))
        # Filtrado por distrito (Promotora)
        elif id_distrito:
            cursor.execute("""
                SELECT m.id, m.nombre, m.sexo, m.Dui, m.Numero_Telefono, m.Direccion, 
                       m.grupo_id, m.creado_en, 
                       g.Nombre AS nombre_grupo
                FROM Miembros m
                LEFT JOIN Grupos g ON m.grupo_id = g.Id_grupo
                WHERE g.distrito_id = %s
                ORDER BY m.grupo_id, m.nombre
            """, (id_distrito,))
        else:
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

def crear_miembro(id_distrito=None, id_grupo=None):
    """
    Formulario para crear nuevos miembros. Si id_distrito se pasa, solo permite seleccionar grupos de ese distrito (para promotora).
    Si es None, permite seleccionar cualquier distrito (para administradora).
    """
    
    import streamlit as st
    from modulos.config.conexion import obtener_conexion
    
    solo_lectura = es_administradora()
    st.subheader("➕ Crear Nuevo Miembro")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        distrito_id = None
        max_miembros = 50
        grupo_completo = False
        if id_grupo:
            # Directiva: solo puede crear miembros en su grupo
            cursor.execute("SELECT Id_grupo, Nombre, distrito_id FROM Grupos WHERE Id_grupo = %s", (id_grupo,))
            grupo_row = cursor.fetchone()
            if not grupo_row:
                st.warning("⚠️ No tienes un grupo asignado o el grupo no existe.")
                return
            grupos = [grupo_row]
            distrito_id = grupo_row['distrito_id']
            # Validar cantidad de miembros
            cursor.execute("SELECT COUNT(*) as total FROM Miembros WHERE grupo_id = %s", (id_grupo,))
            total_miembros = cursor.fetchone()['total']
            if total_miembros >= max_miembros:
                grupo_completo = True
        elif id_distrito:
            # Si es promotora, el distrito ya está definido
            distrito_id = id_distrito
            # Obtener lista de grupos solo de ese distrito
            cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE distrito_id = %s ORDER BY Nombre", (distrito_id,))
            grupos = cursor.fetchall()
            if not grupos:
                st.warning("⚠️ No hay grupos registrados en tu distrito.")
                return
        else:
            # Administradora: puede elegir distrito
            cursor.execute("SELECT distrito_id, nombre_distrito FROM Distrito ORDER BY nombre_distrito")
            distritos = cursor.fetchall()
            if not distritos:
                st.error("❌ No hay distritos registrados en el sistema.")
                return
            distritos_dict = {d['nombre_distrito']: d['distrito_id'] for d in distritos}
            distrito_nombre = st.selectbox("🏘️ Distrito", list(distritos_dict.keys()))
            distrito_id = distritos_dict[distrito_nombre]
            cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE distrito_id = %s ORDER BY Nombre", (distrito_id,))
            grupos = cursor.fetchall()
        
        if not grupos:
            st.warning("⚠️ No hay grupos registrados para crear miembros.")
            return
        
        # Formulario en columnas
        col1, col2 = st.columns(2)
        if grupo_completo and not es_administradora():
            st.error("❌ Este grupo ya tiene el máximo de 50 miembros. No puedes agregar más.")
            return
        with col1:
            nombre_input = st.text_input("🔤 Nombre Completo del Miembro", disabled=solo_lectura or grupo_completo)
            def title_case(text):
                return ' '.join([w.capitalize() for w in text.split()])
            nombre = title_case(nombre_input)
            if nombre_input and nombre != nombre_input:
                st.info(f"Se guardará como: {nombre}")
            sexo = st.selectbox("👤 Sexo", ["M", "F", "O"], disabled=solo_lectura or grupo_completo)
            dui_input = st.text_input("🆔 Dui (Documento Único de Identidad)", max_chars=9, disabled=solo_lectura or grupo_completo)
            dui_digits = ''.join(filter(str.isdigit, dui_input))[:9]
            dui = dui_digits[:8] + '-' + dui_digits[8:] if len(dui_digits) == 9 else dui_digits
            if dui_input and (not dui_input.isdigit() or len(dui_input) > 9):
                st.warning("El DUI debe contener solo 9 números, sin guiones ni letras.")
            if len(dui_digits) < 9 and dui_input:
                st.info("El DUI debe tener 9 dígitos.")
            if len(dui_digits) == 9:
                st.info(f"Se guardará como: {dui}")
        with col2:
            telefono_input = st.text_input("📞 Número de Teléfono", disabled=solo_lectura or grupo_completo)
            telefono_digits = ''.join(filter(str.isdigit, telefono_input))[:8]
            num_telefono = telefono_digits[:4] + '-' + telefono_digits[4:] if len(telefono_digits) > 4 else telefono_digits
            if telefono_input and (len(telefono_digits) != 8 or not telefono_input.replace('-', '').isdigit()):
                st.warning("El número debe tener 8 dígitos y se mostrará como 9999-9999.")
            if len(telefono_digits) == 8 and telefono_input != num_telefono:
                st.info(f"Se guardará como: {num_telefono}")
            grupos_dict = {g['Nombre']: g['Id_grupo'] for g in grupos}
            grupo_nombre = st.selectbox("👥 Grupo", list(grupos_dict.keys()), disabled=solo_lectura or grupo_completo)
            grupo_id = grupos_dict[grupo_nombre]
        direccion = st.text_area("🏠 Dirección Completa", disabled=solo_lectura or grupo_completo)
        if grupo_completo and es_administradora():
            st.info("ℹ️ Grupo completo: ya tiene 50 miembros.")
        if st.button("✅ Registrar Miembro", type="primary", disabled=solo_lectura or grupo_completo):
            if not nombre or not dui or not num_telefono or not direccion:
                st.warning("⚠️ Completa todos los campos obligatorios.")
                return
            if len(dui_digits) != 9:
                st.error("El DUI debe tener exactamente 9 dígitos.")
                return
            if len(num_telefono) != 9 or num_telefono[4] != '-':
                st.error("El número de teléfono debe tener el formato 9999-9999.")
                return
            cursor.execute("SELECT 1 FROM Miembros WHERE Dui = %s OR (nombre = %s AND grupo_id = %s)", (dui, nombre, grupo_id))
            if cursor.fetchone():
                st.error("❌ El Dui o el nombre ya se encuentra registrado en el sistema para este grupo.")
                return
            try:
                sql = """
                INSERT INTO Miembros (nombre, sexo, Dui, Numero_Telefono, Direccion, grupo_id, distrito_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (nombre, sexo, dui, num_telefono, direccion, grupo_id, distrito_id))
                cursor.execute("""
                    UPDATE Grupos 
                    SET Numero_miembros = (SELECT COUNT(*) FROM Miembros WHERE grupo_id = %s)
                    WHERE Id_grupo = %s
                """, (grupo_id, grupo_id))
                conexion.commit()
                st.success(f"✅ Miembro '{nombre}' registrado correctamente en {grupo_nombre}.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al registrar: {str(e)}")
    
    finally:
        conexion.close()

def registrar_beneficiario(id_grupo=None):
    import streamlit as st
    from modulos.config.conexion import obtener_conexion
    
    solo_lectura = es_administradora()
    st.subheader("👥 Registro de Beneficiarios")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Obtener lista de distritos
        cursor.execute("SELECT distrito_id, nombre_distrito FROM Distrito ORDER BY nombre_distrito")
        distritos = cursor.fetchall()
        
        if not distritos:
            st.error("❌ No hay distritos registrados en el sistema.")
            return
        
        # Mostrar información sobre el límite de distritos
        if len(distritos) >= 7:
            st.info(f"ℹ️ Sistema con el máximo de distritos permitidos ({len(distritos)}/7)")
        
        # Crear selectores en columnas
        col1, col2 = st.columns(2)
        
        with col1:
            # Selector de Distrito
            distritos_dict = {d['nombre_distrito']: d['distrito_id'] for d in distritos}
            distrito_nombre = st.selectbox("🏘️ Distrito", list(distritos_dict.keys()), disabled=solo_lectura)
            distrito_id = distritos_dict[distrito_nombre]
        
        # Obtener grupos del distrito seleccionado
        cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE distrito_id = %s ORDER BY Nombre", (distrito_id,))
        grupos = cursor.fetchall()
        
        with col2:
            if not grupos:
                st.warning("⚠️ No hay grupos registrados en este distrito.")
                grupo_id = None
            else:
                # Selector de Grupo
                grupos_dict = {g['Nombre']: g['Id_grupo'] for g in grupos}
                grupo_nombre = st.selectbox("👥 Grupo", list(grupos_dict.keys()), disabled=solo_lectura)
                grupo_id = grupos_dict[grupo_nombre]
        
        # Campos del beneficiario
        nombre = st.text_input("👤 Nombre completo del beneficiario", disabled=solo_lectura)
        correo = st.text_input("📧 Correo electrónico", disabled=solo_lectura)
        contrasena = st.text_input("🔒 Contraseña", type="password", disabled=solo_lectura)

        if st.button("✅ Registrar beneficiario", type="primary", disabled=solo_lectura):
            if not nombre or not correo or not contrasena:
                st.warning("⚠️ Completa todos los campos.")
                return
            
            if not grupo_id:
                st.error("❌ Debes seleccionar un grupo válido.")
                return

            # Verificar límite de beneficiarios en el grupo
            cursor.execute("SELECT COUNT(*) AS total FROM Usuarios WHERE id_grupo = %s AND rol = 'Beneficiario'", (grupo_id,))
            total = cursor.fetchone()["total"]

            if total >= 50:
                st.error("❌ Este grupo ya tiene 50 beneficiarios.")
                return

            # Verificar si el correo ya existe
            cursor.execute("SELECT COUNT(*) AS total FROM Usuarios WHERE correo = %s", (correo,))
            if cursor.fetchone()["total"] > 0:
                st.error("❌ El correo electrónico ya está registrado.")
                return

            # Insertar beneficiario
            try:
                sql = """
                INSERT INTO Usuarios (nombre, correo, contrasena, rol, id_grupo, distrito_id)
                VALUES (%s, %s, %s, 'Beneficiario', %s, %s)
                """
                cursor.execute(sql, (nombre, correo, contrasena, grupo_id, distrito_id))
                
                conexion.commit()
                st.success("✅ Beneficiario registrado correctamente")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al registrar: {str(e)}")
    
    finally:
        conexion.close()
