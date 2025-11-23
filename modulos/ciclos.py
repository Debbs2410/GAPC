import pandas as pd

def obtener_datos_utilidades_ciclo(id_grupo):
    from modulos.config.conexion import obtener_conexion
    conexion = obtener_conexion()
    if not conexion:
        return None
    cursor = conexion.cursor(dictionary=True)
    # Utilidades del ciclo por grupo
    cursor.execute('''
        SELECT c.Id_Ciclo, c.Fecha_Inicio, c.Fecha_Fin, c.Ahorro_Acumulado
        FROM Ciclo c
        INNER JOIN Grupos g ON g.Id_Ciclo = c.Id_Ciclo
        WHERE g.Id_grupo = %s
        ORDER BY c.Fecha_Inicio DESC
        LIMIT 1
    ''', (id_grupo,))
    rows = cursor.fetchall()
    conexion.close()
    if rows:
        return pd.DataFrame(rows)
    return None
import streamlit as st
from modulos.solo_lectura import es_administradora
from modulos.config.conexion import obtener_conexion
import pandas as pd
from datetime import datetime, timedelta
import datetime as dt


def gestionar_ciclos(id_distrito=None, id_grupo=None):
    """
    Función principal para gestionar ciclos.
    Permite crear, ver y gestionar el estado de los ciclos.
    Si se proporciona id_distrito, filtra los ciclos y operaciones por ese distrito.
    """
    st.title("Gestión de Ciclos")
    # Solo lectura para administradora
    solo_lectura = es_administradora()
    # Tabs para organizar las funcionalidades
    if not solo_lectura:
        tab1, tab2, tab3 = st.tabs(["Ver Ciclos", "Crear Ciclo", "Gestionar Estado"])
    else:
        tab1, tab3 = st.tabs(["Ver Ciclos", "Gestionar Estado"])
    with tab1:
        ver_todos_ciclos(id_distrito=id_distrito, id_grupo=id_grupo)
    if not solo_lectura:
        with tab2:
            crear_ciclo(id_distrito=id_distrito, solo_lectura=solo_lectura)
        with tab3:
            gestionar_estado_ciclos(id_distrito=id_distrito, id_grupo=id_grupo, solo_lectura=solo_lectura)
    else:
        with tab3:
            gestionar_estado_ciclos(id_distrito=id_distrito, id_grupo=id_grupo, solo_lectura=solo_lectura)


