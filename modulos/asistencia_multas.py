import streamlit as st
from modulos.config.conexion import obtener_conexion
import pandas as pd
from datetime import datetime, date, time, timedelta


def gestionar_asistencia_multas(id_distrito=None):
    """
    Función principal para gestionar asistencia y multas.
    """
    st.title("📋 Gestión de Asistencia y Multas")
    
    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Reuniones", 
        "✅ Asistencia", 
        "💰 Multas",
        "⚙️ Configuración"
    ])
    
    with tab1:
        gestionar_reuniones(id_distrito=id_distrito, id_grupo=globals().get('id_grupo', None))
    with tab2:
        registrar_asistencia(id_distrito=id_distrito, id_grupo=globals().get('id_grupo', None))
    with tab3:
        gestionar_multas(id_distrito=id_distrito, id_grupo=globals().get('id_grupo', None))
    with tab4:
        configurar_multas(id_distrito=id_distrito, id_grupo=globals().get('id_grupo', None))

def gestionar_asistencia_multas(id_distrito=None, id_grupo=None):
    """
    Función principal para gestionar asistencia y multas.
    """
    st.title("📋 Gestión de Asistencia y Multas")
    
    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Reuniones", 
        "✅ Asistencia", 
        "💰 Multas",
        "⚙️ Configuración"
    ])
    
    with tab1:
        gestionar_reuniones(id_distrito=id_distrito, id_grupo=id_grupo)
    with tab2:
        registrar_asistencia(id_distrito=id_distrito, id_grupo=id_grupo)
    with tab3:
        gestionar_multas(id_distrito=id_distrito, id_grupo=id_grupo)
    with tab4:
        configurar_multas(id_distrito=id_distrito, id_grupo=id_grupo)


def gestionar_reuniones(id_distrito=None, id_grupo=None):
    """
    Gestión de reuniones programadas para los grupos.
    """
    st.subheader("📅 Gestión de Reuniones")
    
    tab1, tab2 = st.tabs(["📋 Ver Reuniones", "➕ Programar Reunión"])
    
    with tab1:
        ver_reuniones(id_distrito=id_distrito, id_grupo=id_grupo)
    with tab2:
        programar_reunion(id_distrito=id_distrito, id_grupo=id_grupo)


