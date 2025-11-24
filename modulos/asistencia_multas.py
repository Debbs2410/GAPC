import pandas as pd

from modulos.solo_lectura import es_administradora

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
    # --- NUEVO: Mostrar tabla resumen de miembros y ausencias acumuladas ---
    if id_grupo:
        # Obtener info de grupo y distrito
        cursor.execute('''
            SELECT g.Nombre AS nombre_grupo, d.nombre_distrito, g.Ausencias_permitidas
            FROM Grupos g
            LEFT JOIN Distrito d ON g.distrito_id = d.distrito_id
            WHERE g.Id_grupo = %s
        ''', (id_grupo,))
        grupo_info = cursor.fetchone()
        # Obtener miembros del grupo
        cursor.execute('''
            SELECT m.id, m.nombre
            FROM Miembros m
            WHERE m.grupo_id = %s
            ORDER BY m.nombre
        ''', (id_grupo,))
        miembros = cursor.fetchall()
        # Calcular ausencias acumuladas (sin justificadas) por miembro
        data = []
        for miembro in miembros:
            cursor.execute('''
                SELECT COUNT(*) AS ausencias
                FROM Asistencia a
                WHERE a.Id_miembro = %s AND a.Estado_asistencia = 'Ausente' AND (a.Observaciones IS NULL OR a.Observaciones = '')
            ''', (miembro['id'],))
            ausencias = cursor.fetchone()['ausencias']
            data.append({
                'Miembro': miembro['nombre'],
                'Grupo': grupo_info['nombre_grupo'] if grupo_info else '',
                'Distrito': grupo_info['nombre_distrito'] if grupo_info else '',
                'Ausencias permitidas': grupo_info['Ausencias_permitidas'] if grupo_info else '',
                'Ausencias acumuladas': ausencias
            })
        if data:
            import pandas as pd
            st.subheader('Resumen de miembros y ausencias')
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
        else:
            st.info('No hay miembros registrados en este grupo.')

    for reunion in reuniones:
        estado_emoji = {
            'Programada': '📅',
            'Realizada': '✅',
            'Cancelada': '❌'
        }
        nombre_grupo = reunion.get('nombre_grupo') or reunion.get('Nombre') or ''
        # Obtener datos reales de asistencia para la reunión
        conexion2 = obtener_conexion()
        if not conexion2:
            st.error("❌ Error de conexión a la base de datos para obtener totales de asistencia de la reunión.")
            totales = {}
        else:
            cursor2 = conexion2.cursor(dictionary=True)
            cursor2.execute('''
                SELECT 
                    SUM(CASE WHEN Estado_asistencia = 'Presente' THEN 1 ELSE 0 END) AS Presentes,
                    SUM(CASE WHEN Estado_asistencia = 'Tardanza' THEN 1 ELSE 0 END) AS Tardanzas,
                    SUM(CASE WHEN Estado_asistencia = 'Ausente' AND Observaciones IS NULL THEN 1 ELSE 0 END) AS Ausentes_Injustificados,
                    SUM(CASE WHEN Estado_asistencia = 'Ausente' AND Observaciones IS NOT NULL THEN 1 ELSE 0 END) AS Ausentes_Justificados,
                    COUNT(*) AS Total_Asistencias
                FROM Asistencia
                WHERE Id_reunion = %s
            ''', (reunion['Id_reunion'],))
            totales = cursor2.fetchone() or {}
            conexion2.close()
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
                st.write(f"**✅ Presentes:** {totales.get('Presentes', 0) or 0}")
                st.write(f"**⏰ Presentes con Tardanza:** {totales.get('Tardanzas', 0) or 0}")
                st.write(f"**❌ Ausentes injustificados:** {totales.get('Ausentes_Injustificados', 0) or 0}")
                st.write(f"**📋 Ausentes justificados:** {totales.get('Ausentes_Justificados', 0) or 0}")
                st.write(f"**🧾 Total Registrado:** {totales.get('Total_Asistencias', 0) or 0}")
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
    # Ya no se muestra ningún botón de crear reunión aquí; solo en la subpestaña correspondiente
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
            # Mostrar resumen de asistencias solo para reuniones realizadas
            if reunion.get('Estado') == 'Realizada':
                # Consultar totales de asistencia para la reunión
                conexion2 = obtener_conexion()
                cursor2 = conexion2.cursor(dictionary=True)
                cursor2.execute('''
                    SELECT 
                        SUM(CASE WHEN Estado_asistencia = 'Presente' THEN 1 ELSE 0 END) AS Presentes,
                        SUM(CASE WHEN Estado_asistencia = 'Tardanza' THEN 1 ELSE 0 END) AS Tardanzas,
                        SUM(CASE WHEN Estado_asistencia = 'Ausente' AND Observaciones IS NULL THEN 1 ELSE 0 END) AS Ausentes_Injustificados,
                        SUM(CASE WHEN Estado_asistencia = 'Ausente' AND Observaciones IS NOT NULL THEN 1 ELSE 0 END) AS Ausentes_Justificados
                    FROM Asistencia
                    WHERE Id_reunion = %s
                ''', (reunion['Id_reunion'],))
                totales = cursor2.fetchone()
                conexion2.close()
                st.write(f"**✅ Presentes:** {totales['Presentes'] or 0}")
                st.write(f"**⏰ Presentes con Tardanza:** {totales['Tardanzas'] or 0}")
                st.write(f"**❌ Ausentes injustificados:** {totales['Ausentes_Injustificados'] or 0}")
                st.write(f"**📋 Ausentes justificados:** {totales['Ausentes_Justificados'] or 0}")
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
            registrar_asistencia(id_distrito=distrito_id_sel, id_grupo=grupo_id_sel)
        with tab3:
            gestionar_multas(id_distrito=distrito_id_sel, id_grupo=grupo_id_sel)
    else:
        # Para Directiva y Promotora: mostrar tabs de su grupo
        usuario = st.session_state.get('usuario', {}) if 'usuario' in st.session_state else {}
        id_grupo_usuario = usuario.get('Id_grupo') or usuario.get('id_grupo') or id_grupo
        id_distrito_usuario = usuario.get('Id_distrito') or usuario.get('id_distrito') or id_distrito
        tab1, tab2, tab3 = st.tabs([
            "Reuniones",
            "✅ Ver Asistencia",
            "💰 Ver Multas"
        ])
        with tab1:
            # --- NUEVO: Tabla editable de asistencias permitidas por grupo bajo supervisión de promotora ---
            if usuario.get('Rol', '').lower() == 'promotora' or usuario.get('rol', '').lower() == 'promotora':
                st.subheader("Editar número de ausencias permitidas por grupo")
                conexion = obtener_conexion()
                cursor = conexion.cursor(dictionary=True)
                # Obtener grupos bajo supervisión de la promotora
                cursor.execute("SELECT Id_grupo, Nombre, Ausencias_permitidas FROM Grupos WHERE distrito_id = %s", (id_distrito_usuario,))
                grupos_promotora = cursor.fetchall()
                if grupos_promotora:
                    df_edit = pd.DataFrame(grupos_promotora)
                    edited = st.data_editor(df_edit, num_rows="dynamic", use_container_width=True, key="ausencias_permitidas_editor")
                    if st.button("Guardar cambios de ausencias permitidas"):
                        for idx, row in edited.iterrows():
                            cursor.execute("UPDATE Grupos SET Ausencias_permitidas = %s WHERE Id_grupo = %s", (row['Ausencias_permitidas'], row['Id_grupo']))
                        conexion.commit()
                        st.success("Cambios guardados correctamente.")
                        st.rerun()
                else:
                    st.info("No hay grupos bajo su supervisión.")
                # --- Tabla resumen de miembros, grupo, distrito, ausencias permitidas y ausencias no justificadas ---
                st.subheader("Resumen de ausencias por grupo")
                cursor.execute('''
                    SELECT m.nombre AS Miembro, g.Nombre AS Grupo, d.nombre_distrito AS Distrito, g.Ausencias_permitidas, m.id AS id_miembro, g.Id_grupo
                    FROM Miembros m
                    JOIN Grupos g ON m.grupo_id = g.Id_grupo
                    JOIN Distrito d ON g.distrito_id = d.distrito_id
                    WHERE g.distrito_id = %s
                    ORDER BY g.Nombre, m.nombre
                ''', (id_distrito_usuario,))
                miembros = cursor.fetchall()
                data = []
                for miembro in miembros:
                    # Calcular ausencias no justificadas
                    cursor.execute('''
                        SELECT COUNT(*) AS ausencias
                        FROM Asistencia a
                        WHERE a.Id_miembro = %s AND a.Estado_asistencia = 'Ausente' AND (a.Observaciones IS NULL OR a.Observaciones = '')
                    ''', (miembro['id_miembro'],))
                    ausencias = cursor.fetchone()['ausencias']
                    data.append({
                        'Miembro': miembro['Miembro'],
                        'Grupo': miembro['Grupo'],
                        'Distrito': miembro['Distrito'],
                        'Ausencias permitidas': miembro['Ausencias_permitidas'],
                        'Ausencias (no justificadas)': ausencias
                    })
                if data:
                    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
                else:
                    st.info('No hay miembros registrados en los grupos bajo su supervisión.')
                conexion.close()
            subtab1, subtab2 = st.tabs(["Ver reuniones", "Crear reunión"])
            with subtab1:
                ver_reuniones(id_distrito=id_distrito_usuario, id_grupo=id_grupo_usuario)
            with subtab2:
                programar_reunion(id_distrito=id_distrito_usuario, id_grupo=id_grupo_usuario)
        with tab2:
            registrar_asistencia(id_distrito=id_distrito_usuario, id_grupo=id_grupo_usuario)
        with tab3:
            gestionar_multas(id_distrito=id_distrito_usuario, id_grupo=id_grupo_usuario)
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
    # Eliminado tab4/configurar_multas no definido

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
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    cursor = conexion.cursor(dictionary=True)
    grupo = None
    ciclo = None
    # Si no se ha especificado el grupo, permitir a la promotora seleccionarlo
    if not id_grupo and id_distrito:
        cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE distrito_id = %s ORDER BY Nombre", (id_distrito,))
        grupos = cursor.fetchall()
        if grupos:
            opciones = {g['Nombre']: g['Id_grupo'] for g in grupos}
            grupo_sel = st.selectbox("Selecciona el grupo para la reunión", list(opciones.keys()), key="crear_reunion_grupo_select")
            id_grupo = opciones[grupo_sel]
    if id_grupo:
        cursor.execute("SELECT g.Id_grupo, g.Nombre, g.Id_Ciclo, c.Fecha_Inicio, c.Fecha_Fin FROM Grupos g LEFT JOIN Ciclo c ON g.Id_Ciclo = c.Id_Ciclo WHERE g.Id_grupo = %s", (id_grupo,))
        grupo = cursor.fetchone()
    if grupo:
        st.write(f"**Grupo:** {grupo['Nombre']}")
        st.write(f"**Ciclo:** {grupo['Id_Ciclo']} (Inicio: {grupo['Fecha_Inicio']}, Fin: {grupo['Fecha_Fin']})")
    else:
        st.error("No se pudo determinar el grupo o ciclo.")
        cursor.close()
        conexion.close()
        return
    with st.form(key="form_crear_reunion"):
        fecha = st.date_input("Fecha de la reunión")
        hora_inicio = st.time_input("Hora de inicio")
        hora_fin = st.time_input("Hora de fin")
        lugar = st.text_input("Lugar")
        observaciones = st.text_area("Observaciones", "")
        # Calcular número de semana automáticamente
        cursor.execute("SELECT COUNT(*) as num FROM Reuniones WHERE Id_grupo = %s", (id_grupo,))
        num_semana = (cursor.fetchone()['num'] or 0) + 1
        st.write(f"**Número de semana de reunión:** {num_semana}")
        submit = st.form_submit_button("Crear reunión")
        if submit:
            cursor.execute("""
                INSERT INTO Reuniones (Id_grupo, Fecha_reunion, Numero_semana, Hora_inicio, Hora_fin, Lugar, Observaciones, Estado, Id_Ciclo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Programada', %s)
            """, (id_grupo, fecha, num_semana, hora_inicio, hora_fin, lugar, observaciones, grupo['Id_Ciclo']))
            conexion.commit()
            id_reunion = cursor.lastrowid
            st.success(f"Reunión creada exitosamente. ID de la reunión: {id_reunion}")
            cursor.close()
            conexion.close()
            st.rerun()
    cursor.close()
    conexion.close()


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
        # Mostrar todas las reuniones realizadas y su asistencia en modo solo lectura
        conexion = obtener_conexion()
        if not conexion:
            st.error("❌ Error de conexión a la base de datos.")
            return
        cursor = conexion.cursor(dictionary=True)
        query = (
            """
            SELECT r.Id_reunion, r.Fecha_reunion, r.Numero_semana, r.Estado, g.Nombre AS Grupo
            FROM Reuniones r
            LEFT JOIN Grupos g ON r.Id_grupo = g.Id_grupo
            ORDER BY r.Fecha_reunion DESC
            """
        )
        cursor.execute(query)
        reuniones = cursor.fetchall()
        for reunion in reuniones:
            st.markdown(f"### {reunion['Grupo']} - Semana {reunion['Numero_semana']} ({reunion['Fecha_reunion']}) [{reunion['Estado']}]" )
            # Mostrar tabla de asistencia para cada reunión
            cursor.execute(
                """
                SELECT m.nombre AS Miembro, a.Estado_asistencia, a.Hora_llegada, a.Observaciones
                FROM Asistencia a
                JOIN Miembros m ON a.Id_miembro = m.id
                WHERE a.Id_reunion = %s
                ORDER BY m.nombre
                """,
                (reunion['Id_reunion'],)
            )
            registros = cursor.fetchall()
            if registros:
                import pandas as pd
                df = pd.DataFrame(registros)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No hay asistencias registradas para esta reunión.")
        conexion.close()
        return

    # Selección de grupo para promotora/directiva
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
    # Mostrar reuniones del grupo
    cursor.execute("SELECT * FROM Reuniones WHERE Id_grupo = %s ORDER BY Fecha_reunion DESC", (id_grupo,))
    reuniones = cursor.fetchall()
    if not reuniones:
        st.info("No hay reuniones programadas para este grupo.")
        conexion.close()
        return
    # --- NUEVO: Selección de reunión para tomar asistencia ---
    # Filtrar reuniones programadas que NO tienen asistencia registrada
    reuniones_programadas = [r for r in reuniones if r['Estado'] == 'Programada']
    reuniones_con_asistencia = set()
    if reuniones_programadas:
        ids = ",".join(str(r['Id_reunion']) for r in reuniones_programadas)
        cursor.execute(f"SELECT DISTINCT Id_reunion FROM Asistencia WHERE Id_reunion IN ({ids})")
        for row in cursor.fetchall():
            reuniones_con_asistencia.add(row['Id_reunion'])
    reuniones_disponibles = [r for r in reuniones_programadas if r['Id_reunion'] not in reuniones_con_asistencia]
    id_usuario_aplica = None
    if 'usuario' in st.session_state:
        id_usuario_aplica = st.session_state['usuario'].get('Id_usuario') or st.session_state['usuario'].get('id_usuario')
    if rol in ('Promotora', 'Directiva'):
        if reuniones_disponibles:
            opciones = {f"Semana {r['Numero_semana']} - {r['Fecha_reunion']}": r for r in reuniones_disponibles}
            seleccion = st.selectbox("Selecciona la reunión para tomar asistencia", list(opciones.keys()), key="asistencia_reunion_select")
            reunion = opciones[seleccion]
            # ...formulario de asistencia igual que antes...
            cursor.execute("SELECT m.id, m.nombre FROM Miembros m WHERE m.grupo_id = %s ORDER BY m.nombre", (id_grupo,))
            miembros = cursor.fetchall()
            if not miembros:
                st.info("No hay miembros registrados en este grupo.")
            else:
                cursor.execute("SELECT Id_Ciclo FROM Grupos WHERE Id_grupo = %s", (id_grupo,))
                grupo_row = cursor.fetchone()
                id_ciclo = grupo_row['Id_Ciclo'] if grupo_row else None
                with st.form(key=f"form_asistencia_{reunion['Id_reunion']}"):
                    for miembro in miembros:
                        col1, col2, col3 = st.columns([2,2,3])
                        with col1:
                            estado = st.selectbox(
                                f"Estado de {miembro['nombre']}",
                                ["Presente", "Tardanza", "Ausente (Injustificada)", "Ausente (Justificada)"],
                                key=f"estado_{reunion['Id_reunion']}_{miembro['id']}"
                            )
                        with col2:
                            hora_llegada = st.time_input(
                                f"Hora llegada {miembro['nombre']}",
                                key=f"hora_{reunion['Id_reunion']}_{miembro['id']}"
                            )
                        with col3:
                            observ = st.text_input(
                                f"Observaciones {miembro['nombre']}",
                                key=f"obs_{reunion['Id_reunion']}_{miembro['id']}"
                            )
                    submitted = st.form_submit_button("Guardar asistencia")
                    if submitted:
                        for miembro in miembros:
                            estado = st.session_state.get(f"estado_{reunion['Id_reunion']}_{miembro['id']}")
                            hora_llegada = st.session_state.get(f"hora_{reunion['Id_reunion']}_{miembro['id']}")
                            observ = st.session_state.get(f"obs_{reunion['Id_reunion']}_{miembro['id']}")
                            if estado == "Ausente (Injustificada)":
                                estado_db = "Ausente"
                                observ_db = None
                            elif estado == "Ausente (Justificada)":
                                estado_db = "Ausente"
                                observ_db = observ
                            else:
                                estado_db = estado
                                observ_db = observ
                            cursor.execute("""
                                INSERT INTO Asistencia (Id_reunion, Id_miembro, Estado_asistencia, Hora_llegada, Observaciones)
                                VALUES (%s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE Estado_asistencia=VALUES(Estado_asistencia), Hora_llegada=VALUES(Hora_llegada), Observaciones=VALUES(Observaciones)
                            """, (reunion['Id_reunion'], miembro['id'], estado_db, hora_llegada, observ_db))
                            if estado == "Ausente (Injustificada)":
                                cursor.execute("""
                                    INSERT INTO Multas (Id_miembro, Id_grupo, Id_Ciclo, Id_reunion, Fecha_multa, Tipo_multa, Monto, Estado_pago, Descripcion, Aplicado_por)
                                    VALUES (%s, %s, %s, %s, CURDATE(), 'Inasistencia', 5.00, 'Pendiente', 'Multa por inasistencia injustificada', %s)
                                    ON DUPLICATE KEY UPDATE Estado_pago='Pendiente', Aplicado_por=VALUES(Aplicado_por)
                                """, (miembro['id'], id_grupo, id_ciclo, reunion['Id_reunion'], id_usuario_aplica))
                            elif estado == "Tardanza":
                                cursor.execute("""
                                    INSERT INTO Multas (Id_miembro, Id_grupo, Id_Ciclo, Id_reunion, Fecha_multa, Tipo_multa, Monto, Estado_pago, Descripcion, Aplicado_por)
                                    VALUES (%s, %s, %s, %s, CURDATE(), 'Tardanza', 2.00, 'Pendiente', 'Multa por tardanza', %s)
                                    ON DUPLICATE KEY UPDATE Estado_pago='Pendiente', Aplicado_por=VALUES(Aplicado_por)
                                """, (miembro['id'], id_grupo, id_ciclo, reunion['Id_reunion'], id_usuario_aplica))
                        conexion.commit()
                        st.success("Asistencia guardada y multas aplicadas.")
                        st.rerun()
        else:
            st.info("No hay reuniones programadas disponibles para tomar asistencia o ya se registró asistencia para todas.")

    # --- NUEVO: Selección de reunión para ver tabla de asistencia ---
    st.divider()
    st.subheader("Ver asistencia registrada por reunión")
    opciones_tabla = {f"Semana {r['Numero_semana']} - {r['Fecha_reunion']} [{r['Estado']}]": r for r in reuniones}
    seleccion_tabla = st.selectbox("Selecciona la reunión para ver la asistencia", list(opciones_tabla.keys()), key="tabla_asistencia_reunion_select")
    reunion_tabla = opciones_tabla[seleccion_tabla]
    # Obtener asistencias y multas actuales para la reunión
    cursor.execute(
        """
        SELECT m.nombre AS Miembro, a.Estado_asistencia, a.Hora_llegada, a.Observaciones, m.id as id_miembro
        FROM Asistencia a
        JOIN Miembros m ON a.Id_miembro = m.id
        WHERE a.Id_reunion = %s
        ORDER BY m.nombre
        """,
        (reunion_tabla['Id_reunion'],)
    )
    registros = cursor.fetchall()
    if registros:
        # Para cada registro, buscar la multa asociada según el tipo de asistencia
        for reg in registros:
            tipo_multa = None
            if reg['Estado_asistencia'] == 'Tardanza':
                tipo_multa = 'Tardanza'
            elif reg['Estado_asistencia'] == 'Ausente' and (reg['Observaciones'] is None or reg['Observaciones'] == ''):
                tipo_multa = 'Inasistencia'
            # Solo buscar multa si corresponde
            if tipo_multa:
                cursor.execute(
                    """
                    SELECT Tipo_multa, Monto, Estado_pago FROM Multas 
                    WHERE Id_miembro = %s AND Id_grupo = %s AND Id_reunion = %s AND Tipo_multa = %s
                    """,
                    (reg['id_miembro'], id_grupo, reunion_tabla['Id_reunion'], tipo_multa)
                )
                multa = cursor.fetchone()
                if multa:
                    reg['Multa'] = f"{multa['Tipo_multa']} - ${multa['Monto']} ({multa['Estado_pago']})"
                else:
                    reg['Multa'] = 'Sin multa'
            else:
                reg['Multa'] = 'Sin multa'
        import pandas as pd
        df = pd.DataFrame([{k: v for k, v in r.items() if k != 'id_miembro'} for r in registros])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay asistencias registradas para esta reunión.")
    conexion.close()