def ver_todos_ciclos(id_distrito=None, id_grupo=None):
    """
    Muestra todos los ciclos registrados en el sistema con su información completa.
    Si se proporciona id_distrito, solo muestra ciclos asociados a grupos de ese distrito.
    """
    st.subheader("Historial de Ciclos")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    from modulos.solo_lectura import es_administradora
    if 'solo_lectura' not in locals() or solo_lectura is None:
        solo_lectura = es_administradora()
        from modulos.solo_lectura import es_administradora
        if 'solo_lectura' not in locals() or solo_lectura is None:
            solo_lectura = es_administradora()
    try:
        # Consulta para obtener ciclos con información adicional y el ahorro real acumulado
        if id_grupo is not None:
            cursor.execute("""
                SELECT 
                    c.Id_Ciclo,
                    c.Fecha_Inicio,
                    c.Fecha_Fin,
                    (SELECT IFNULL(SUM(Monto),0) FROM Ahorros WHERE Id_Ciclo = c.Id_Ciclo AND Estado = 'Activo') AS Ahorro_Real,
                    c.Ahorro_Acumulado AS Ahorro_Anterior,
                    COUNT(DISTINCT g.Id_grupo) as num_grupos,
                    GROUP_CONCAT(DISTINCT g.Nombre SEPARATOR ', ') as grupos_nombres,
                    DATEDIFF(c.Fecha_Fin, c.Fecha_Inicio) as duracion_dias,
                    CASE 
                        WHEN CURDATE() < c.Fecha_Inicio THEN 'Pendiente'
                        WHEN CURDATE() BETWEEN c.Fecha_Inicio AND c.Fecha_Fin THEN 'Activo'
                        WHEN CURDATE() > c.Fecha_Fin THEN 'Completado'
                    END as estado
                FROM Ciclo c
                LEFT JOIN Grupos g ON g.Id_Ciclo = c.Id_Ciclo
                WHERE g.Id_grupo = %s
                GROUP BY c.Id_Ciclo
                ORDER BY c.Fecha_Inicio DESC
            """, (id_grupo,))
        elif id_distrito is not None:
            cursor.execute("""
                SELECT 
                    c.Id_Ciclo,
                    c.Fecha_Inicio,
                    c.Fecha_Fin,
                    (SELECT IFNULL(SUM(Monto),0) FROM Ahorros WHERE Id_Ciclo = c.Id_Ciclo AND Estado = 'Activo') AS Ahorro_Real,
                    c.Ahorro_Acumulado AS Ahorro_Anterior,
                    COUNT(DISTINCT g.Id_grupo) as num_grupos,
                    GROUP_CONCAT(DISTINCT g.Nombre SEPARATOR ', ') as grupos_nombres,
                    DATEDIFF(c.Fecha_Fin, c.Fecha_Inicio) as duracion_dias,
                    CASE 
                        WHEN CURDATE() < c.Fecha_Inicio THEN 'Pendiente'
                        WHEN CURDATE() BETWEEN c.Fecha_Inicio AND c.Fecha_Fin THEN 'Activo'
                        WHEN CURDATE() > c.Fecha_Fin THEN 'Completado'
                    END as estado
                FROM Ciclo c
                LEFT JOIN Grupos g ON g.Id_Ciclo = c.Id_Ciclo
                WHERE g.distrito_id = %s
                GROUP BY c.Id_Ciclo
                ORDER BY c.Fecha_Inicio DESC
            """, (id_distrito,))
        else:
            cursor.execute("""
                SELECT 
                    c.Id_Ciclo,
                    c.Fecha_Inicio,
                    c.Fecha_Fin,
                    (SELECT IFNULL(SUM(Monto),0) FROM Ahorros WHERE Id_Ciclo = c.Id_Ciclo AND Estado = 'Activo') AS Ahorro_Real,
                    c.Ahorro_Acumulado AS Ahorro_Anterior,
                    COUNT(DISTINCT g.Id_grupo) as num_grupos,
                    GROUP_CONCAT(DISTINCT g.Nombre SEPARATOR ', ') as grupos_nombres,
                    DATEDIFF(c.Fecha_Fin, c.Fecha_Inicio) as duracion_dias,
                    CASE 
                        WHEN CURDATE() < c.Fecha_Inicio THEN 'Pendiente'
                        WHEN CURDATE() BETWEEN c.Fecha_Inicio AND c.Fecha_Fin THEN 'Activo'
                        WHEN CURDATE() > c.Fecha_Fin THEN 'Completado'
                    END as estado
                FROM Ciclo c
                LEFT JOIN Grupos g ON g.Id_Ciclo = c.Id_Ciclo
                GROUP BY c.Id_Ciclo
                ORDER BY c.Fecha_Inicio DESC
            """)
        ciclos = cursor.fetchall()
        
        if not ciclos:
            st.info("📭 No hay ciclos registrados aún.")
        else:
            # Convertir a DataFrame
            df = pd.DataFrame(ciclos)
            # Renombrar columnas y usar el ahorro real calculado
            df = df.rename(columns={
                'Id_Ciclo': 'ID',
                'Fecha_Inicio': 'Inicio',
                'Fecha_Fin': 'Fin',
                'Ahorro_Real': 'Ahorro ($)',
                'num_grupos': 'Grupos',
                'duracion_dias': 'Días',
                'estado': 'Estado'
            })
            # Seleccionar columnas para mostrar
            df_display = df[['ID', 'Inicio', 'Fin', 'Días', 'Ahorro ($)', 'Grupos', 'Estado']]
            # Aplicar formato de color según estado
            def color_estado(val):
                if val == 'Activo':
                    return 'background-color: #90EE90'
                elif val == 'Completado':
                    return 'background-color: #D3D3D3'
                elif val == 'Pendiente':
                    return 'background-color: #FFD700'
                return ''
            # Mostrar tabla
            st.dataframe(
                df_display.style.applymap(color_estado, subset=['Estado']),
                use_container_width=True,
                hide_index=True
            )
            # Métricas generales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Ciclos", len(ciclos))
            with col2:
                ciclos_activos = len([c for c in ciclos if c['estado'] == 'Activo'])
                st.metric("Activos", ciclos_activos)
            with col3:
                ciclos_completados = len([c for c in ciclos if c['estado'] == 'Completado'])
                st.metric("Completados", ciclos_completados)
            with col4:
                ahorro_total = sum([c['Ahorro_Real'] or 0 for c in ciclos])
                st.metric("Ahorro Total", f"${ahorro_total:.2f}")
            
            # Mostrar detalles expandibles de cada ciclo
            st.divider()
            st.subheader("📌 Detalles por Ciclo")
            
            for ciclo in ciclos:
                # Color del badge según estado
                if ciclo['estado'] == 'Activo':
                    badge = "🟢"
                elif ciclo['estado'] == 'Completado':
                    badge = "⚫"
                else:
                    badge = "🟡"
                with st.expander(f"{badge} Ciclo {ciclo['Id_Ciclo']} - {ciclo['estado']} ({ciclo['Fecha_Inicio']} / {ciclo['Fecha_Fin']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Fecha Inicio:** {ciclo['Fecha_Inicio']}")
                        st.write(f"**Fecha Fin:** {ciclo['Fecha_Fin']}")
                        st.write(f"**Duración:** {ciclo['duracion_dias']} días (~{ciclo['duracion_dias']//7} semanas)")
                        # Usar el campo correcto para el ahorro acumulado
                        st.write(f"**Ahorro Acumulado:** ${ciclo.get('Ahorro_Real', 0) or 0:.2f}")
                    with col2:
                        st.write(f"**Grupos Asociados:** {ciclo['num_grupos']}")
                        if ciclo['grupos_nombres']:
                            st.write(f"**Nombres:** {ciclo['grupos_nombres']}")
                        st.write(f"**Estado:** {ciclo['estado']}")
                        # Calcular progreso si está activo
                        if ciclo['estado'] == 'Activo':
                            dias_totales = ciclo['duracion_dias']
                            dias_transcurridos = (datetime.now().date() - ciclo['Fecha_Inicio']).days
                            progreso = min(100, (dias_transcurridos / dias_totales) * 100)
                            st.progress(progreso / 100)
                            st.write(f"**Progreso:** {progreso:.1f}% ({dias_transcurridos}/{dias_totales} días)")
                    # Mostrar grupos del ciclo
                    if ciclo['num_grupos'] > 0:
                        st.write("---")
                        st.write("**Grupos en este ciclo:**")
                        cursor.execute("""
                            SELECT Id_grupo, Nombre, Numero_miembros 
                            FROM Grupos 
                            WHERE Id_Ciclo = %s
                            ORDER BY Nombre
                        """, (ciclo['Id_Ciclo'],))
                        grupos = cursor.fetchall()
                        for g in grupos:
                            st.write(f"- **{g['Nombre']}** (ID: {g['Id_grupo']}) - {g['Numero_miembros']} miembros")
    
    finally:
        conexion.close()


