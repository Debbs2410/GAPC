
import streamlit as st
from modulos.config.conexion import obtener_conexion
import pandas as pd
from modulos.solo_lectura import es_administradora


def gestionar_grupos(id_distrito=None):
    """
    Función principal para gestionar grupos.
    Permite crear, ver, editar y eliminar grupos.
    Filtra por distrito si se proporciona id_distrito.
    """
    st.title("👥 Gestión de Grupos")
    # Tabs para organizar las funcionalidades
    if es_administradora():
        tab1 = st.tabs(["📋 Ver Grupos"])[0]
        with tab1:
            ver_todos_grupos(id_distrito=id_distrito)
    else:
        tab1, tab2, tab3 = st.tabs(["📋 Ver Grupos", "➕ Crear Grupo", "✏️ Editar/Eliminar"])
        with tab1:
            ver_todos_grupos(id_distrito=id_distrito)
        with tab2:
            crear_grupo(id_distrito=id_distrito)
        with tab3:
            editar_eliminar_grupo(id_distrito=id_distrito)


def ver_todos_grupos(id_distrito=None):
    """
    Muestra todos los grupos registrados en el sistema con su información completa.
    Si se proporciona id_distrito, filtra los grupos por ese distrito.
    """
    st.subheader("📋 Lista de Grupos Registrados")
    
    # Botón para recalcular todos los conteos
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("🔄 Recalcular Conteos", help="Actualiza el número de miembros de todos los grupos según los miembros reales registrados"):
            conexion_temp = obtener_conexion()
            if conexion_temp:
                cursor_temp = conexion_temp.cursor()
                try:
                    # Actualizar todos los grupos con el conteo real de miembros
                    cursor_temp.execute("""
                        UPDATE Grupos g
                        SET g.Numero_miembros = (
                            SELECT COUNT(*) 
                            FROM Miembros m 
                            WHERE m.grupo_id = g.Id_grupo
                        )
                    """)
                    conexion_temp.commit()
                    st.success("✅ Conteos actualizados correctamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al recalcular: {str(e)}")
                finally:
                    conexion_temp.close()
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Obtener todos los grupos (filtrando por distrito si corresponde)
        if id_distrito is not None:
            cursor.execute("SELECT Id_grupo, Id_caja FROM Grupos WHERE distrito_id = %s", (id_distrito,))
        else:
            cursor.execute("SELECT Id_grupo, Id_caja FROM Grupos")
        grupos_ids = cursor.fetchall()
        # Asegurar que cada grupo tenga su propia caja y actualizar fondo común
        cajas_creadas = 0
        for g in grupos_ids:
            grupo_id = g['Id_grupo']
            id_caja = g['Id_caja']
            # Si el grupo no tiene caja, crear una y asociarla
            if not id_caja:
                cursor.execute("INSERT INTO Caja (Fondo_Comun, Interes_de_grupo) VALUES (0, 0)")
                nueva_caja_id = cursor.lastrowid
                cursor.execute("UPDATE Grupos SET Id_caja = %s WHERE Id_grupo = %s", (nueva_caja_id, grupo_id))
                id_caja = nueva_caja_id
                cajas_creadas += 1
            # Calcular fondo común
            cursor.execute("SELECT SUM(Monto) as total_ahorrado FROM Ahorros WHERE Id_grupo = %s", (grupo_id,))
            total_ahorrado = cursor.fetchone()['total_ahorrado'] or 0
            cursor.execute("SELECT SUM(Monto) as total_multas FROM Multas WHERE Id_grupo = %s AND Estado_pago = 'Pagada'", (grupo_id,))
            total_multas = cursor.fetchone()['total_multas'] or 0
            cursor.execute("SELECT SUM(monto) as total_rifas FROM Rifas WHERE grupo_id = %s", (grupo_id,))
            total_rifas = cursor.fetchone()['total_rifas'] or 0
            fondo_comun = (total_ahorrado or 0) + (total_multas or 0) + (total_rifas or 0)
            cursor.execute("UPDATE Caja SET Fondo_Comun = %s WHERE Id_caja = %s", (fondo_comun, id_caja))
        conexion.commit()
        if cajas_creadas > 0:
            st.info(f"🔑 Se crearon y asociaron {cajas_creadas} cajas nuevas para grupos que no tenían.")
        # Consulta para obtener grupos con información adicional incluyendo distrito y fondo actualizado
        if id_distrito is not None:
            cursor.execute("""
                SELECT 
                    g.Id_grupo,
                    g.Nombre,
                    g.Numero_miembros,
                    g.Id_Ciclo,
                    g.Id_caja,
                    g.distrito_id,
                    d.nombre_distrito,
                    ci.Fecha_Inicio as ciclo_inicio,
                    ci.Fecha_Fin as ciclo_fin,
                    ca.Fondo_Comun as fondo_comun,
                    (SELECT GROUP_CONCAT(Nombre_Usuario SEPARATOR ', ') FROM Usuarios WHERE Id_distrito = g.distrito_id AND Rol = 'Promotora') as promotora_nombre
                FROM Grupos g
                LEFT JOIN Distrito d ON g.distrito_id = d.distrito_id
                LEFT JOIN Ciclo ci ON g.Id_Ciclo = ci.Id_Ciclo
                LEFT JOIN Caja ca ON g.Id_caja = ca.Id_caja
                WHERE g.distrito_id = %s
                GROUP BY g.Id_grupo
                ORDER BY g.Id_grupo
            """, (id_distrito,))
        else:
            cursor.execute("""
                SELECT 
                    g.Id_grupo,
                    g.Nombre,
                    g.Numero_miembros,
                    g.Id_Ciclo,
                    g.Id_caja,
                    g.distrito_id,
                    d.nombre_distrito,
                    ci.Fecha_Inicio as ciclo_inicio,
                    ci.Fecha_Fin as ciclo_fin,
                    ca.Fondo_Comun as fondo_comun,
                    (SELECT GROUP_CONCAT(Nombre_Usuario SEPARATOR ', ') FROM Usuarios WHERE Id_distrito = g.distrito_id AND Rol = 'Promotora') as promotora_nombre
                FROM Grupos g
                LEFT JOIN Distrito d ON g.distrito_id = d.distrito_id
                LEFT JOIN Ciclo ci ON g.Id_Ciclo = ci.Id_Ciclo
                LEFT JOIN Caja ca ON g.Id_caja = ca.Id_caja
                GROUP BY g.Id_grupo
                ORDER BY g.Id_grupo
            """)
        grupos = cursor.fetchall()
        
        if not grupos:
            st.info("📭 No hay grupos registrados aún.")
        else:
            # Convertir a DataFrame para mejor visualización
            df = pd.DataFrame(grupos)
            
            # Renombrar columnas para mostrar
            df = df.rename(columns={
                'Id_grupo': 'ID',
                'Nombre': 'Nombre del Grupo',
                'nombre_distrito': 'Distrito',
                'Numero_miembros': 'Nº Miembros',
                'Id_Ciclo': 'ID Ciclo',
                'Id_caja': 'ID Caja',
                'ciclo_inicio': 'Ciclo Inicio',
                'ciclo_fin': 'Ciclo Fin',
                'fondo_comun': 'Fondo Común ($)',
                'promotora_nombre': 'Promotora'
            })
            # Seleccionar columnas a mostrar
            if es_administradora():
                columnas_mostrar = ['ID', 'Nombre del Grupo', 'Distrito', 'Nº Miembros', 'ID Ciclo', 'ID Caja', 'Fondo Común ($)', 'Promotora']
            else:
                columnas_mostrar = ['ID', 'Nombre del Grupo', 'Distrito', 'Nº Miembros', 'ID Ciclo', 'ID Caja', 'Fondo Común ($)', 'Promotora']
            df_mostrar = df[columnas_mostrar]
            # Mostrar tabla
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
            
            # Métricas generales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Grupos", len(grupos))
            with col2:
                total_miembros = sum([g['Numero_miembros'] or 0 for g in grupos])
                st.metric("👥 Total Miembros", total_miembros)
            with col3:
                grupos_con_ciclo = len([g for g in grupos if g['Id_Ciclo']])
                st.metric("🔄 Con Ciclo Activo", grupos_con_ciclo)
            with col4:
                fondo_total = sum([g['fondo_comun'] or 0 for g in grupos])
                st.metric("💰 Fondo Total", f"${fondo_total:.2f}")
            
            # (Se eliminó la sección de 'Grupos por Distrito')

            st.divider()
            st.subheader("📌 Detalles de Grupos por Distrito")
            # Agrupar grupos por distrito
            detalles_por_distrito = {}
            for grupo in grupos:
                distrito = grupo['nombre_distrito'] or 'Sin distrito'
                if distrito not in detalles_por_distrito:
                    detalles_por_distrito[distrito] = []
                detalles_por_distrito[distrito].append(grupo)

            for distrito, lista_grupos in detalles_por_distrito.items():
                st.markdown(f"### 🏘️ {distrito}")
                for grupo in lista_grupos:
                    with st.expander(f"🔍 {grupo['Nombre']} (ID: {grupo['Id_grupo']})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Miembros:** {grupo['Numero_miembros'] or 0}")
                            st.write(f"**ID Ciclo:** {grupo['Id_Ciclo'] or 'Sin ciclo'}")
                            st.write(f"**ID Caja:** {grupo['Id_caja'] or 'Sin caja'}")
                        with col2:
                            if grupo['ciclo_inicio']:
                                st.write(f"**Ciclo Inicio:** {grupo['ciclo_inicio']}")
                            if grupo['ciclo_fin']:
                                st.write(f"**Ciclo Fin:** {grupo['ciclo_fin']}")
                            st.write(f"**Fondo Común del grupo:** ${grupo['fondo_comun'] or 0:.2f}")
                            st.caption("Este fondo común es el mismo que se muestra en la sección de Caja para este grupo.")
                        # Mostrar promotora responsable del distrito
                        id_distrito_grupo = grupo.get('distrito_id') or grupo.get('distrito') or id_distrito
                        cursor.execute("SELECT Nombre_Usuario, Correo FROM Usuarios WHERE Rol = 'Promotora' AND Id_distrito = %s LIMIT 1", (id_distrito_grupo,))
                        promotora_distrito = cursor.fetchone()
                        if promotora_distrito:
                            st.write(f"**👩‍💼 Promotora responsable:** {promotora_distrito['Nombre_Usuario']} ({promotora_distrito['Correo']})")
                        else:
                            st.warning("⚠️ Sin promotora asignada a este distrito")
                        # Mostrar miembros del grupo
                        cursor.execute("""
                            SELECT nombre, sexo, Numero_Telefono 
                            FROM Miembros 
                            WHERE grupo_id = %s
                            ORDER BY nombre
                        """, (grupo['Id_grupo'],))
                        miembros = cursor.fetchall()
                        if miembros:
                            st.write(f"**👤 Miembros del grupo ({len(miembros)}):**")
                            for m in miembros:
                                st.write(f"- {m['nombre']} ({m['sexo']}) - Tel: {m['Numero_Telefono']}")
                        else:
                            st.info("Sin miembros registrados")
    
    finally:
        conexion.close()