def gestionar_multas(id_distrito=None, id_grupo=None):
    """
    Gestión de multas aplicadas a los miembros.
    """
    tab1, tab2, tab3 = st.tabs(["📋 Ver Multas", "💵 Pago de multas", "📊 Reportes"])
    with tab1:
        ver_multas(id_grupo=id_grupo)
    with tab2:
        st.write("### 💵 Pago de multas")
        from modulos.solo_lectura import es_administradora
        if es_administradora():
            st.info("La administradora solo puede visualizar las multas. No puede marcar como pagadas.")
            conexion = obtener_conexion()
            if not conexion:
                st.error("❌ Error de conexión a la base de datos.")
            else:
                cursor = conexion.cursor(dictionary=True)
                query = (
                    """
                    SELECT mu.Id_multa, mu.Fecha_multa, mu.Tipo_multa, mu.Monto, mu.Estado_pago, mu.Descripcion, m.nombre AS Nombre_Miembro
                    FROM Multas mu
                    JOIN Miembros m ON mu.Id_miembro = m.id
                    WHERE mu.Estado_pago = 'Pendiente' {filtro_grupo}
                    ORDER BY mu.Fecha_multa DESC
                    """
                )
                filtro_grupo = ''
                params = []
                if id_grupo:
                    filtro_grupo = 'AND mu.Id_grupo = %s'
                    params.append(id_grupo)
                query = query.format(filtro_grupo=filtro_grupo)
                cursor.execute(query, params)
                multas = cursor.fetchall()
                if not multas:
                    st.info("No hay multas pendientes para pagar.")
                else:
                    import pandas as pd
                    df = pd.DataFrame(multas)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                conexion.close()
        else:
            conexion = obtener_conexion()
            if not conexion:
                st.error("❌ Error de conexión a la base de datos.")
            else:
                cursor = conexion.cursor(dictionary=True)
                # Mostrar solo multas pendientes del grupo
                query = (
                    """
                    SELECT mu.Id_multa, mu.Fecha_multa, mu.Tipo_multa, mu.Monto, mu.Estado_pago, mu.Descripcion, m.nombre AS Nombre_Miembro
                    FROM Multas mu
                    JOIN Miembros m ON mu.Id_miembro = m.id
                    WHERE mu.Estado_pago = 'Pendiente' {filtro_grupo}
                    ORDER BY mu.Fecha_multa DESC
                    """
                )
                filtro_grupo = ''
                params = []
                if id_grupo:
                    filtro_grupo = 'AND mu.Id_grupo = %s'
                    params.append(id_grupo)
                query = query.format(filtro_grupo=filtro_grupo)
                cursor.execute(query, params)
                multas = cursor.fetchall()
                if not multas:
                    st.info("No hay multas pendientes para pagar.")
                else:
                    import pandas as pd
                    df = pd.DataFrame(multas)
                    for i, multa in enumerate(multas):
                        col1, col2, col3, col4 = st.columns([3,2,2,2])
                        col1.write(f"**{multa['Nombre_Miembro']}** - {multa['Tipo_multa']} - ${multa['Monto']:.2f}")
                        col2.write(f"Fecha: {multa['Fecha_multa']}")
                        col3.write(f"Descripción: {multa['Descripcion']}")
                        if col4.button("Marcar como pagada", key=f"pagar_multa_{multa['Id_multa']}"):
                            cursor.execute("UPDATE Multas SET Estado_pago = 'Pagada', Fecha_pago = CURDATE() WHERE Id_multa = %s", (multa['Id_multa'],))
                            conexion.commit()
                            st.success(f"Multa de {multa['Nombre_Miembro']} marcada como pagada.")
                            st.rerun()
                conexion.close()
    with tab3:
        reportes_multas(id_grupo=id_grupo)