def crear_ciclo(id_distrito=None, solo_lectura=None):
    if solo_lectura is None:
        from modulos.solo_lectura import es_administradora
        solo_lectura = es_administradora()
    """
    Formulario para crear un nuevo ciclo.
    Los ciclos tienen una duración de 8 semanas (56 días).
    Si se proporciona id_distrito, solo permite asignar el ciclo a grupos de ese distrito.
    """
    st.subheader("Crear Nuevo Ciclo")
    st.info("Los ciclos tienen una duración estándar de **8 semanas (56 días)**")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Formulario de creación
        with st.form("form_crear_ciclo"):
            col1, col2 = st.columns(2)
            
            with col1:
                fecha_inicio = st.date_input(
                    "Fecha de Inicio*",
                    value=datetime.now().date(),
                    help="Fecha en que inicia el ciclo",
                    disabled=solo_lectura
                )
                # Calcular automáticamente la fecha fin (8 semanas = 56 días)
                fecha_fin_calculada = fecha_inicio + timedelta(days=56)
                st.info(f"Fecha de Fin (calculada): **{fecha_fin_calculada}**")
                st.write(f"Duración: **8 semanas (56 días)**")
            with col2:
                ahorro_inicial = st.number_input(
                    "Ahorro Acumulado Inicial",
                    min_value=0.0,
                    value=0.0,
                    step=0.01,
                    format="%.2f",
                    help="Monto inicial del ciclo (usualmente $0.00)",
                    disabled=solo_lectura
                )
            
            st.divider()
            st.write("**Asignar Grupos al Ciclo** (opcional)")
            
            # Obtener grupos disponibles (sin ciclo asignado o con ciclo completado)
            if id_distrito is not None:
                cursor.execute("""
                    SELECT g.Id_grupo, g.Nombre, g.Numero_miembros,
                           c.Fecha_Fin,
                           CASE 
                               WHEN c.Fecha_Fin IS NULL THEN 'Sin ciclo'
                               WHEN CURDATE() > c.Fecha_Fin THEN 'Ciclo completado'
                               ELSE 'En ciclo activo'
                           END as estado_ciclo
                    FROM Grupos g
                    LEFT JOIN Ciclo c ON g.Id_Ciclo = c.Id_Ciclo
                    WHERE g.distrito_id = %s
                    ORDER BY g.Nombre
                """, (id_distrito,))
            else:
                cursor.execute("""
                    SELECT g.Id_grupo, g.Nombre, g.Numero_miembros,
                           c.Fecha_Fin,
                           CASE 
                               WHEN c.Fecha_Fin IS NULL THEN 'Sin ciclo'
                               WHEN CURDATE() > c.Fecha_Fin THEN 'Ciclo completado'
                               ELSE 'En ciclo activo'
                           END as estado_ciclo
                    FROM Grupos g
                    LEFT JOIN Ciclo c ON g.Id_Ciclo = c.Id_Ciclo
                    ORDER BY g.Nombre
                """)
            grupos = cursor.fetchall()
            
            # Filtrar grupos disponibles
            grupos_disponibles = [g for g in grupos if g['estado_ciclo'] in ['Sin ciclo', 'Ciclo completado']]
            grupos_no_disponibles = [g for g in grupos if g['estado_ciclo'] == 'En ciclo activo']
            
            if grupos_disponibles:
                grupos_dict = {
                    f"{g['Nombre']} (ID: {g['Id_grupo']}, {g['Numero_miembros']} miembros)": g['Id_grupo'] 
                    for g in grupos_disponibles
                }
                grupos_seleccionados = st.multiselect(
                    "Selecciona grupos para asignar al ciclo",
                    list(grupos_dict.keys()),
                    help="Solo se muestran grupos sin ciclo activo",
                    disabled=solo_lectura
                )
                ids_grupos = [grupos_dict[g] for g in grupos_seleccionados]
            else:
                st.warning("No hay grupos disponibles. Todos los grupos están en ciclos activos.")
                ids_grupos = []
            
            if grupos_no_disponibles:
                with st.expander("Grupos NO disponibles (en ciclo activo)"):
                    for g in grupos_no_disponibles:
                        st.write(f"- {g['Nombre']} (finaliza: {g['Fecha_Fin']})")
            
            submitted = st.form_submit_button("Crear Ciclo", type="primary", disabled=solo_lectura)
            
            if submitted:
                # Validaciones
                if fecha_inicio < datetime.now().date():
                    st.warning("La fecha de inicio es anterior a hoy. ¿Estás seguro?")
                
                # Verificar solapamiento de fechas con ciclos existentes para los grupos seleccionados
                if ids_grupos:
                    placeholders = ','.join(['%s'] * len(ids_grupos))
                    cursor.execute(f"""
                        SELECT g.Nombre, c.Fecha_Inicio, c.Fecha_Fin
                        FROM Grupos g
                        JOIN Ciclo c ON g.Id_Ciclo = c.Id_Ciclo
                        WHERE g.Id_grupo IN ({placeholders})
                        AND (
                            (%s BETWEEN c.Fecha_Inicio AND c.Fecha_Fin) OR
                            (%s BETWEEN c.Fecha_Inicio AND c.Fecha_Fin) OR
                            (c.Fecha_Inicio BETWEEN %s AND %s)
                        )
                    """, ids_grupos + [fecha_inicio, fecha_fin_calculada, fecha_inicio, fecha_fin_calculada])
                    
                    conflictos = cursor.fetchall()
                    if conflictos:
                        st.error("❌ Conflicto de fechas detectado:")
                        for conf in conflictos:
                            st.write(f"- **{conf['Nombre']}** ya tiene un ciclo del {conf['Fecha_Inicio']} al {conf['Fecha_Fin']}")
                        return
                
                # Insertar el ciclo
                try:
                    sql = """
                    INSERT INTO Ciclo (Fecha_Inicio, Fecha_Fin, Ahorro_Acumulado)
                    VALUES (%s, %s, %s)
                    """
                    cursor.execute(sql, (fecha_inicio, fecha_fin_calculada, ahorro_inicial))
                    
                    # Obtener el ID del ciclo recién creado
                    id_ciclo_nuevo = cursor.lastrowid
                    
                    # Asignar grupos al ciclo
                    if ids_grupos:
                        for id_grupo in ids_grupos:
                            cursor.execute(
                                "UPDATE Grupos SET Id_Ciclo = %s WHERE Id_grupo = %s",
                                (id_ciclo_nuevo, id_grupo)
                            )
                    
                    conexion.commit()
                    st.success(f"Ciclo creado exitosamente con ID {id_ciclo_nuevo}!")
                    st.success(f"Duración: {fecha_inicio} al {fecha_fin_calculada} (8 semanas)")
                    
                    if ids_grupos:
                        st.info(f"{len(ids_grupos)} grupo(s) asignado(s) al ciclo.")
                    
                    st.balloons()
                    st.rerun()
                
                except Exception as e:
                    conexion.rollback()
                    st.error(f"Error al crear el ciclo: {str(e)}")
    
    finally:
        conexion.close()


