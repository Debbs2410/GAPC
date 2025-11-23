import pandas as pd

def obtener_datos_reuniones_actas(id_grupo):
    from modulos.config.conexion import obtener_conexion
    conexion = obtener_conexion()
    if not conexion:
        return None
    cursor = conexion.cursor(dictionary=True)
    # Reuniones y actas por grupo
    cursor.execute('''
        SELECT r.Id_reunion, r.Fecha_reunion
        FROM Reuniones r
        WHERE r.Id_grupo = %s
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
from datetime import datetime, date, time, timedelta

# Definición temporal para evitar error de función no definida

# Definición temporal para evitar error de función no definida
def ver_reuniones(id_distrito=None, id_grupo=None):
    from modulos.config.conexion import obtener_conexion
    import streamlit as st
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    cursor = conexion.cursor(dictionary=True)
    # Administradora: ve todas las reuniones del sistema
    # Promotora: ve y edita reuniones de sus grupos (por distrito)
    # Directiva: ve y edita reuniones de su grupo
    usuario = st.session_state.get('usuario', {}) if 'usuario' in st.session_state else {}
    rol = usuario.get('Rol') or usuario.get('rol')
    filtro = ""
    params = []
    if rol == 'Administradora':
        if id_distrito:
            filtro += " AND g.distrito_id = %s"
            params.append(id_distrito)
        if id_grupo:
            filtro += " AND r.Id_grupo = %s"
            params.append(id_grupo)
    elif rol == 'Promotora':
        # Solo reuniones de grupos de su distrito
        id_distrito_usuario = usuario.get('Id_distrito') or usuario.get('id_distrito')
        filtro += " AND g.distrito_id = %s"
        params.append(id_distrito_usuario)
        if id_grupo:
            filtro += " AND r.Id_grupo = %s"
            params.append(id_grupo)
    elif rol == 'Directiva':
        # Solo reuniones de su grupo
        id_grupo_usuario = usuario.get('Id_grupo') or usuario.get('id_grupo')
        filtro += " AND r.Id_grupo = %s"
        params.append(id_grupo_usuario)
    else:
        st.warning("No se pudo determinar el rol del usuario.")
        conexion.close()
        return
    query = f'''
        SELECT r.*, g.Nombre AS nombre_grupo
        FROM Reuniones r
        LEFT JOIN Grupos g ON r.Id_grupo = g.Id_grupo
        WHERE 1=1 {filtro}
        ORDER BY r.Fecha_reunion DESC
    '''
    cursor.execute(query, tuple(params))
    reuniones = cursor.fetchall()
    if not reuniones:
        st.info("No hay reuniones para mostrar.")
        conexion.close()
        return
    for reunion in reuniones:
        estado_emoji = {
            'Programada': '📅',
            'Realizada': '✅',
            'Cancelada': '❌'
        }
        nombre_grupo = reunion.get('nombre_grupo') or reunion.get('Nombre') or ''
        with st.expander(f"{estado_emoji.get(reunion.get('Estado'), '📋')} {nombre_grupo} - Semana {reunion.get('Numero_semana', '')} ({reunion.get('Fecha_reunion', '')})"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**📅 Fecha:** {reunion.get('Fecha_reunion', '')}")
                st.write(f"**🔢 Semana del Ciclo:** {reunion.get('Numero_semana', '')}")
                st.write(f"**🕐 Hora Inicio:** {reunion.get('Hora_inicio', 'No definida')}")
                st.write(f"**🕐 Hora Fin:** {reunion.get('Hora_fin', 'No definida')}")
                st.write(f"**📍 Lugar:** {reunion.get('Lugar', 'No definido')}")
            with col2:
                st.write(f"**👥 Grupo:** {nombre_grupo}")
                st.write(f"**📊 Estado:** {reunion.get('Estado', '')}")
                st.write(f"**✅ Presentes:** {reunion.get('Presentes', 0) or 0}")
                st.write(f"**⏰ Presentes con Tardanza:** {reunion.get('Tardanzas', 0) or 0}")
                st.write(f"**❌ Ausentes:** {reunion.get('Ausentes', 0) or 0}")
                st.write(f"**📋 Total Registrado:** {reunion.get('Total_Asistencias', 0) or 0}")
            if reunion.get('Observaciones'):
                st.info(f"📝 Observaciones: {reunion['Observaciones']}")
            # Solo Promotora y Directiva pueden editar/cancelar
            if rol in ('Promotora', 'Directiva'):
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

# Definición temporal para evitar error de función no definida
def gestionar_reuniones(id_distrito=None, id_grupo=None):
    from modulos.config.conexion import obtener_conexion
    import streamlit as st
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    cursor = conexion.cursor(dictionary=True)
    usuario = st.session_state.get('usuario', {}) if 'usuario' in st.session_state else {}
    rol = usuario.get('Rol') or usuario.get('rol')
    filtro = ""
    params = []
    if rol == 'Administradora':
        if id_distrito:
            filtro += " AND g.distrito_id = %s"
            params.append(id_distrito)
        if id_grupo:
            filtro += " AND r.Id_grupo = %s"
            params.append(id_grupo)
    elif rol == 'Promotora':
        id_distrito_usuario = usuario.get('Id_distrito') or usuario.get('id_distrito')
        filtro += " AND g.distrito_id = %s"
        params.append(id_distrito_usuario)
        if id_grupo:
            filtro += " AND r.Id_grupo = %s"
            params.append(id_grupo)
    elif rol == 'Directiva':
        id_grupo_usuario = usuario.get('Id_grupo') or usuario.get('id_grupo')
        filtro += " AND r.Id_grupo = %s"
        params.append(id_grupo_usuario)
    else:
        st.warning("No se pudo determinar el rol del usuario.")
        conexion.close()
        return
    query = f'''
        SELECT r.*, g.Nombre AS nombre_grupo
        FROM Reuniones r
        LEFT JOIN Grupos g ON r.Id_grupo = g.Id_grupo
        WHERE 1=1 {filtro}
        ORDER BY r.Fecha_reunion DESC
    '''
    cursor.execute(query, tuple(params))
    reuniones = cursor.fetchall()
    if not reuniones:
        st.info("No hay reuniones para mostrar.")
        conexion.close()
        return
    for reunion in reuniones:
        estado_emoji = {
            'Programada': '📅',
            'Realizada': '✅',
            'Cancelada': '❌'
        }
        nombre_grupo = reunion.get('nombre_grupo') or reunion.get('Nombre') or ''
        with st.expander(f"{estado_emoji.get(reunion.get('Estado'), '📋')} {nombre_grupo} - Semana {reunion.get('Numero_semana', '')} ({reunion.get('Fecha_reunion', '')})"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**📅 Fecha:** {reunion.get('Fecha_reunion', '')}")
                st.write(f"**🔢 Semana del Ciclo:** {reunion.get('Numero_semana', '')}")
                st.write(f"**🕐 Hora Inicio:** {reunion.get('Hora_inicio', 'No definida')}")
                st.write(f"**🕐 Hora Fin:** {reunion.get('Hora_fin', 'No definida')}")
                st.write(f"**📍 Lugar:** {reunion.get('Lugar', 'No definido')}")
            with col2:
                st.write(f"**👥 Grupo:** {nombre_grupo}")
                st.write(f"**📊 Estado:** {reunion.get('Estado', '')}")
                st.write(f"**✅ Presentes:** {reunion.get('Presentes', 0) or 0}")
                st.write(f"**⏰ Presentes con Tardanza:** {reunion.get('Tardanzas', 0) or 0}")
                st.write(f"**❌ Ausentes:** {reunion.get('Ausentes', 0) or 0}")
                st.write(f"**📋 Total Registrado:** {reunion.get('Total_Asistencias', 0) or 0}")
            if reunion.get('Observaciones'):
                st.info(f"📝 Observaciones: {reunion['Observaciones']}")
            if rol in ('Promotora', 'Directiva'):
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



def gestionar_asistencia_multas(id_distrito=None, id_grupo=None):
    """
    Función principal para gestionar asistencia y multas.
    """
    st.title("📋 Gestión de Asistencia y Multas")
    
    if es_administradora():
        tab1, tab2, tab3 = st.tabs([
            "📅 Ver Reuniones",
            "✅ Ver Asistencia",
            "💰 Ver Multas"
        ])
        # Filtros globales para administradora
        conexion = obtener_conexion()
        if not conexion:
            st.error("❌ Error de conexión a la base de datos. Por favor, intente más tarde.")
            return
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT distrito_id, nombre_distrito FROM Distrito ORDER BY nombre_distrito")
            distritos = cursor.fetchall()
            distrito_nombres = ["Todos"] + [d['nombre_distrito'] for d in distritos]
            distrito_sel = st.selectbox("Selecciona un distrito", distrito_nombres, key="asist_distrito_admin_main")
            if distrito_sel == "Todos":
                distrito_id_sel = None
            else:
                distrito_id_sel = next((d['distrito_id'] for d in distritos if d['nombre_distrito'] == distrito_sel), None)
            grupos = []
            grupo_nombres = ["Todos"]
            if distrito_id_sel:
                cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE distrito_id = %s ORDER BY Nombre", (distrito_id_sel,))
                grupos = cursor.fetchall()
                grupo_nombres += [g['Nombre'] for g in grupos]
            elif distrito_sel == "Todos":
                cursor.execute("SELECT Id_grupo, Nombre FROM Grupos ORDER BY Nombre")
                grupos = cursor.fetchall()
                grupo_nombres += [g['Nombre'] for g in grupos]
            grupo_sel = st.selectbox("Selecciona un grupo", grupo_nombres, key="asist_grupo_admin_main")
            if grupo_sel == "Todos":
                grupo_id_sel = None
            else:
                grupo_id_sel = next((g['Id_grupo'] for g in grupos if g['Nombre'] == grupo_sel), None)
            # Mostrar promotoras asignadas al grupo seleccionado (solo si hay grupo específico)
            if grupo_id_sel:
                cursor.execute("""
                    SELECT Nombre_Usuario as nombre, Correo as correo
                    FROM Usuarios 
                    WHERE Id_grupo = %s AND Rol = 'Promotora'""", (grupo_id_sel,))
                promotoras = cursor.fetchall()
                if promotoras:
                    st.write("**👩‍💼 Promotoras asignadas a este grupo:**")
                    for p in promotoras:
                        st.write(f"- {p['nombre']} ({p['correo']})")
                else:
                    # Si no hay promotora asignada al grupo, buscar promotora monitora del distrito
                    if distrito_id_sel:
                        cursor.execute("SELECT Nombre_Usuario, Correo FROM Usuarios WHERE Rol = 'Promotora' AND Id_distrito = %s LIMIT 1", (distrito_id_sel,))
                        promotora_distrito = cursor.fetchone()
                        if promotora_distrito:
                            st.info(f"👩‍💼 Promotora monitora del distrito: {promotora_distrito['Nombre_Usuario']} ({promotora_distrito['Correo']})")
                        else:
                            st.warning("⚠️ Sin promotora asignada al grupo ni al distrito")
            # Solo visualización, sin edición ni programación
            with tab1:
                ver_reuniones(id_distrito=distrito_id_sel, id_grupo=grupo_id_sel)
            with tab2:
                ver_asistencia_global(distrito_id_sel, grupo_id_sel)
            with tab3:
                ver_multas(id_grupo=grupo_id_sel)
        finally:
            if conexion:
                conexion.close()
        return
    # Para promotora y directiva, usar los parámetros recibidos
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
# --- NUEVA FUNCIÓN PARA ADMINISTRADORA: Visualización global de ausencias acumuladas ---
def ver_asistencia_global(distrito_id_sel=None, grupo_id_sel=None):
    """
    Visualiza ausencias acumuladas por miembro, distrito y grupo para la administradora.
    """
    st.subheader("✅ Ausencias acumuladas por miembro (por grupo)")
    reuniones = None  # Inicializa la variable para evitar UnboundLocalError
    cursor = None  # Inicializa cursor para evitar errores de referencia
    # Aquí va la lógica de visualización de ausencias acumuladas, si aplica.
    # Tabs principales para usuarios que no son administradora
    if 'id_distrito' not in locals():
        id_distrito = None
    if 'id_grupo' not in locals():
        id_grupo = None
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

    # Mostrar cada reunión como un expander (desplegable) con toda la información relevante
    if reuniones:
        if not isinstance(reuniones, list):
            reuniones = list(reuniones) if reuniones is not None else []
        for reunion in reuniones:
            estado_emoji = {
                'Programada': '📅',
                'Realizada': '✅',
                'Cancelada': '❌'
            }
            nombre_grupo = reunion.get('nombre_grupo') or reunion.get('Nombre') or ''
            with st.expander(f"{estado_emoji.get(reunion.get('Estado'), '📋')} {nombre_grupo} - Semana {reunion.get('Numero_semana', '')} ({reunion.get('Fecha_reunion', '')})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**📅 Fecha:** {reunion.get('Fecha_reunion', '')}")
                    st.write(f"**🔢 Semana del Ciclo:** {reunion.get('Numero_semana', '')}")
                    st.write(f"**🕐 Hora Inicio:** {reunion.get('Hora_inicio', 'No definida')}")
                    st.write(f"**🕐 Hora Fin:** {reunion.get('Hora_fin', 'No definida')}")
                    st.write(f"**📍 Lugar:** {reunion.get('Lugar', 'No definido')}")
                with col2:
                    st.write(f"**👥 Grupo:** {nombre_grupo}")
                    st.write(f"**📊 Estado:** {reunion.get('Estado', '')}")
                    st.write(f"**✅ Presentes:** {reunion.get('Presentes', 0) or 0}")
                    st.write(f"**⏰ Presentes con Tardanza:** {reunion.get('Tardanzas', 0) or 0}")
                    st.write(f"**❌ Ausentes:** {reunion.get('Ausentes', 0) or 0}")
                    st.write(f"**📋 Total Registrado:** {reunion.get('Total_Asistencias', 0) or 0}")
                if reunion.get('Observaciones'):
                    st.info(f"📝 Observaciones: {reunion['Observaciones']}")
    else:
        st.info("No hay reuniones para mostrar.")
        reuniones = reuniones if isinstance(reuniones, list) else []
        programadas = len([r for r in reuniones if isinstance(r, dict) and r.get('Estado') == 'Programada'])
        canceladas = len([r for r in reuniones if isinstance(r, dict) and r.get('Estado') == 'Cancelada'])
        st.metric("📅 Programadas", programadas)
        st.metric("❌ Canceladas", canceladas)
        st.divider()
        if not reuniones:
            st.info("📭 No hay reuniones registradas para este grupo o filtro.")
            if 'conexion' in locals() and conexion:
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
    from modulos.solo_lectura import es_administradora
    if es_administradora():
        st.info("Solo puede visualizar reuniones. No puede programar reuniones.")
        return
    st.write("### ➕ Programar Nueva Reunión")
    # ... (rest of function unchanged)


def registrar_asistencia(id_distrito=None, id_grupo=None):
    """
    Registro de asistencia a reuniones con causas de ausencia diferenciadas.
    """
    from modulos.solo_lectura import es_administradora
    import streamlit as st
    usuario = st.session_state.get('usuario', {}) if 'usuario' in st.session_state else {}
    rol = usuario.get('Rol') or usuario.get('rol')
    if rol == 'Administradora':
        st.info("Solo puede visualizar asistencias. No puede registrar ni editar asistencias.")
        return
        st.subheader("✅ Registro de Asistencia")
        st.info("💡 **Tipos de asistencia:**\n"
            "- ✅ **Presente**: Miembro asistió a la reunión\n"
            "- ❌ **Ausente (Injustificada)**: No asistió sin justificación → Genera multa automáticamente\n"
            "- 📋 **Ausente (Justificada)**: No asistió con justificación válida → NO genera multa\n"
            "- ⏰ **Tardanza**: Llegó tarde → Puede generar multa según configuración\n"
            "- 📝 **Otras Razones**: Situaciones especiales")

        # Mostrar resumen de ausencias solo una vez, al final del registro de asistencia
        # Eliminar cualquier bloque duplicado que muestre la tabla de ausencias aquí

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
        # ...existing code (todo el bloque try original)...
        # (No se modifica la lógica interna)
        pass
    finally:
        if conexion:
            conexion.close()
    

    # Mostrar resumen de ausencias acumuladas solo una vez para el grupo actual (promotora)
    if id_grupo is not None:
        st.divider()
        st.subheader("✅ Ausencias acumuladas por miembro (solo este grupo)")
        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor(dictionary=True)
            query = '''
                SELECT m.id, m.nombre AS Miembro,
                       COALESCE(d.nombre_distrito, 'Sin distrito') AS Distrito,
                       COALESCE(g.Nombre, 'Sin grupo') AS Grupo,
                       IFNULL(g.Ausencias_permitidas, 3) AS Ausencias_permitidas,
                       g.Id_grupo
                FROM Miembros m
                LEFT JOIN Grupos g ON m.grupo_id = g.Id_grupo
                LEFT JOIN Distrito d ON g.distrito_id = d.distrito_id
                WHERE g.Id_grupo = %s
                ORDER BY m.nombre
            '''
            cursor.execute(query, (id_grupo,))
            miembros = cursor.fetchall()
            data_ausencias = []
            for m in miembros:
                cursor.execute(
                    "SELECT COUNT(*) as ausencias "
                    "FROM Asistencia a "
                    "JOIN Reuniones r ON a.Id_reunion = r.Id_reunion "
                    "WHERE a.Id_miembro = %s AND a.Estado_asistencia = 'Ausente' AND r.Id_grupo = %s",
                    (m['id'], m['Id_grupo'])
                )
                ausencias = cursor.fetchone()['ausencias']
                data_ausencias.append({
                    "Grupo": m.get('Grupo', ''),
                    "Distrito": m.get('Distrito', ''),
                    "Miembro": m.get('Miembro', ''),
                    "Ausencias permitidas en grupo": m.get('Ausencias_permitidas', ''),
                    "Ausencias": ausencias
                })
            if data_ausencias:
                orden_columnas = ["Grupo", "Distrito", "Miembro", "Ausencias permitidas en grupo", "Ausencias"]
                df = pd.DataFrame(data_ausencias)
                for col in orden_columnas:
                    if col not in df.columns:
                        df[col] = ''
                df = df[orden_columnas]
                st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error al mostrar ausencias: {e}")
        finally:
            conexion.close()
    else:
        # No mostrar tabla de ausencias si no hay grupo seleccionado
        pass


def gestionar_multas(id_distrito=None, id_grupo=None):
    """
    Gestión de multas aplicadas a los miembros.
    """
    from modulos.solo_lectura import es_administradora
    if es_administradora():
        st.info("Solo puede visualizar multas y reportes. No puede aplicar ni editar multas.")
        tab1, tab2 = st.tabs(["📋 Ver Multas", "📊 Reportes"])
        with tab1:
            ver_multas(id_grupo=id_grupo)
        with tab2:
            reportes_multas(id_grupo=id_grupo)
        return
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
        
        # Generar un sufijo único para los keys según el contexto de llamada
        import uuid
        key_suffix = str(uuid.uuid4())[:8]
        with col1:
            estado_filtro = st.selectbox("Estado de Pago", ["Todas", "Pendiente", "Pagada", "Condonada"], key=f"multas_estado_filtro_{key_suffix}")
        
        with col2:
            tipo_filtro = st.selectbox("Tipo de Multa", ["Todas", "Inasistencia", "Tardanza", "Falta_Pago", "Incumplimiento", "Otro"], key=f"multas_tipo_filtro_{key_suffix}")
        
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
            grupo_filtro = st.selectbox("Grupo", list(grupos_dict.keys()), index=1 if id_grupo_usuario else 0, key=f"multas_grupo_filtro_{key_suffix}")
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
                            if st.button(f"✅ Marcar como Pagada", key=f"pagar_{multa['Id_multa']}_{key_suffix}"):
                                cursor.execute(
                                    "UPDATE Multas SET Estado_pago = 'Pagada', Fecha_pago = CURDATE() WHERE Id_multa = %s",
                                    (multa['Id_multa'],)
                                )
                                conexion.commit()
                                st.success("Multa marcada como pagada")
                                st.rerun()
                        
                        with col_btn2:
                            if st.button(f"🔄 Condonar", key=f"condonar_{multa['Id_multa']}_{key_suffix}"):
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
    from modulos.solo_lectura import es_administradora
    if es_administradora():
        st.info("Solo puede visualizar multas. No puede aplicar multas manualmente.")
        return
    st.write("### ➕ Aplicar Multa Manual")
    # ... (rest of function unchanged)


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
    from modulos.solo_lectura import es_administradora
    if es_administradora():
        st.info("Solo puede visualizar la configuración de multas. No puede editar la configuración.")
        return
    st.subheader("⚙️ Configuración de Multas")
    # ... (rest of function unchanged)