# Restaurar función ver_multas
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
    # Filtros
    col1, col2, col3 = st.columns(3)
    import uuid
    key_suffix = str(uuid.uuid4())[:8]
    with col1:
        estado_filtro = st.selectbox("Estado de Pago", ["Todas", "Pendiente", "Pagada", "Condonada"], key=f"multas_estado_filtro_{key_suffix}")
    with col2:
        tipo_filtro = st.selectbox("Tipo de Multa", ["Todas", "Inasistencia", "Tardanza", "Falta_Pago", "Incumplimiento", "Otro"], key=f"multas_tipo_filtro_{key_suffix}")
    with col3:
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
        # Mostrar tabla detallada solo para administradora
        from modulos.solo_lectura import es_administradora
        if es_administradora():
            import pandas as pd
            df = pd.DataFrame(multas)
            # Seleccionar y renombrar columnas relevantes
            cols = {
                'Nombre_Miembro': 'Miembro',
                'Nombre_Grupo': 'Grupo',
                'Tipo_multa': 'Motivo',
                'Monto': 'Monto',
                'Estado_pago': 'Estado',
                'Fecha_multa': 'Fecha',
                'Descripcion': 'Descripción',
                'Aplicado_Por': 'Aplicado por'
            }
            mostrar = [c for c in cols.keys() if c in df.columns]
            df = df[mostrar].rename(columns=cols)
            st.dataframe(df, use_container_width=True, hide_index=True)
    conexion.close()
    



def aplicar_multa_manual(id_grupo=None):
    """
    Formulario para aplicar multas manualmente.
    """
    from modulos.solo_lectura import es_administradora
    if es_administradora():
        st.info("Solo puede visualizar multas. No puede aplicar multas manualmente.")
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
GROUP BY m.id, g.Nombre
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
            SUM(CASE WHEN mu.Estado_pago = 'Pendiente' THEN mu.Monto ELSE 0 END) AS Monto_Pendiente,
            SUM(CASE WHEN mu.Estado_pago = 'Pagada' THEN mu.Monto ELSE 0 END) AS Monto_Pagado
        FROM Grupos g
        LEFT JOIN Miembros m ON m.grupo_id = g.Id_grupo
        LEFT JOIN Multas mu ON mu.Id_miembro = m.id
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
            'Monto_Pendiente': 'Pendiente ($)',
            'Monto_Pagado': 'Pagado ($)'
        })
        st.dataframe(df_grupos, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de multas por grupo")
    conexion.close()