def gestionar_estado_ciclos(id_distrito=None, id_grupo=None, solo_lectura=False):
    from modulos.solo_lectura import es_administradora
    solo_lectura = es_administradora()
    """
    Permite gestionar el estado de los ciclos: actualizar ahorro, finalizar ciclos, etc.
    Si se proporciona id_distrito, solo permite gestionar ciclos de ese distrito.
    """
    st.subheader("⚙️ Gestionar Estado de Ciclos")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Obtener ciclos activos y pendientes
        if id_grupo is not None:
            cursor.execute("""
                SELECT 
                    c.Id_Ciclo,
                    c.Fecha_Inicio,
                    c.Fecha_Fin,
                    c.Ahorro_Acumulado,
                    COUNT(DISTINCT g.Id_grupo) as num_grupos,
                    CASE 
                        WHEN CURDATE() < c.Fecha_Inicio THEN 'Pendiente'
                        WHEN CURDATE() BETWEEN c.Fecha_Inicio AND c.Fecha_Fin THEN 'Activo'
                        WHEN CURDATE() > c.Fecha_Fin THEN 'Completado'
                    END as estado
                FROM Ciclo c
                LEFT JOIN Grupos g ON g.Id_Ciclo = c.Id_Ciclo
                WHERE g.Id_grupo = %s
                GROUP BY c.Id_Ciclo
                HAVING estado IN ('Activo', 'Pendiente')
                ORDER BY c.Fecha_Inicio DESC
            """, (id_grupo,))
        elif id_distrito is not None:
            cursor.execute("""
                SELECT 
                    c.Id_Ciclo,
                    c.Fecha_Inicio,
                    c.Fecha_Fin,
                    c.Ahorro_Acumulado,
                    COUNT(DISTINCT g.Id_grupo) as num_grupos,
                    CASE 
                        WHEN CURDATE() < c.Fecha_Inicio THEN 'Pendiente'
                        WHEN CURDATE() BETWEEN c.Fecha_Inicio AND c.Fecha_Fin THEN 'Activo'
                        WHEN CURDATE() > c.Fecha_Fin THEN 'Completado'
                    END as estado
                FROM Ciclo c
                LEFT JOIN Grupos g ON g.Id_Ciclo = c.Id_Ciclo
                WHERE g.distrito_id = %s
                GROUP BY c.Id_Ciclo
                HAVING estado IN ('Activo', 'Pendiente')
                ORDER BY c.Fecha_Inicio DESC
            """, (id_distrito,))
        else:
            cursor.execute("""
                SELECT 
                    c.Id_Ciclo,
                    c.Fecha_Inicio,
                    c.Fecha_Fin,
                    c.Ahorro_Acumulado,
                    COUNT(DISTINCT g.Id_grupo) as num_grupos,
                    CASE 
                        WHEN CURDATE() < c.Fecha_Inicio THEN 'Pendiente'
                        WHEN CURDATE() BETWEEN c.Fecha_Inicio AND c.Fecha_Fin THEN 'Activo'
                        WHEN CURDATE() > c.Fecha_Fin THEN 'Completado'
                    END as estado
                FROM Ciclo c
                LEFT JOIN Grupos g ON g.Id_Ciclo = c.Id_Ciclo
                GROUP BY c.Id_Ciclo
                HAVING estado IN ('Activo', 'Pendiente')
                ORDER BY c.Fecha_Inicio DESC
            """)
        
        ciclos = cursor.fetchall()
        
        if not ciclos:
            st.info("📭 No hay ciclos activos o pendientes para gestionar.")
            st.write("Todos los ciclos están completados o no hay ciclos registrados.")
            return
        
        # Selector de ciclo
        ciclos_dict = {
            f"Ciclo {c['Id_Ciclo']} - {c['estado']} ({c['Fecha_Inicio']} / {c['Fecha_Fin']})": c['Id_Ciclo'] 
            for c in ciclos
        }
        ciclo_seleccionado = st.selectbox("🔍 Selecciona un ciclo", list(ciclos_dict.keys()))
        id_ciclo = ciclos_dict[ciclo_seleccionado]
        
        # Obtener datos del ciclo seleccionado
        ciclo = next(c for c in ciclos if c['Id_Ciclo'] == id_ciclo)
        
        st.divider()
        
        # Tabs para diferentes acciones
        tab1, tab2, tab3 = st.tabs(["Actualizar Ahorro", "Ver Detalles", "Finalizar Ciclo"])
        
        with tab1:
            st.write(f"**Ahorro Actual:** ${ciclo['Ahorro_Acumulado']:.2f}")
            
            with st.form("form_actualizar_ahorro"):
                nuevo_ahorro = st.number_input(
                    "💰 Nuevo Ahorro Acumulado",
                    min_value=0.0,
                    value=float(ciclo['Ahorro_Acumulado'] or 0),
                    step=0.01,
                    format="%.2f",
                    disabled=solo_lectura
                )
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Actualizar Ahorro", type="primary", disabled=solo_lectura):
                        try:
                            cursor.execute(
                                "UPDATE Ciclo SET Ahorro_Acumulado = %s WHERE Id_Ciclo = %s",
                                (nuevo_ahorro, id_ciclo)
                            )
                            conexion.commit()
                            st.success(f"✅ Ahorro actualizado a ${nuevo_ahorro:.2f}")
                            st.rerun()
                        except Exception as e:
                            conexion.rollback()
                            st.error(f"❌ Error: {str(e)}")
        
        with tab2:
            st.write("**Información del Ciclo:**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("📅 Fecha Inicio", str(ciclo['Fecha_Inicio']))
                st.metric("📅 Fecha Fin", str(ciclo['Fecha_Fin']))
                st.metric("💰 Ahorro Acumulado", f"${ciclo['Ahorro_Acumulado']:.2f}")
            
            with col2:
                # Convertir a date si son objetos datetime
                fecha_inicio = ciclo['Fecha_Inicio'] if isinstance(ciclo['Fecha_Inicio'], dt.date) else ciclo['Fecha_Inicio']
                fecha_fin = ciclo['Fecha_Fin'] if isinstance(ciclo['Fecha_Fin'], dt.date) else ciclo['Fecha_Fin']
                dias_totales = (fecha_fin - fecha_inicio).days
                st.metric("⏱️ Duración Total", f"{dias_totales} días")
                st.metric("👥 Grupos Asignados", ciclo['num_grupos'])
                st.metric("📊 Estado", ciclo['estado'])
            
            # Mostrar grupos del ciclo
            if ciclo['num_grupos'] > 0:
                st.write("---")
                st.write("**👥 Grupos en este ciclo:**")
                
                cursor.execute("""
                    SELECT g.Id_grupo, g.Nombre, g.Numero_miembros,
                           COUNT(m.id) as miembros_reales
                    FROM Grupos g
                    LEFT JOIN Miembros m ON g.Id_grupo = m.grupo_id
                    WHERE g.Id_Ciclo = %s
                    GROUP BY g.Id_grupo
                    ORDER BY g.Nombre
                """, (id_ciclo,))
                grupos = cursor.fetchall()
                
                df_grupos = pd.DataFrame(grupos)
                df_grupos = df_grupos.rename(columns={
                    'Id_grupo': 'ID',
                    'Nombre': 'Nombre',
                    'Numero_miembros': 'Miembros (config)',
                    'miembros_reales': 'Miembros (reales)'
                })
                st.dataframe(df_grupos, use_container_width=True, hide_index=True)
        
        with tab3:
            st.warning("⚠️ **Finalizar Ciclo**")
            
            if ciclo['estado'] == 'Completado':
                st.info("ℹ️ Este ciclo ya está completado (fecha fin superada).")
            elif ciclo['estado'] == 'Pendiente':
                st.info("ℹ️ Este ciclo aún no ha comenzado. Espera a que esté activo para finalizarlo.")
            else:
                st.write("Al finalizar el ciclo manualmente:")
                st.write("- Los grupos asociados quedarán sin ciclo asignado")
                st.write("- El ciclo quedará marcado como completado")
                st.write("- Esta acción NO se puede deshacer")
                
                confirmar = st.checkbox("Confirmo que deseo finalizar este ciclo", disabled=solo_lectura)
                
                # Validar préstamos pendientes según el contexto
                prestamos_pendientes = 0
                prestamos_detalle = []
                if id_grupo is not None:
                    # Solo para el grupo propio (directiva)
                    cursor.execute("""
                        SELECT COUNT(*) as pendientes FROM Prestamos p
                        INNER JOIN Grupos g ON p.Id_grupo = g.Id_grupo
                        WHERE g.Id_grupo = %s AND p.Estado IN ('Pendiente', 'Vencido')
                    """, (id_grupo,))
                    prestamos_pendientes = cursor.fetchone()['pendientes']
                else:
                    # Para todos los grupos asociados al ciclo (promotora, administradora)
                    cursor.execute("""
                        SELECT g.Nombre, COUNT(p.Id_prestamo) as pendientes
                        FROM Grupos g
                        LEFT JOIN Prestamos p ON p.Id_grupo = g.Id_grupo AND p.Estado IN ('Pendiente', 'Vencido')
                        WHERE g.Id_Ciclo = %s
                        GROUP BY g.Id_grupo
                    """, (id_ciclo,))
                    prestamos_grupos = cursor.fetchall()
                    prestamos_pendientes = sum(g['pendientes'] for g in prestamos_grupos)
                    prestamos_detalle = [f"{g['Nombre']}: {g['pendientes']} préstamo(s) pendiente(s)" for g in prestamos_grupos if g['pendientes'] > 0]
                if prestamos_pendientes > 0:
                    st.error(f"No se puede finalizar el ciclo: hay {prestamos_pendientes} préstamo(s) pendiente(s) de pago en el/los grupo(s).")
                    if prestamos_detalle:
                        st.warning("Detalle de préstamos pendientes:")
                        for detalle in prestamos_detalle:
                            st.write(f"- {detalle}")
                elif st.button("🏁 Finalizar Ciclo Ahora", type="secondary", disabled=not confirmar or solo_lectura):
                    try:
                        # Actualizar fecha fin a hoy
                        cursor.execute(
                            "UPDATE Ciclo SET Fecha_Fin = CURDATE() WHERE Id_Ciclo = %s",
                            (id_ciclo,)
                        )
                        # Desasignar grupos
                        cursor.execute(
                            "UPDATE Grupos SET Id_Ciclo = NULL WHERE Id_Ciclo = %s",
                            (id_ciclo,)
                        )
                        conexion.commit()
                        st.success(f"✅ Ciclo {id_ciclo} finalizado correctamente.")
                        st.info("Los grupos han sido desasignados y pueden ser asignados a un nuevo ciclo.")
                        st.rerun()
                    except Exception as e:
                        conexion.rollback()
                        st.error(f"❌ Error al finalizar ciclo: {str(e)}")
    
    finally:
        conexion.close()