def ver_reuniones(id_distrito=None, id_grupo=None):
    """
    Muestra todas las reuniones programadas.
    """
    st.write("### 📋 Lista de Reuniones")
    if id_grupo:
        # Mostrar solo el grupo de pertenencia como opción única en el filtro
        conexion = obtener_conexion()
        nombre_grupo = None
        if conexion:
            try:
                cursor_tmp = conexion.cursor(dictionary=True)
                cursor_tmp.execute("SELECT Nombre FROM Grupos WHERE Id_grupo = %s", (id_grupo,))
                row = cursor_tmp.fetchone()
                if row:
                    nombre_grupo = row['Nombre']
            except Exception:
                pass
        if nombre_grupo:
            st.selectbox("Grupo", [nombre_grupo], index=0, disabled=True)
        if not conexion:
            st.error("❌ Error de conexión a la base de datos.")
            return
        cursor = conexion.cursor(dictionary=True)
    elif id_distrito is not None:
        # Mostrar todos los grupos del distrito como filtro
        conexion = obtener_conexion()
        grupos = []
        if conexion:
            try:
                cursor_tmp = conexion.cursor(dictionary=True)
                cursor_tmp.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE distrito_id = %s ORDER BY Nombre", (id_distrito,))
                grupos = cursor_tmp.fetchall()
            except Exception:
                pass
        if grupos:
            opciones = {g['Nombre']: g['Id_grupo'] for g in grupos}
            grupo_sel = st.selectbox("Grupo", list(opciones.keys()))
            id_grupo = opciones[grupo_sel]
        if not conexion:
            st.error("❌ Error de conexión a la base de datos.")
            return
        cursor = conexion.cursor(dictionary=True)
    else:
        conexion = obtener_conexion()
        if not conexion:
            st.error("❌ Error de conexión a la base de datos.")
            return
        cursor = conexion.cursor(dictionary=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            cursor.execute("SELECT Id_grupo, Nombre FROM Grupos ORDER BY Nombre")
            grupos = cursor.fetchall()
            grupos_dict = {"Todos los grupos": None}
            grupos_dict.update({g['Nombre']: g['Id_grupo'] for g in grupos})
            grupo_filtro = st.selectbox("Filtrar por Grupo", list(grupos_dict.keys()))
        if grupo_filtro != "Todos los grupos":
            cursor.execute("""
                SELECT r.*, g.Nombre AS nombre_grupo,
                    (SELECT COUNT(*) FROM Asistencia a WHERE a.Id_reunion = r.Id_reunion AND a.Estado_asistencia = 'Presente') AS Presentes,
                    (SELECT COUNT(*) FROM Asistencia a WHERE a.Id_reunion = r.Id_reunion AND a.Estado_asistencia = 'Tardanza') AS Tardanzas,
                    (SELECT COUNT(*) FROM Asistencia a WHERE a.Id_reunion = r.Id_reunion AND a.Estado_asistencia = 'Ausente') AS Ausentes,
                    (SELECT COUNT(*) FROM Asistencia a WHERE a.Id_reunion = r.Id_reunion) AS Total_Asistencias
                FROM Reuniones r
                LEFT JOIN Grupos g ON r.Id_grupo = g.Id_grupo
                WHERE r.Id_grupo = %s
                ORDER BY r.Fecha_reunion DESC
            """, (grupos_dict[grupo_filtro],))
            reuniones = cursor.fetchall()
        else:
            cursor.execute("""
                SELECT r.*, g.Nombre AS nombre_grupo,
                    (SELECT COUNT(*) FROM Asistencia a WHERE a.Id_reunion = r.Id_reunion AND a.Estado_asistencia = 'Presente') AS Presentes,
                    (SELECT COUNT(*) FROM Asistencia a WHERE a.Id_reunion = r.Id_reunion AND a.Estado_asistencia = 'Tardanza') AS Tardanzas,
                    (SELECT COUNT(*) FROM Asistencia a WHERE a.Id_reunion = r.Id_reunion AND a.Estado_asistencia = 'Ausente') AS Ausentes,
                    (SELECT COUNT(*) FROM Asistencia a WHERE a.Id_reunion = r.Id_reunion) AS Total_Asistencias
                FROM Reuniones r
                LEFT JOIN Grupos g ON r.Id_grupo = g.Id_grupo
                ORDER BY r.Fecha_reunion DESC
            """)
            reuniones = cursor.fetchall()
        programadas = len([r for r in reuniones if r['Estado'] == 'Programada'])
        st.metric("📅 Programadas", programadas)
        with col3:
            canceladas = len([r for r in reuniones if r['Estado'] == 'Cancelada'])
            st.metric("❌ Canceladas", canceladas)
        st.divider()
        if not reuniones:
            st.info("📭 No hay reuniones registradas para este grupo o filtro.")
            conexion.close()
            return
        # Mostrar reuniones (fuera de else para todos los casos)
        for reunion in reuniones:
            estado_emoji = {
                'Programada': '📅',
                'Realizada': '✅',
                'Cancelada': '❌'
            }
            with st.expander(f"{estado_emoji.get(reunion['Estado'], '📋')} {reunion.get('Nombre_Grupo', reunion.get('nombre_grupo', ''))} - Semana {reunion['Numero_semana']} ({reunion['Fecha_reunion']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**📅 Fecha:** {reunion['Fecha_reunion']}")
                    st.write(f"**🔢 Semana del Ciclo:** {reunion['Numero_semana']}")
                    st.write(f"**🕐 Hora Inicio:** {reunion['Hora_inicio'] or 'No definida'}")
                    st.write(f"**🕐 Hora Fin:** {reunion['Hora_fin'] or 'No definida'}")
                    st.write(f"**📍 Lugar:** {reunion['Lugar'] or 'No definido'}")
                with col2:
                    st.write(f"**👥 Grupo:** {reunion.get('Nombre_Grupo', reunion.get('nombre_grupo', ''))}")
                    st.write(f"**📊 Estado:** {reunion['Estado']}")
                    st.write(f"**✅ Presentes:** {reunion.get('Presentes', 0) or 0}")
                    st.write(f"**⏰ Presentes con Tardanza:** {reunion.get('Tardanzas', 0) or 0}")
                    st.write(f"**❌ Ausentes:** {reunion.get('Ausentes', 0) or 0}")
                    st.write(f"**📋 Total Registrado:** {reunion.get('Total_Asistencias', 0) or 0}")
                if reunion['Observaciones']:
                    st.info(f"📝 Observaciones: {reunion['Observaciones']}")
                # Botones de acción
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button(f"✅ Marcar Realizada", key=f"realizada_{reunion['Id_reunion']}"):
                        cursor.execute(
                            "UPDATE Reuniones SET Estado = 'Realizada' WHERE Id_reunion = %s",
                            (reunion['Id_reunion'],)
                        )
                        conexion.commit()
                        st.success("Reunión marcada como realizada")
                        st.rerun()
                with col_btn2:
                    if st.button(f"❌ Cancelar", key=f"cancelar_{reunion['Id_reunion']}"):
                        cursor.execute(
                            "UPDATE Reuniones SET Estado = 'Cancelada' WHERE Id_reunion = %s",
                            (reunion['Id_reunion'],)
                        )
                        conexion.commit()
                        st.warning("Reunión cancelada")
                        st.rerun()
        conexion.close()
        return
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        try:
            if id_grupo:
                cursor.execute("""
                    SELECT r.*, g.Nombre AS nombre_grupo,
                        (SELECT COUNT(*) FROM Asistencia a WHERE a.Id_reunion = r.Id_reunion AND a.Estado_asistencia = 'Presente') AS Presentes,
                        (SELECT COUNT(*) FROM Asistencia a WHERE a.Id_reunion = r.Id_reunion AND a.Estado_asistencia = 'Tardanza') AS Tardanzas,
                        (SELECT COUNT(*) FROM Asistencia a WHERE a.Id_reunion = r.Id_reunion AND a.Estado_asistencia = 'Ausente') AS Ausentes,
                        (SELECT COUNT(*) FROM Asistencia a WHERE a.Id_reunion = r.Id_reunion) AS Total_Asistencias
                    FROM Reuniones r
                    LEFT JOIN Grupos g ON r.Id_grupo = g.Id_grupo
                    WHERE r.Id_grupo = %s
                    ORDER BY r.Fecha_reunion DESC
                """, (id_grupo,))
                reuniones = cursor.fetchall()
            elif id_distrito is not None:
                cursor.execute("""
                    SELECT r.*, g.Nombre AS nombre_grupo,
                        (SELECT COUNT(*) FROM Asistencia a WHERE a.Id_reunion = r.Id_reunion AND a.Estado_asistencia = 'Presente') AS Presentes,
                        (SELECT COUNT(*) FROM Asistencia a WHERE a.Id_reunion = r.Id_reunion AND a.Estado_asistencia = 'Tardanza') AS Tardanzas,
                        (SELECT COUNT(*) FROM Asistencia a WHERE a.Id_reunion = r.Id_reunion AND a.Estado_asistencia = 'Ausente') AS Ausentes,
                        (SELECT COUNT(*) FROM Asistencia a WHERE a.Id_reunion = r.Id_reunion) AS Total_Asistencias
                    FROM Reuniones r
                    LEFT JOIN Grupos g ON r.Id_grupo = g.Id_grupo
                    WHERE g.distrito_id = %s
                    ORDER BY r.Fecha_reunion DESC
                """, (id_distrito,))
                reuniones = cursor.fetchall()
            # El caso else ya fue manejado arriba para administradora
        finally:
            if 'conexion' in locals() and conexion:
                conexion.close()

def programar_reunion(id_distrito=None, id_grupo=None):
    """
    Formulario para programar nuevas reuniones.
    """
    st.write("### ➕ Programar Nueva Reunión")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        with st.form("form_programar_reunion"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Solo permitir seleccionar el grupo asignado si corresponde
                if id_grupo:
                    cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE Id_grupo = %s ORDER BY Nombre", (id_grupo,))
                elif id_distrito is not None:
                    cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE distrito_id = %s ORDER BY Nombre", (id_distrito,))
                else:
                    cursor.execute("SELECT Id_grupo, Nombre FROM Grupos ORDER BY Nombre")
                grupos = cursor.fetchall()
                if not grupos:
                    st.error("No hay grupos registrados")
                    return
                grupos_dict = {f"{g['Nombre']} (ID: {g['Id_grupo']})": g['Id_grupo'] for g in grupos}
                grupo_sel = st.selectbox("👥 Grupo*", list(grupos_dict.keys()), index=0)
                id_grupo = grupos_dict[grupo_sel]
                
                # Seleccionar ciclo
                cursor.execute("""
                    SELECT c.Id_Ciclo, c.Fecha_Inicio, c.Fecha_Fin
                    FROM Ciclo c
                    JOIN Grupos g ON g.Id_Ciclo = c.Id_Ciclo
                    WHERE g.Id_grupo = %s
                    ORDER BY c.Fecha_Inicio DESC
                """, (id_grupo,))
                ciclos = cursor.fetchall()
                
                if not ciclos:
                    st.warning("El grupo seleccionado no tiene ciclo asignado")
                    ciclos_dict = {}
                else:
                    ciclos_dict = {
                        f"Ciclo {c['Id_Ciclo']} ({c['Fecha_Inicio']} - {c['Fecha_Fin']})": c['Id_Ciclo'] 
                        for c in ciclos
                    }
                
                if ciclos_dict:
                    ciclo_sel = st.selectbox("🔄 Ciclo*", list(ciclos_dict.keys()))
                    id_ciclo = ciclos_dict[ciclo_sel]
                else:
                    id_ciclo = None
                
                fecha_reunion = st.date_input("📅 Fecha de Reunión*", value=date.today())
                numero_semana = st.number_input("🔢 Número de Semana (1-8)*", min_value=1, max_value=8, value=1)
            
            with col2:
                hora_inicio = st.time_input("🕐 Hora de Inicio", value=time(9, 0))
                hora_fin = st.time_input("🕐 Hora de Fin", value=time(11, 0))
                lugar = st.text_input("📍 Lugar de Reunión")
                observaciones = st.text_area("📝 Observaciones")
            
            submitted = st.form_submit_button("✅ Programar Reunión", type="primary")
            
            if submitted:
                if not id_ciclo:
                    st.error("El grupo debe tener un ciclo asignado")
                    return
                
                try:
                    sql = """
                    INSERT INTO Reuniones (Id_grupo, Id_Ciclo, Fecha_reunion, Numero_semana, Hora_inicio, Hora_fin, Lugar, Observaciones)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        id_grupo, id_ciclo, fecha_reunion, numero_semana,
                        hora_inicio, hora_fin, lugar, observaciones
                    ))
                    conexion.commit()
                    st.success("✅ Reunión programada exitosamente")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    conexion.rollback()
                    st.error(f"❌ Error: {str(e)}")
    
    finally:
        conexion.close()


def registrar_asistencia(id_distrito=None, id_grupo=None):
    """
    Registro de asistencia a reuniones con causas de ausencia diferenciadas.
    """
    st.subheader("✅ Registro de Asistencia")
    
    st.info("💡 **Tipos de asistencia:**\n"
            "- ✅ **Presente**: Miembro asistió a la reunión\n"
            "- ❌ **Ausente (Injustificada)**: No asistió sin justificación → Genera multa automáticamente\n"
            "- 📋 **Ausente (Justificada)**: No asistió con justificación válida → NO genera multa\n"
            "- ⏰ **Tardanza**: Llegó tarde → Puede generar multa según configuración\n"
            "- 📝 **Otras Razones**: Situaciones especiales")

    # Si no se recibe id_grupo pero sí id_distrito, permitir seleccionar grupo del distrito
    if id_grupo is None and id_distrito is not None:
        conexion_tmp = obtener_conexion()
        grupos = []
        if conexion_tmp:
            try:
                cursor_tmp = conexion_tmp.cursor(dictionary=True)
                cursor_tmp.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE distrito_id = %s ORDER BY Nombre", (id_distrito,))
                grupos = cursor_tmp.fetchall()
            except Exception:
                pass
            finally:
                conexion_tmp.close()
        if grupos:
            opciones = {g['Nombre']: g['Id_grupo'] for g in grupos}
            grupo_sel = st.selectbox("Grupo", list(opciones.keys()), key="grupo_asistencia_select")
            id_grupo = opciones[grupo_sel]
    # Si no se recibe id_grupo ni id_distrito (administrador), permitir seleccionar cualquier grupo
    if id_grupo is None and id_distrito is None:
        conexion_tmp = obtener_conexion()
        grupos = []
        if conexion_tmp:
            try:
                cursor_tmp = conexion_tmp.cursor(dictionary=True)
                cursor_tmp.execute("SELECT Id_grupo, Nombre FROM Grupos ORDER BY Nombre")
                grupos = cursor_tmp.fetchall()
            except Exception:
                pass
            finally:
                conexion_tmp.close()
        if grupos:
            opciones = {g['Nombre']: g['Id_grupo'] for g in grupos}
            grupo_sel = st.selectbox("Grupo", list(opciones.keys()), key="grupo_asistencia_admin_select")
            id_grupo = opciones[grupo_sel]
    # Si sigue sin id_grupo, intentar obtenerlo del usuario
    if id_grupo is None:
        id_grupo = st.session_state.get('usuario', {}).get('Id_grupo') if 'usuario' in st.session_state else None
    if id_grupo is None:
        st.error("No se pudo determinar el grupo del usuario. Contacte al administrador.")
        return

    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return

    cursor = conexion.cursor(dictionary=True)

    try:
        # Seleccionar reuniones según el contexto
        if id_grupo is not None:
            cursor.execute("""
                SELECT 
                    r.Id_reunion,
                    r.Fecha_reunion,
                    r.Numero_semana,
                    r.Estado,
                    g.Nombre AS Nombre_Grupo,
                    g.Id_grupo,
                    c.Id_Ciclo
                FROM Reuniones r
                JOIN Grupos g ON r.Id_grupo = g.Id_grupo
                JOIN Ciclo c ON r.Id_Ciclo = c.Id_Ciclo
                WHERE r.Id_grupo = %s
                ORDER BY r.Fecha_reunion DESC
                LIMIT 50
            """, (id_grupo,))
        elif id_distrito is not None:
            cursor.execute("""
                SELECT 
                    r.Id_reunion,
                    r.Fecha_reunion,
                    r.Numero_semana,
                    r.Estado,
                    g.Nombre AS Nombre_Grupo,
                    g.Id_grupo,
                    c.Id_Ciclo
                FROM Reuniones r
                JOIN Grupos g ON r.Id_grupo = g.Id_grupo
                JOIN Ciclo c ON r.Id_Ciclo = c.Id_Ciclo
                WHERE g.distrito_id = %s
                ORDER BY r.Fecha_reunion DESC
                LIMIT 50
            """, (id_distrito,))
        else:
            cursor.execute("""
                SELECT 
                    r.Id_reunion,
                    r.Fecha_reunion,
                    r.Numero_semana,
                    r.Estado,
                    g.Nombre AS Nombre_Grupo,
                    g.Id_grupo,
                    c.Id_Ciclo
                FROM Reuniones r
                JOIN Grupos g ON r.Id_grupo = g.Id_grupo
                JOIN Ciclo c ON r.Id_Ciclo = c.Id_Ciclo
                ORDER BY r.Fecha_reunion DESC
                LIMIT 50
            """)
        reuniones = cursor.fetchall()
        if not reuniones:
            st.info("📭 No hay reuniones disponibles para registrar asistencia")
            return
        reuniones_dict = {
            f"{r['Nombre_Grupo']} - Semana {r['Numero_semana']} ({r['Fecha_reunion']}) [{r['Estado']}]": r['Id_reunion']
            for r in reuniones
        }
        reunion_sel = st.selectbox("🔍 Seleccionar Reunión", list(reuniones_dict.keys()))
        id_reunion = reuniones_dict[reunion_sel]
        # Obtener datos de la reunión seleccionada
        reunion = next(r for r in reuniones if r['Id_reunion'] == id_reunion)
        
        st.divider()
        
        # Obtener miembros del grupo
        cursor.execute("""
            SELECT id, nombre, Numero_Telefono
            FROM Miembros
            WHERE grupo_id = %s
            ORDER BY nombre
        """, (reunion['Id_grupo'],))
        miembros = cursor.fetchall()
        
        if not miembros:
            st.warning("El grupo no tiene miembros registrados")
            return
        
        st.write(f"**👥 Grupo:** {reunion['Nombre_Grupo']}")
        st.write(f"**📅 Fecha:** {reunion['Fecha_reunion']}")
        st.write(f"**🔢 Semana:** {reunion['Numero_semana']}")
        
        st.divider()
        st.write("### 📝 Registrar Asistencia por Miembro")
        
        # Obtener asistencias ya registradas
        cursor.execute("""
            SELECT Id_miembro, Estado_asistencia, Hora_llegada, Observaciones
            FROM Asistencia
            WHERE Id_reunion = %s
        """, (id_reunion,))
        asistencias_existentes = {a['Id_miembro']: a for a in cursor.fetchall()}
        
        # Formulario de asistencia
        asistencias_nuevas = []
        
        # Opciones de estado - Mapeo de display a valores de BD
        estados_display = ['✅ Presente', '❌ Ausente (Injustificada)', '📋 Ausente (Justificada)', '⏰ Tardanza', '📝 Otras Razones']
        estados_bd = ['Presente', 'Ausente', 'Justificado', 'Tardanza', 'Otro']
        
        from datetime import datetime
        fecha_reunion_dt = datetime.strptime(str(reunion['Fecha_reunion']), "%Y-%m-%d")
        reunion_pasada = fecha_reunion_dt.date() < datetime.now().date()
        for miembro in miembros:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
                asist_existente = asistencias_existentes.get(miembro['id'])
                disabled = bool(asist_existente) or reunion_pasada
                with col1:
                    st.write(f"**{miembro['nombre']}**")
                with col2:
                    # Mapear el estado existente al índice correcto
                    if asist_existente:
                        estado_guardado = asist_existente['Estado_asistencia']
                        mapeo_bd_a_idx = {
                            'Presente': 0,
                            'Ausente': 1,
                            'Justificado': 2,
                            'Tardanza': 3,
                            'Otro': 4
                        }
                        idx_default = mapeo_bd_a_idx.get(estado_guardado, 0)
                    else:
                        idx_default = 0
                    estado_display_sel = st.selectbox(
                        "Estado",
                        estados_display,
                        index=idx_default,
                        key=f"estado_{miembro['id']}",
                        label_visibility="collapsed",
                        disabled=disabled
                    )
                    idx_seleccionado = estados_display.index(estado_display_sel)
                    estado = estados_bd[idx_seleccionado]
                with col3:
                    if asist_existente and asist_existente['Hora_llegada']:
                        hora_td = asist_existente['Hora_llegada']
                        if isinstance(hora_td, timedelta):
                            total_seconds = int(hora_td.total_seconds())
                            hours = total_seconds // 3600
                            minutes = (total_seconds % 3600) // 60
                            hora_default = time(hours, minutes)
                        else:
                            hora_default = hora_td
                    else:
                        hora_default = time(9, 0)
                    hora_llegada = st.time_input(
                        "Hora",
                        value=hora_default,
                        key=f"hora_{miembro['id']}",
                        label_visibility="collapsed",
                        disabled=disabled
                    )
                with col4:
                    obs_default = asist_existente['Observaciones'] if asist_existente else ""
                    observaciones = st.text_input(
                        "Observaciones",
                        value=obs_default,
                        key=f"obs_{miembro['id']}",
                        label_visibility="collapsed",
                        placeholder="Observaciones...",
                        disabled=disabled
                    )
                asistencias_nuevas.append({
                    'id_miembro': miembro['id'],
                    'nombre': miembro['nombre'],
                    'estado': estado,
                    'hora': hora_llegada,
                    'observaciones': observaciones
                })
        
        st.divider()
        # Mostrar resumen real de la base de datos si ya existe asistencia
        cursor.execute("SELECT COUNT(*) as total FROM Asistencia WHERE Id_reunion = %s", (id_reunion,))
        total_asistencias = cursor.fetchone()['total']
        col_res1, col_res2, col_res3, col_res4, col_res5, col_res6 = st.columns(6)
        if total_asistencias > 0:
            # Resumen real de la base de datos
            cursor.execute("""
                SELECT Estado_asistencia, COUNT(*) as cantidad
                FROM Asistencia
                WHERE Id_reunion = %s
                GROUP BY Estado_asistencia
            """, (id_reunion,))
            resumen = {row['Estado_asistencia']: row['cantidad'] for row in cursor.fetchall()}
            presentes = resumen.get('Presente', 0)
            tardanzas = resumen.get('Tardanza', 0)
            presentes_totales = presentes + tardanzas
            ausentes_inj = resumen.get('Ausente', 0)
            ausentes_just = resumen.get('Justificado', 0)
            otras = resumen.get('Otro', 0)
        else:
            # Resumen de lo que se va a guardar
            presentes = sum(1 for a in asistencias_nuevas if a['estado'] == 'Presente')
            tardanzas = sum(1 for a in asistencias_nuevas if a['estado'] == 'Tardanza')
            presentes_totales = presentes + tardanzas
            ausentes_inj = sum(1 for a in asistencias_nuevas if a['estado'] == 'Ausente')
            ausentes_just = sum(1 for a in asistencias_nuevas if a['estado'] == 'Justificado')
            otras = sum(1 for a in asistencias_nuevas if a['estado'] == 'Otro')
        with col_res1:
            st.metric("✅ Presentes", presentes)
        with col_res2:
            st.metric("⏰ Presentes con Tardanza", tardanzas)
        with col_res3:
            st.metric("❌ Ausentes (Injust.)", ausentes_inj)
        with col_res4:
            st.metric("📋 Ausentes (Just.)", ausentes_just)
        with col_res5:
            st.metric("📝 Otras", otras)
        with col_res6:
            st.metric("👥 Total Presentes", presentes_totales)
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Verificar si ya existe asistencia para la reunión
            cursor.execute("SELECT COUNT(*) as total FROM Asistencia WHERE Id_reunion = %s", (id_reunion,))
            total_asistencias = cursor.fetchone()['total']
            if total_asistencias > 0:
                st.info("Esta asistencia ya fue guardada. Si necesitas modificarla, hazlo desde la gestión de asistencias.")
            else:
                if st.button("💾 Guardar Asistencia", type="primary", use_container_width=True):
                    try:
                        usuario_id = st.session_state.get('usuario', {}).get('Id_usuario')
                        registros_guardados = 0
                        for asist in asistencias_nuevas:
                            cursor.execute("SELECT 1 FROM Asistencia WHERE Id_reunion = %s AND Id_miembro = %s", (id_reunion, asist['id_miembro']))
                            if not cursor.fetchone():
                                cursor.execute("""
                                    INSERT INTO Asistencia 
                                    (Id_reunion, Id_miembro, Estado_asistencia, Hora_llegada, Observaciones, Registrado_por)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, (
                                    id_reunion,
                                    asist['id_miembro'],
                                    asist['estado'],
                                    asist['hora'],
                                    asist['observaciones'],
                                    usuario_id
                                ))
                                registros_guardados += 1
                        if registros_guardados > 0:
                            # Marcar la reunión como realizada si se guardó asistencia
                            cursor.execute("UPDATE Reuniones SET Estado = 'Realizada' WHERE Id_reunion = %s", (id_reunion,))
                            conexion.commit()
                            st.success(f"✅ Asistencia registrada para {registros_guardados} miembros")
                            st.rerun()
                        else:
                            st.info("No se registró ninguna asistencia nueva (ya existían)")
                    except Exception as e:
                        conexion.rollback()
                        st.error(f"❌ Error: {str(e)}")
        
        with col2:
            st.write("**Aplicar multas automáticas**")
            aplicar_multas_auto = st.checkbox("Generar multas por ausencias injustificadas y tardanzas", value=True)
            st.caption("💡 Las ausencias justificadas NO generan multas")
            
            if st.button("💰 Aplicar Multas", type="secondary", use_container_width=True, disabled=not aplicar_multas_auto):
                try:
                    usuario_id = st.session_state.get('usuario', {}).get('Id_usuario')
                    multas_aplicadas = 0
                    miembros_multados = []
                    
                    for asist in asistencias_nuevas:
                        # Solo aplicar multas a ausencias injustificadas y tardanzas
                        # 'Ausente' = Ausente Injustificada, 'Justificado' = Ausente Justificada (no genera multa)
                        if asist['estado'] in ['Ausente', 'Tardanza']:
                            tipo_multa = 'Inasistencia' if asist['estado'] == 'Ausente' else 'Tardanza'
                            
                            # Obtener monto de configuración
                            cursor.execute(
                                "SELECT Monto_default FROM Configuracion_Multas WHERE Tipo_multa = %s",
                                (tipo_multa,)
                            )
                            config = cursor.fetchone()
                            monto = config['Monto_default'] if config else 0
                            
                            if monto > 0:
                                # Verificar si ya existe una multa para esta reunión y miembro
                                cursor.execute("""
                                    SELECT Id_multa FROM Multas 
                                    WHERE Id_miembro = %s AND Id_reunion = %s AND Tipo_multa = %s
                                """, (asist['id_miembro'], id_reunion, tipo_multa))
                                
                                multa_existente = cursor.fetchone()
                                
                                if not multa_existente:
                                    cursor.execute("""
                                        INSERT INTO Multas 
                                        (Id_miembro, Id_grupo, Id_Ciclo, Id_reunion, Tipo_multa, Monto, Descripcion, Fecha_multa, Aplicado_por)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, CURDATE(), %s)
                                    """, (
                                        asist['id_miembro'],
                                        reunion['Id_grupo'],
                                        reunion['Id_Ciclo'],
                                        id_reunion,
                                        tipo_multa,
                                        monto,
                                        f"Multa automática por {tipo_multa.lower()} en reunión semana {reunion['Numero_semana']}",
                                        usuario_id
                                    ))
                                    multas_aplicadas += 1
                                    miembros_multados.append(f"{asist['nombre']} (${monto:.2f})")
                    
                    conexion.commit()
                    if multas_aplicadas > 0:
                        st.success(f"✅ {multas_aplicadas} multa(s) aplicada(s) automáticamente")
                        with st.expander("Ver detalles de multas aplicadas"):
                            for miembro_info in miembros_multados:
                                st.write(f"- {miembro_info}")
                        st.rerun()
                    else:
                        st.info("ℹ️ No se aplicaron multas nuevas (ya existentes, todos presentes o montos en $0)")
                except Exception as e:
                    conexion.rollback()
                    st.error(f"❌ Error: {str(e)}")
    
    finally:
        conexion.close()


def gestionar_multas(id_distrito=None, id_grupo=None):
    """
    Gestión de multas aplicadas a los miembros.
    """
    st.subheader("💰 Gestión de Multas")
    
    tab1, tab2, tab3 = st.tabs(["📋 Ver Multas", "➕ Aplicar Multa Manual", "📊 Reportes"])
    
    with tab1:
        ver_multas(id_grupo=id_grupo)
    
    with tab2:
        aplicar_multa_manual(id_grupo=id_grupo)
    
    with tab3:
        reportes_multas(id_grupo=id_grupo)


def ver_multas(id_grupo=None):
    """
    Muestra todas las multas registradas.
    """
    st.write("### 📋 Lista de Multas")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            estado_filtro = st.selectbox("Estado de Pago", ["Todas", "Pendiente", "Pagada", "Condonada"])
        
        with col2:
            tipo_filtro = st.selectbox("Tipo de Multa", ["Todas", "Inasistencia", "Tardanza", "Falta_Pago", "Incumplimiento", "Otro"])
        
        with col3:
            # Filtrar solo el grupo asignado si es promotora/directiva
            id_grupo_usuario = id_grupo
            if id_grupo_usuario:
                cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE Id_grupo = %s ORDER BY Nombre", (id_grupo_usuario,))
            else:
                cursor.execute("SELECT Id_grupo, Nombre FROM Grupos ORDER BY Nombre")
            grupos = cursor.fetchall()
            grupos_dict = {"Todos": None}
            grupos_dict.update({g['Nombre']: g['Id_grupo'] for g in grupos})
            grupo_filtro = st.selectbox("Grupo", list(grupos_dict.keys()), index=1 if id_grupo_usuario else 0)
            id_grupo_filtro = grupos_dict[grupo_filtro]
        
        # Construir consulta
        id_distrito = None
        if 'usuario' in st.session_state:
            usuario = st.session_state['usuario']
            id_distrito = usuario.get('Id_distrito') or usuario.get('id_distrito')
        query = """
            SELECT 
                mu.Id_multa,
                mu.Fecha_multa,
                mu.Tipo_multa,
                mu.Monto,
                mu.Estado_pago,
                mu.Fecha_pago,
                mu.Descripcion,
                m.nombre AS Nombre_Miembro,
                g.Nombre AS Nombre_Grupo,
                u.Nombre_Usuario AS Aplicado_Por
            FROM Multas mu
            JOIN Miembros m ON mu.Id_miembro = m.id
            JOIN Grupos g ON mu.Id_grupo = g.Id_grupo
            LEFT JOIN Usuarios u ON mu.Aplicado_por = u.Id_usuario
            WHERE 1=1
        """
        params = []
        # Si hay id_grupo (promotora/directiva), filtrar solo ese grupo
        if id_grupo:
            query += " AND mu.Id_grupo = %s"
            params.append(id_grupo)
        if estado_filtro != "Todas":
            query += " AND mu.Estado_pago = %s"
            params.append(estado_filtro)
        if tipo_filtro != "Todas":
            query += " AND mu.Tipo_multa = %s"
            params.append(tipo_filtro)
        if id_grupo_filtro:
            query += " AND mu.Id_grupo = %s"
            params.append(id_grupo_filtro)
        query += " ORDER BY mu.Fecha_multa DESC"
        cursor.execute(query, params)
        multas = cursor.fetchall()
        
        if not multas:
            st.info("📭 No hay multas que coincidan con los filtros")
        else:
            # Estadísticas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Multas", len(multas))
            with col2:
                pendientes = [m for m in multas if m['Estado_pago'] == 'Pendiente']
                monto_pendiente = sum([m['Monto'] for m in pendientes])
                st.metric("⏳ Pendientes", f"${monto_pendiente:.2f}")
            with col3:
                pagadas = [m for m in multas if m['Estado_pago'] == 'Pagada']
                monto_pagado = sum([m['Monto'] for m in pagadas])
                st.metric("✅ Pagadas", f"${monto_pagado:.2f}")
            with col4:
                total_monto = sum([m['Monto'] for m in multas])
                st.metric("💰 Total", f"${total_monto:.2f}")
            
            st.divider()
            
            # Tabla de multas
            df = pd.DataFrame(multas)
            df = df.rename(columns={
                'Id_multa': 'ID',
                'Fecha_multa': 'Fecha',
                'Tipo_multa': 'Tipo',
                'Monto': 'Monto ($)',
                'Estado_pago': 'Estado',
                'Nombre_Miembro': 'Miembro',
                'Nombre_Grupo': 'Grupo',
                'Aplicado_Por': 'Aplicado Por'
            })
            
            st.dataframe(
                df[['ID', 'Fecha', 'Tipo', 'Monto ($)', 'Estado', 'Miembro', 'Grupo']],
                use_container_width=True,
                hide_index=True
            )
            
            # Detalles expandibles
            st.divider()
            st.write("### ⚙️ Acciones sobre Multas")
            
            for multa in multas:
                estado_emoji = {'Pendiente': '⏳', 'Pagada': '✅', 'Condonada': '🔄'}
                
                with st.expander(f"{estado_emoji.get(multa['Estado_pago'], '💰')} {multa['Nombre_Miembro']} - ${multa['Monto']:.2f} ({multa['Fecha_multa']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**👤 Miembro:** {multa['Nombre_Miembro']}")
                        st.write(f"**👥 Grupo:** {multa['Nombre_Grupo']}")
                        st.write(f"**📅 Fecha:** {multa['Fecha_multa']}")
                        st.write(f"**💰 Monto:** ${multa['Monto']:.2f}")
                    
                    with col2:
                        st.write(f"**📋 Tipo:** {multa['Tipo_multa']}")
                        st.write(f"**📊 Estado:** {multa['Estado_pago']}")
                        if multa['Fecha_pago']:
                            st.write(f"**✅ Pagada el:** {multa['Fecha_pago']}")
                        st.write(f"**👤 Aplicada por:** {multa['Aplicado_Por'] or 'Sistema'}")
                    
                    if multa['Descripcion']:
                        st.info(f"📝 {multa['Descripcion']}")
                    
                    # Botones de acción
                    if multa['Estado_pago'] == 'Pendiente':
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            if st.button(f"✅ Marcar como Pagada", key=f"pagar_{multa['Id_multa']}"):
                                cursor.execute(
                                    "UPDATE Multas SET Estado_pago = 'Pagada', Fecha_pago = CURDATE() WHERE Id_multa = %s",
                                    (multa['Id_multa'],)
                                )
                                conexion.commit()
                                st.success("Multa marcada como pagada")
                                st.rerun()
                        
                        with col_btn2:
                            if st.button(f"🔄 Condonar", key=f"condonar_{multa['Id_multa']}"):
                                cursor.execute(
                                    "UPDATE Multas SET Estado_pago = 'Condonada' WHERE Id_multa = %s",
                                    (multa['Id_multa'],)
                                )
                                conexion.commit()
                                st.info("Multa condonada")
                                st.rerun()
    
    finally:
        conexion.close()


def aplicar_multa_manual(id_grupo=None):
    """
    Formulario para aplicar multas manualmente.
    """
    st.write("### ➕ Aplicar Multa Manual")
    
    st.info("💡 Utiliza este formulario para aplicar multas por razones específicas fuera del proceso automático de asistencia.")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        with st.form("form_aplicar_multa"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Seleccionar grupo (solo el asignado si corresponde)
                if id_grupo:
                    cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE Id_grupo = %s ORDER BY Nombre", (id_grupo,))
                else:
                    cursor.execute("SELECT Id_grupo, Nombre FROM Grupos ORDER BY Nombre")
                grupos = cursor.fetchall()
                grupos_dict = {g['Nombre']: g['Id_grupo'] for g in grupos}
                grupo_sel = st.selectbox("👥 Grupo*", list(grupos_dict.keys()), index=0)
                id_grupo = grupos_dict[grupo_sel]
                
                # Seleccionar miembro
                cursor.execute(
                    "SELECT id, nombre FROM Miembros WHERE grupo_id = %s ORDER BY nombre",
                    (id_grupo,)
                )
                miembros = cursor.fetchall()
                
                if not miembros:
                    st.warning("El grupo no tiene miembros")
                    return
                
                miembros_dict = {m['nombre']: m['id'] for m in miembros}
                miembro_sel = st.selectbox("👤 Miembro*", list(miembros_dict.keys()))
                id_miembro = miembros_dict[miembro_sel]
                
                # Obtener ciclo del grupo
                cursor.execute(
                    "SELECT Id_Ciclo FROM Grupos WHERE Id_grupo = %s",
                    (id_grupo,)
                )
                grupo_info = cursor.fetchone()
                id_ciclo = grupo_info['Id_Ciclo'] if grupo_info else None
                
                if not id_ciclo:
                    st.warning("El grupo no tiene ciclo asignado")
                
                tipo_multa = st.selectbox(
                    "📋 Tipo de Multa*",
                    ['Inasistencia', 'Tardanza', 'Falta_Pago', 'Incumplimiento', 'Otro']
                )
            
            with col2:
                # Obtener monto sugerido
                cursor.execute(
                    "SELECT Monto_default FROM Configuracion_Multas WHERE Tipo_multa = %s",
                    (tipo_multa,)
                )
                config = cursor.fetchone()
                monto_sugerido = config['Monto_default'] if config else 0.0
                
                monto = st.number_input(
                    "💰 Monto*",
                    min_value=0.0,
                    value=float(monto_sugerido),
                    step=0.01,
                    format="%.2f"
                )
                
                fecha_multa = st.date_input("📅 Fecha de la Multa*", value=date.today())
                
                descripcion = st.text_area("📝 Descripción/Motivo*", height=100, 
                                           placeholder="Describe la razón de la multa...")
            
            submitted = st.form_submit_button("✅ Aplicar Multa", type="primary")
            
            if submitted:
                if not id_ciclo:
                    st.error("El grupo debe tener un ciclo asignado")
                    return
                
                if not descripcion:
                    st.error("La descripción es obligatoria")
                    return
                
                try:
                    usuario_id = st.session_state.get('usuario', {}).get('Id_usuario')
                    
                    cursor.execute("""
                        INSERT INTO Multas 
                        (Id_miembro, Id_grupo, Id_Ciclo, Tipo_multa, Monto, Descripcion, Fecha_multa, Aplicado_por)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        id_miembro, id_grupo, id_ciclo, tipo_multa,
                        monto, descripcion, fecha_multa, usuario_id
                    ))
                    
                    conexion.commit()
                    st.success(f"✅ Multa de ${monto:.2f} aplicada a {miembro_sel}")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    conexion.rollback()
                    st.error(f"❌ Error: {str(e)}")
    
    finally:
        conexion.close()


def reportes_multas(id_grupo=None):
    """
    Reportes y estadísticas de multas.
    """
    st.write("### 📊 Reportes de Multas")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Reporte por miembro
        st.write("#### 👤 Multas por Miembro")
        
        cursor.execute("""
            SELECT 
                m.nombre AS Miembro,
                g.Nombre AS Grupo,
                COUNT(mu.Id_multa) AS Total_Multas,
                SUM(mu.Monto) AS Total_Monto,
                SUM(CASE WHEN mu.Estado_pago = 'Pendiente' THEN mu.Monto ELSE 0 END) AS Monto_Pendiente,
                SUM(CASE WHEN mu.Estado_pago = 'Pagada' THEN mu.Monto ELSE 0 END) AS Monto_Pagado
            FROM Miembros m
            JOIN Grupos g ON m.grupo_id = g.Id_grupo
            LEFT JOIN Multas mu ON mu.Id_miembro = m.id
            GROUP BY m.id
            HAVING Total_Multas > 0
            ORDER BY Total_Monto DESC
        """)
        
        reporte_miembros = cursor.fetchall()
        
        if reporte_miembros:
            df = pd.DataFrame(reporte_miembros)
            df = df.rename(columns={
                'Miembro': 'Miembro',
                'Grupo': 'Grupo',
                'Total_Multas': 'Nº Multas',
                'Total_Monto': 'Total ($)',
                'Monto_Pendiente': 'Pendiente ($)',
                'Monto_Pagado': 'Pagado ($)'
            })
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos de multas")
        
        st.divider()
        
        # Reporte por tipo
        st.write("#### 📋 Multas por Tipo")
        
        cursor.execute("""
            SELECT 
                Tipo_multa,
                COUNT(*) AS Cantidad,
                SUM(Monto) AS Total_Monto,
                AVG(Monto) AS Promedio_Monto
            FROM Multas
            GROUP BY Tipo_multa
            ORDER BY Total_Monto DESC
        """)
        
        reporte_tipos = cursor.fetchall()
        
        if reporte_tipos:
            df_tipos = pd.DataFrame(reporte_tipos)
            df_tipos = df_tipos.rename(columns={
                'Tipo_multa': 'Tipo',
                'Cantidad': 'Cantidad',
                'Total_Monto': 'Total ($)',
                'Promedio_Monto': 'Promedio ($)'
            })
            st.dataframe(df_tipos, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Reporte por grupo
        st.write("#### 👥 Multas por Grupo")
        
        cursor.execute("""
            SELECT 
                g.Nombre AS Grupo,
                COUNT(mu.Id_multa) AS Total_Multas,
                SUM(mu.Monto) AS Total_Monto,
                SUM(CASE WHEN mu.Estado_pago = 'Pendiente' THEN 1 ELSE 0 END) AS Multas_Pendientes
            FROM Grupos g
            LEFT JOIN Multas mu ON mu.Id_grupo = g.Id_grupo
            GROUP BY g.Id_grupo
            HAVING Total_Multas > 0
            ORDER BY Total_Monto DESC
        """)
        
        reporte_grupos = cursor.fetchall()
        
        if reporte_grupos:
            df_grupos = pd.DataFrame(reporte_grupos)
            df_grupos = df_grupos.rename(columns={
                'Grupo': 'Grupo',
                'Total_Multas': 'Nº Multas',
                'Total_Monto': 'Total ($)',
                'Multas_Pendientes': 'Pendientes'
            })
            st.dataframe(df_grupos, use_container_width=True, hide_index=True)
    
    finally:
        conexion.close()


def configurar_multas(id_distrito=None, id_grupo=None):
    """
    Configuración de montos estándar de multas.
    """
    st.subheader("⚙️ Configuración de Multas")
    
    st.info("💡 Define los montos estándar para cada tipo de multa. Estos montos se aplicarán automáticamente al registrar asistencia.")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM Configuracion_Multas ORDER BY Tipo_multa")
        configs = cursor.fetchall()
        
        if not configs:
            st.warning("⚠️ No hay configuraciones de multas")
            return
        
        with st.form("form_config_multas"):
            st.write("### 💰 Montos Estándar por Tipo de Multa")
            
            nuevos_montos = {}
            
            for config in configs:
                col1, col2, col3 = st.columns([2, 2, 4])
                
                with col1:
                    tipo_emoji = {
                        'Inasistencia': '❌',
                        'Tardanza': '⏰',
                        'Falta_Pago': '💸',
                        'Incumplimiento': '⚠️',
                        'Otro': '📝'
                    }
                    st.write(f"**{tipo_emoji.get(config['Tipo_multa'], '💰')} {config['Tipo_multa']}**")
                
                with col2:
                    nuevo_monto = st.number_input(
                        "Monto ($)",
                        min_value=0.0,
                        value=float(config['Monto_default']),
                        step=0.01,
                        format="%.2f",
                        key=f"monto_{config['Id_config']}",
                        label_visibility="collapsed"
                    )
                    nuevos_montos[config['Id_config']] = nuevo_monto
                
                with col3:
                    st.text_input(
                        "Descripción",
                        value=config['Descripcion'] or "",
                        disabled=True,
                        key=f"desc_{config['Id_config']}",
                        label_visibility="collapsed"
                    )
            
            st.divider()
            st.info("ℹ️ **Nota:** Las ausencias justificadas NO generan multas automáticamente.")
            
            submitted = st.form_submit_button("💾 Guardar Configuración", type="primary")
            
            if submitted:
                try:
                    for id_config, monto in nuevos_montos.items():
                        cursor.execute(
                            "UPDATE Configuracion_Multas SET Monto_default = %s WHERE Id_config = %s",
                            (monto, id_config)
                        )
                    
                    conexion.commit()
                    st.success("✅ Configuración actualizada correctamente")
                    st.rerun()
                except Exception as e:
                    conexion.rollback()
                    st.error(f"❌ Error: {str(e)}")
    
    finally:
        conexion.close()