def crear_grupo(id_distrito=None):
    """
    Formulario para crear un nuevo grupo.
    Si se proporciona id_distrito, el grupo se crea solo en ese distrito y el selector de distrito se oculta.
    """
    if es_administradora():
        st.info("🔒 Solo lectura: la administradora no puede crear grupos. Solo puede visualizar los grupos existentes.")
        return

    st.subheader("➕ Crear Nuevo Grupo")

    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return

    cursor = conexion.cursor(dictionary=True)

    try:
        # Obtener lista de distritos solo si no se fuerza id_distrito
        if id_distrito is None:
            cursor.execute("SELECT distrito_id, nombre_distrito FROM Distrito ORDER BY nombre_distrito")
            distritos = cursor.fetchall()
            if not distritos:
                st.error("❌ No hay distritos registrados en el sistema.")
                return
        # Obtener todos los nombres de grupos existentes para validación reactiva
        cursor.execute("SELECT Nombre FROM Grupos")
        nombres_grupos_existentes = set(row['Nombre'].strip().lower() for row in cursor.fetchall())

        with st.form("form_crear_grupo"):
            # Selector de Distrito (solo si no se fuerza id_distrito)
            if id_distrito is None:
                distritos_dict = {d['nombre_distrito']: d['distrito_id'] for d in distritos}
                distrito_nombre = st.selectbox("🏘️ Distrito*", list(distritos_dict.keys()))
                distrito_id = distritos_dict[distrito_nombre]
            else:
                distrito_id = id_distrito

            col1, col2 = st.columns(2)

            with col1:
                nombre_grupo = st.text_input(
                    "📝 Nombre del Grupo*",
                    placeholder="Ej: Grupo Esperanza, Grupo Unidos, etc."
                )

                # Validación reactiva de nombre duplicado
                nombre_duplicado = False
                nombre_normalizado = nombre_grupo.strip().lower() if nombre_grupo else ""
                if nombre_grupo and nombre_normalizado in nombres_grupos_existentes:
                    nombre_duplicado = True
                    st.error(f"❌ Ese nombre ya está repetido.")

                numero_miembros = st.number_input(
                    "👥 Número de Miembros*",
                    min_value=1,
                    max_value=50,
                    value=1,
                    help="Cantidad inicial de miembros (puedes actualizarlo después)"
                )

            with col2:
                # Obtener ciclos disponibles
                cursor.execute("SELECT Id_Ciclo, Fecha_Inicio, Fecha_Fin FROM Ciclo ORDER BY Id_Ciclo DESC")
                ciclos = cursor.fetchall()

                ciclos_dict = {"Sin ciclo asignado": None}
                if ciclos:
                    for c in ciclos:
                        ciclos_dict[f"Ciclo {c['Id_Ciclo']} ({c['Fecha_Inicio']} - {c['Fecha_Fin']})"] = c['Id_Ciclo']

                ciclo_seleccionado = st.selectbox("🔄 Ciclo", list(ciclos_dict.keys()))
                id_ciclo = ciclos_dict[ciclo_seleccionado]

                # Ingreso del interés de grupo (1-99)
                interes_grupo = st.number_input(
                    "Interés de grupo (%)",
                    min_value=1,
                    max_value=99,
                    value=1,
                    help="Porcentaje de interés anual para la caja de este grupo"
                )
                st.info("Al crear el grupo se le asignará automáticamente una caja individual con el interés indicado.")
            
            st.divider()
            st.write("**👩‍💼 Asignar Promotoras** (opcional)")
            
            # Obtener promotoras disponibles
            cursor.execute("""
                SELECT Id_usuario, Nombre_Usuario as nombre, Correo as correo
                FROM Usuarios 
                WHERE Rol = 'Promotora'
                ORDER BY Nombre_Usuario
            """)
            promotoras = cursor.fetchall()
            
            promotoras_seleccionadas = []
            if promotoras:
                promotoras_dict = {f"{p['nombre']} ({p['correo']})": p['Id_usuario'] for p in promotoras}
                promotoras_seleccionadas = st.multiselect(
                    "Selecciona promotoras para asignar al grupo",
                    list(promotoras_dict.keys())
                )
                ids_promotoras = [promotoras_dict[p] for p in promotoras_seleccionadas]
            else:
                st.info("ℹ️ No hay promotoras disponibles en el sistema")
                ids_promotoras = []
            

            # --- Selección de directiva (presidenta, secretaria, tesorero) ---
            st.divider()
            st.write("**👩‍💼 Asignar Directiva del Grupo**")
            # Miembros temporales (aún no existen, así que solo se puede dejar vacío o permitir asignar después)
            st.info("Puedes asignar la directiva después de registrar los miembros del grupo.")
            presidenta_id = st.number_input("ID de Miembro Presidenta (opcional)", min_value=0, step=1, value=0, help="Asigna después si aún no hay miembros.")
            secretaria_id = st.number_input("ID de Miembro Secretaria (opcional)", min_value=0, step=1, value=0, help="Asigna después si aún no hay miembros.")
            tesorero_id = st.number_input("ID de Miembro Tesorero (opcional)", min_value=0, step=1, value=0, help="Asigna después si aún no hay miembros.")

            submitted = st.form_submit_button(
                "✅ Crear Grupo",
                type="primary"
            )

            if submitted:
                # Validaciones
                if not nombre_grupo:
                    st.error("❌ El nombre del grupo es obligatorio.")
                    return
                if nombre_duplicado:
                    st.error(f"❌ Ya existe un grupo con el nombre '{nombre_grupo}'.")
                    return

                try:
                    # Crear caja individual para el grupo
                    interes_decimal = interes_grupo / 100
                    cursor.execute("INSERT INTO Caja (Fondo_Comun, Interes_de_grupo) VALUES (0, %s)", (interes_decimal,))
                    nueva_caja_id = cursor.lastrowid
                    # Crear grupo con la nueva caja
                    sql = """
                    INSERT INTO Grupos (Nombre, Numero_miembros, Id_Ciclo, Id_caja, distrito_id)
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (nombre_grupo, numero_miembros, id_ciclo, nueva_caja_id, distrito_id))
                    id_grupo_nuevo = cursor.lastrowid

                    # Asignar promotoras al grupo
                    if ids_promotoras:
                        for id_promotora in ids_promotoras:
                            cursor.execute(
                                "UPDATE Usuarios SET Id_grupo = %s WHERE Id_usuario = %s",
                                (id_grupo_nuevo, id_promotora)
                            )

                    # Asignar directiva si se proporcionan IDs válidos
                    if presidenta_id > 0:
                        cursor.execute("INSERT INTO Directiva_Grupo (id_grupo, id_miembro, rol_directiva) VALUES (%s, %s, 'Presidenta')", (id_grupo_nuevo, presidenta_id))
                    if secretaria_id > 0:
                        cursor.execute("INSERT INTO Directiva_Grupo (id_grupo, id_miembro, rol_directiva) VALUES (%s, %s, 'Secretaria')", (id_grupo_nuevo, secretaria_id))
                    if tesorero_id > 0:
                        cursor.execute("INSERT INTO Directiva_Grupo (id_grupo, id_miembro, rol_directiva) VALUES (%s, %s, 'Tesorero')", (id_grupo_nuevo, tesorero_id))

                    conexion.commit()
                    st.success(f"✅ Grupo '{nombre_grupo}' creado exitosamente en {distrito_nombre} con ID {id_grupo_nuevo}!")

                    if ids_promotoras:
                        st.info(f"👩‍💼 {len(ids_promotoras)} promotora(s) asignada(s) al grupo.")
                    if presidenta_id > 0 or secretaria_id > 0 or tesorero_id > 0:
                        st.info("👩‍💼 Directiva registrada para el grupo.")

                    st.balloons()
                    st.rerun()

                except Exception as e:
                    conexion.rollback()
                    st.error(f"❌ Error al crear el grupo: {str(e)}")
    
    finally:
        conexion.close()


def editar_eliminar_grupo(id_distrito=None):
    """
    Permite editar o eliminar grupos existentes.
    Si se proporciona id_distrito, solo permite editar/eliminar grupos de ese distrito.
    """
    st.subheader("✏️ Editar o Eliminar Grupo")
    if es_administradora():
        st.info("🔒 Solo lectura: la administradora no puede editar ni eliminar grupos. Solo puede visualizar los grupos existentes.")
        return
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Obtener lista de grupos (filtrando por distrito si corresponde)
        if id_distrito is not None:
            cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE distrito_id = %s ORDER BY Nombre", (id_distrito,))
        else:
            cursor.execute("SELECT Id_grupo, Nombre FROM Grupos ORDER BY Nombre")
        grupos = cursor.fetchall()
        
        if not grupos:
            st.info("📭 No hay grupos registrados para editar.")
            return
        
        # Selector de grupo
        grupos_dict = {f"{g['Nombre']} (ID: {g['Id_grupo']})": g['Id_grupo'] for g in grupos}
        grupo_seleccionado = st.selectbox("🔍 Selecciona un grupo", list(grupos_dict.keys()))
        id_grupo = grupos_dict[grupo_seleccionado]
        
        # Obtener datos del grupo seleccionado
        cursor.execute("""
            SELECT * FROM Grupos WHERE Id_grupo = %s
        """, (id_grupo,))
        grupo = cursor.fetchone()
        
        if not grupo:
            st.error("❌ Grupo no encontrado.")
            return
        
        # Tabs para editar o eliminar
        tab1, tab2 = st.tabs(["✏️ Editar", "🗑️ Eliminar"])
        
        with tab1:
            st.write("**Información actual del grupo:**")
            
            with st.form("form_editar_grupo"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nuevo_nombre = st.text_input(
                        "📝 Nombre del Grupo",
                        value=grupo['Nombre']
                    )
                    
                    # Obtener el número real de miembros desde la BD
                    cursor.execute("SELECT COUNT(*) as total FROM Miembros WHERE grupo_id = %s", (id_grupo,))
                    miembros_reales = cursor.fetchone()['total']
                    
                    st.info(f"👥 Número de Miembros: **{miembros_reales}** (se actualiza automáticamente)")
                
                with col2:
                    # Ciclos
                    cursor.execute("SELECT Id_Ciclo, Fecha_Inicio, Fecha_Fin FROM Ciclo ORDER BY Id_Ciclo DESC")
                    ciclos = cursor.fetchall()
                    
                    ciclos_dict = {"Sin ciclo asignado": None}
                    if ciclos:
                        for c in ciclos:
                            ciclos_dict[f"Ciclo {c['Id_Ciclo']} ({c['Fecha_Inicio']} - {c['Fecha_Fin']})"] = c['Id_Ciclo']
                    
                    # Encontrar el ciclo actual
                    ciclo_actual = None
                    for key, val in ciclos_dict.items():
                        if val == grupo['Id_Ciclo']:
                            ciclo_actual = key
                            break
                    if not ciclo_actual:
                        ciclo_actual = "Sin ciclo asignado"
                    
                    nuevo_ciclo = st.selectbox(
                        "🔄 Ciclo",
                        list(ciclos_dict.keys()),
                        index=list(ciclos_dict.keys()).index(ciclo_actual)
                    )
                    nuevo_id_ciclo = ciclos_dict[nuevo_ciclo]
                    
                    # Cajas
                    cursor.execute("SELECT Id_caja, Fondo_Comun FROM Caja ORDER BY Id_caja DESC")
                    cajas = cursor.fetchall()
                    
                    cajas_dict = {"Sin caja asignada": None}
                    if cajas:
                        for ca in cajas:
                            cajas_dict[f"Caja {ca['Id_caja']} (Fondo: ${ca['Fondo_Comun']:.2f})"] = ca['Id_caja']
                    
                    # Encontrar la caja actual
                    caja_actual = None
                    for key, val in cajas_dict.items():
                        if val == grupo['Id_caja']:
                            caja_actual = key
                            break
                    if not caja_actual:
                        caja_actual = "Sin caja asignada"
                    
                    nueva_caja = st.selectbox(
                        "💰 Caja",
                        list(cajas_dict.keys()),
                        index=list(cajas_dict.keys()).index(caja_actual)
                    )
                    nueva_id_caja = cajas_dict[nueva_caja]
                
                st.divider()
                st.write("**👩‍💼 Promotoras Asignadas**")
                
                # Obtener promotoras actuales del grupo
                cursor.execute("""
                    SELECT Id_usuario, Nombre_Usuario as nombre, Correo as correo
                    FROM Usuarios 
                    WHERE Id_grupo = %s AND Rol = 'Promotora'
                """, (id_grupo,))
                promotoras_actuales = cursor.fetchall()
                
                # Obtener todas las promotoras disponibles
                cursor.execute("""
                    SELECT Id_usuario, Nombre_Usuario as nombre, Correo as correo
                    FROM Usuarios 
                    WHERE Rol = 'Promotora'
                    ORDER BY Nombre_Usuario
                """)
                todas_promotoras = cursor.fetchall()
                
                if todas_promotoras:
                    promotoras_dict = {f"{p['nombre']} ({p['correo']})": p['Id_usuario'] for p in todas_promotoras}
                    
                    # Pre-seleccionar las promotoras actuales
                    promotoras_actuales_nombres = [
                        f"{p['nombre']} ({p['correo']})" for p in promotoras_actuales
                    ]
                    
                    nuevas_promotoras = st.multiselect(
                        "Actualizar promotoras del grupo",
                        list(promotoras_dict.keys()),
                        default=promotoras_actuales_nombres
                    )
                    nuevos_ids_promotoras = [promotoras_dict[p] for p in nuevas_promotoras]
                else:
                    st.info("ℹ️ No hay promotoras disponibles")
                    nuevos_ids_promotoras = []
                
                submitted = st.form_submit_button("💾 Guardar Cambios", type="primary")
                
                if submitted:
                    try:
                        # Actualizar datos del grupo
                        sql = """
                        UPDATE Grupos 
                        SET Nombre = %s, Id_Ciclo = %s, Id_caja = %s
                        WHERE Id_grupo = %s
                        """
                        cursor.execute(sql, (
                            nuevo_nombre,
                            nuevo_id_ciclo,
                            nueva_id_caja,
                            id_grupo
                        ))
                        
                        # Actualizar el número de miembros desde la tabla Miembros
                        cursor.execute("""
                            UPDATE Grupos 
                            SET Numero_miembros = (SELECT COUNT(*) FROM Miembros WHERE grupo_id = %s)
                            WHERE Id_grupo = %s
                        """, (id_grupo, id_grupo))
                        
                        # Actualizar asignación de promotoras
                        # 1. Quitar el grupo a todas las promotoras que lo tenían
                        cursor.execute("""
                            UPDATE Usuarios 
                            SET Id_grupo = NULL 
                            WHERE Id_grupo = %s AND Rol = 'Promotora'
                        """, (id_grupo,))
                        
                        # 2. Asignar el grupo a las nuevas promotoras seleccionadas
                        if nuevos_ids_promotoras:
                            for id_promotora in nuevos_ids_promotoras:
                                cursor.execute(
                                    "UPDATE Usuarios SET Id_grupo = %s WHERE Id_usuario = %s",
                                    (id_grupo, id_promotora)
                                )
                        
                        conexion.commit()
                        st.success(f"✅ Grupo '{nuevo_nombre}' actualizado correctamente!")
                        st.rerun()
                    
                    except Exception as e:
                        conexion.rollback()
                        st.error(f"❌ Error al actualizar el grupo: {str(e)}")
        
        with tab2:
            st.warning("⚠️ **Advertencia**: Esta acción no se puede deshacer.")
            
            # Verificar dependencias
            cursor.execute("SELECT COUNT(*) as total FROM Miembros WHERE grupo_id = %s", (id_grupo,))
            num_miembros = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM Usuarios WHERE Id_grupo = %s", (id_grupo,))
            num_usuarios = cursor.fetchone()['total']
            
            st.write(f"**Información del grupo a eliminar:**")
            st.write(f"- Nombre: **{grupo['Nombre']}**")
            st.write(f"- Miembros asociados: **{num_miembros}**")
            st.write(f"- Usuarios asignados: **{num_usuarios}**")
            
            if num_miembros > 0 or num_usuarios > 0:
                st.error("❌ No se puede eliminar el grupo porque tiene miembros o usuarios asociados.")
                st.info("💡 Primero debes reasignar o eliminar los miembros y usuarios del grupo.")
            else:
                confirmar = st.checkbox("Confirmo que deseo eliminar este grupo")
                
                if st.button("🗑️ Eliminar Grupo", type="secondary", disabled=not confirmar):
                    try:
                        cursor.execute("DELETE FROM Grupos WHERE Id_grupo = %s", (id_grupo,))
                        conexion.commit()
                        st.success(f"✅ Grupo '{grupo['Nombre']}' eliminado correctamente.")
                        st.rerun()
                    except Exception as e:
                        conexion.rollback()
                        st.error(f"❌ Error al eliminar el grupo: {str(e)}")
    
    finally:
        conexion.close()
