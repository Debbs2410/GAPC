import streamlit as st
from modulos.solo_lectura import es_administradora
from modulos.config.conexion import obtener_conexion
import pandas as pd
from datetime import datetime, date
from decimal import Decimal


def gestionar_ahorros(id_distrito=None, id_grupo=None):
    """
    Función principal para gestionar ahorros de los miembros.
    Si se proporciona id_distrito, solo muestra los grupos y ciclos de ese distrito.
    """
    st.title("💰 Gestión de Ahorros")
    st.info("💡 Los miembros pueden realizar ahorros en cada reunión. "
            "Al finalizar el ciclo, se les devolverá el total ahorrado.")
    # Solo lectura para administradora
    solo_lectura = es_administradora()
    # Filtro global de ciclo
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    cursor = conexion.cursor(dictionary=True)
    # Restaurar filtro original para administradora y restringir solo para directiva
    usuario = st.session_state.get('usuario', {}) if 'usuario' in st.session_state else {}
    rol = (usuario.get('Rol') or usuario.get('rol') or '').strip().lower()
    if rol == 'directiva' and id_grupo is not None:
        cursor.execute("""
            SELECT c.Id_Ciclo, c.Fecha_Inicio, c.Fecha_Fin,
                CASE 
                    WHEN CURDATE() < c.Fecha_Inicio THEN 'Pendiente'
                    WHEN CURDATE() BETWEEN c.Fecha_Inicio AND c.Fecha_Fin THEN 'Activo'
                    WHEN CURDATE() > c.Fecha_Fin THEN 'Completado'
                END as Estado
            FROM Ciclo c
            INNER JOIN Grupos g ON g.Id_Ciclo = c.Id_Ciclo
            WHERE g.Id_grupo = %s
            ORDER BY c.Fecha_Inicio DESC
        """, (id_grupo,))
        ciclos = cursor.fetchall()
    elif id_distrito is not None:
        cursor.execute("""
            SELECT DISTINCT c.Id_Ciclo, c.Fecha_Inicio, c.Fecha_Fin,
                CASE 
                    WHEN CURDATE() < c.Fecha_Inicio THEN 'Pendiente'
                    WHEN CURDATE() BETWEEN c.Fecha_Inicio AND c.Fecha_Fin THEN 'Activo'
                    WHEN CURDATE() > c.Fecha_Fin THEN 'Completado'
                END as Estado
            FROM Ciclo c
            INNER JOIN Grupos g ON g.Id_Ciclo = c.Id_Ciclo
            WHERE g.distrito_id = %s
            ORDER BY c.Fecha_Inicio DESC
        """, (id_distrito,))
        ciclos = cursor.fetchall()
    else:
        cursor.execute("""
            SELECT 
                c.Id_Ciclo,
                c.Fecha_Inicio,
                c.Fecha_Fin,
                CASE 
                    WHEN CURDATE() < c.Fecha_Inicio THEN 'Pendiente'
                    WHEN CURDATE() BETWEEN c.Fecha_Inicio AND c.Fecha_Fin THEN 'Activo'
                    WHEN CURDATE() > c.Fecha_Fin THEN 'Completado'
                END as Estado
            FROM Ciclo c
            ORDER BY c.Fecha_Inicio DESC
        """)
        ciclos = cursor.fetchall()
    if not ciclos:
        st.warning("No hay ciclos registrados.")
        return
    ciclos_dict = {f"Ciclo {c['Id_Ciclo']} ({c['Estado']}) {c['Fecha_Inicio']} - {c['Fecha_Fin']}": c['Id_Ciclo'] for c in ciclos}
    ciclo_sel = st.selectbox("🔄 Selecciona el ciclo a gestionar", list(ciclos_dict.keys()), key="ciclo_global_ahorros")
    id_ciclo_global = ciclos_dict[ciclo_sel]
    st.divider()
    # Tabs principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💵 Registrar Ahorro",
        "📋 Ver Ahorros", 
        "📊 Reportes",
        "💸 Devolución de Ahorros",
        "⚙️ Configuración"
    ])
    with tab1:
        if not solo_lectura:
            registrar_ahorro(id_ciclo_global, id_distrito=id_distrito, solo_lectura=solo_lectura)
        else:
            st.info("Solo lectura: la administradora no puede registrar ahorros.")
    with tab2:
        ver_ahorros(id_ciclo_global, id_distrito=id_distrito, id_grupo=id_grupo)
    with tab3:
        reportes_ahorros(id_ciclo_global, id_distrito=id_distrito)
    with tab4:
        if not solo_lectura:
            devolver_ahorros(id_ciclo_global, id_distrito=id_distrito, solo_lectura=solo_lectura)
        else:
            st.info("Solo lectura: la administradora no puede devolver ahorros.")
    with tab5:
        if not solo_lectura:
            configurar_monto_minimo(id_ciclo_global, id_distrito=id_distrito, solo_lectura=solo_lectura)
        else:
            st.info("Solo lectura: la administradora no puede modificar la configuración de ahorros.")


def registrar_ahorro(id_ciclo_filtro, id_distrito=None, solo_lectura=False):
    """
    Registrar ahorros de miembros en una reunión específica para el ciclo seleccionado.
    """
    st.subheader("💵 Registrar Ahorro en Reunión")
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    cursor = conexion.cursor(dictionary=True)
    try:
        # Obtener configuración de monto mínimo
        cursor.execute("SELECT * FROM Configuracion_Ahorros LIMIT 1")
        config_ahorro = cursor.fetchone()
        if not config_ahorro:
            st.warning("⚠️ No hay configuración de ahorros. Configúrala en la pestaña de Configuración.")
            monto_minimo = 0.0
            aplica_multa = False
            monto_multa = 0.0
        else:
            monto_minimo = float(config_ahorro['Monto_minimo'])
            aplica_multa = bool(config_ahorro['Aplica_multa'])
            monto_multa = float(config_ahorro['Monto_multa'])
        # Seleccionar reunión (filtrada por ciclo y distrito si corresponde)
        if id_distrito is not None:
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
                WHERE r.Estado IN ('Programada', 'Realizada')
                AND c.Id_Ciclo = %s
                AND g.distrito_id = %s
                ORDER BY r.Fecha_reunion DESC
                LIMIT 50
            """, (id_ciclo_filtro, id_distrito))
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
                WHERE r.Estado IN ('Programada', 'Realizada')
                AND c.Id_Ciclo = %s
                ORDER BY r.Fecha_reunion DESC
                LIMIT 50
            """, (id_ciclo_filtro,))
        reuniones = cursor.fetchall()
        if not reuniones:
            st.info("📭 No hay reuniones disponibles para registrar ahorros en este ciclo")
            return
        reuniones_dict = {
            f"{r['Nombre_Grupo']} - Semana {r['Numero_semana']} ({r['Fecha_reunion']})": r['Id_reunion']
            for r in reuniones
        }
        reunion_sel = st.selectbox("🔍 Seleccionar Reunión", list(reuniones_dict.keys()), key=f"reunion_{id_ciclo_filtro}", disabled=solo_lectura)
        id_reunion = reuniones_dict[reunion_sel]
        # Obtener datos de la reunión seleccionada
        reunion = next(r for r in reuniones if r['Id_reunion'] == id_reunion)
        st.divider()
        # Obtener miembros que asistieron (Presente o Tardanza), filtrando por distrito si corresponde
        if id_distrito is not None:
            cursor.execute("""
                SELECT 
                    m.id,
                    m.nombre,
                    a.Estado_asistencia
                FROM Miembros m
                INNER JOIN Asistencia a ON m.id = a.Id_miembro
                INNER JOIN Grupos g ON m.grupo_id = g.Id_grupo
                WHERE a.Id_reunion = %s 
                AND a.Estado_asistencia IN ('Presente', 'Tardanza')
                AND g.distrito_id = %s
                ORDER BY m.nombre
            """, (id_reunion, id_distrito))
        else:
            cursor.execute("""
                SELECT 
                    m.id,
                    m.nombre,
                    a.Estado_asistencia
                FROM Miembros m
                INNER JOIN Asistencia a ON m.id = a.Id_miembro
                WHERE a.Id_reunion = %s 
                AND a.Estado_asistencia IN ('Presente', 'Tardanza')
                ORDER BY m.nombre
            """, (id_reunion,))
        miembros_asistentes = cursor.fetchall()
        if not miembros_asistentes:
            st.warning("⚠️ No hay miembros que hayan asistido a esta reunión. Primero registra la asistencia.")
            return
        st.write(f"**👥 Grupo:** {reunion['Nombre_Grupo']}")
        st.write(f"**📅 Fecha:** {reunion['Fecha_reunion']}")
        st.write(f"**🔢 Semana:** {reunion['Numero_semana']}")
        st.write(f"**✅ Miembros asistentes:** {len(miembros_asistentes)}")
        st.divider()
        st.write("### 💵 Registrar Ahorros")
        # Obtener ahorros ya registrados para esta reunión
        cursor.execute("""
            SELECT Id_miembro, Monto, Observaciones
            FROM Ahorros
            WHERE Id_reunion = %s
        """, (id_reunion,))
        ahorros_existentes = {a['Id_miembro']: a for a in cursor.fetchall()}
        # Formulario de ahorros
        ahorros_nuevos = []
        for miembro in miembros_asistentes:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 3])
                ahorro_existente = ahorros_existentes.get(miembro['id'])
                with col1:
                    st.write(f"**{miembro['nombre']}**")
                    st.caption(f"Estado: {miembro['Estado_asistencia']}")
                with col2:
                    monto_default = float(ahorro_existente['Monto']) if ahorro_existente else monto_minimo
                    monto = st.number_input(
                        f"Monto ($) [Mín: ${monto_minimo:.2f}]",
                        min_value=0.0,
                        value=monto_default,
                        step=0.50,
                        format="%.2f",
                        key=f"monto_{miembro['id']}_{id_reunion}",
                        label_visibility="collapsed",
                        help=f"Monto mínimo requerido: ${monto_minimo:.2f}",
                        disabled=solo_lectura
                    )
                    if monto > 0 and monto < monto_minimo and aplica_multa:
                        st.warning(f"⚠️ Multa: ${monto_multa:.2f}", icon="⚠️")
                    elif monto == 0 and aplica_multa and monto_minimo > 0:
                        st.error(f"❌ Multa: ${monto_multa:.2f}", icon="❌")
                with col3:
                    obs_default = ahorro_existente['Observaciones'] if ahorro_existente else ""
                    observaciones = st.text_input(
                        "Observaciones",
                        value=obs_default,
                        key=f"obs_{miembro['id']}_{id_reunion}",
                        label_visibility="collapsed",
                        placeholder="Observaciones (opcional)...",
                        disabled=solo_lectura
                    )
                ahorros_nuevos.append({
                    'id_miembro': miembro['id'],
                    'nombre': miembro['nombre'],
                    'monto': monto,
                    'observaciones': observaciones,
                    'cumple_minimo': monto >= monto_minimo
                })
        st.divider()
        # Mostrar resumen
        total_ahorro = sum(a['monto'] for a in ahorros_nuevos)
        miembros_ahorrando = sum(1 for a in ahorros_nuevos if a['monto'] > 0)
        no_cumplen_minimo = sum(1 for a in ahorros_nuevos if not a['cumple_minimo'])
        col_res1, col_res2, col_res3, col_res4 = st.columns(4)
        with col_res1:
            st.metric("👥 Miembros ahorrando", miembros_ahorrando)
        with col_res2:
            st.metric("💰 Total a ahorrar", f"${total_ahorro:.2f}")
        with col_res3:
            promedio = total_ahorro / len(ahorros_nuevos) if ahorros_nuevos else 0
            st.metric("📊 Promedio", f"${promedio:.2f}")
        with col_res4:
            if aplica_multa and no_cumplen_minimo > 0:
                st.metric("⚠️ Con multa", no_cumplen_minimo)
        st.divider()
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 Guardar Ahorros", type="primary", use_container_width=True, key=f"guardar_{id_reunion}", disabled=solo_lectura):
                try:
                    usuario_id = st.session_state.get('usuario', {}).get('Id_usuario')
                    registros_guardados = 0
                    for ahorro in ahorros_nuevos:
                        cursor.execute("""
                            INSERT INTO Ahorros 
                            (Id_miembro, Id_grupo, Id_Ciclo, Id_reunion, Monto, Fecha_ahorro, Observaciones, Registrado_por)
                            VALUES (%s, %s, %s, %s, %s, CURDATE(), %s, %s)
                            ON DUPLICATE KEY UPDATE
                            Monto = VALUES(Monto),
                            Observaciones = VALUES(Observaciones),
                            Fecha_ahorro = CURDATE()
                        """, (
                            ahorro['id_miembro'],
                            reunion['Id_grupo'],
                            reunion['Id_Ciclo'],
                            id_reunion,
                            ahorro['monto'],
                            ahorro['observaciones'],
                            usuario_id
                        ))
                        registros_guardados += 1
                    cursor.execute("""
                        UPDATE Ciclo 
                        SET Ahorro_Acumulado = (
                            SELECT IFNULL(SUM(Monto), 0) FROM Ahorros WHERE Id_Ciclo = %s AND Estado = 'Activo'
                        )
                        WHERE Id_Ciclo = %s
                    """, (reunion['Id_Ciclo'], reunion['Id_Ciclo']))
                    conexion.commit()
                    st.success(f"✅ Ahorros registrados para {registros_guardados} miembro(s). Total: ${total_ahorro:.2f}")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    conexion.rollback()
                    st.error(f"❌ Error: {str(e)}")
        with col_btn2:
            if aplica_multa and no_cumplen_minimo > 0:
                st.write(f"**Aplicar multas automáticas**")
                aplicar_multas_ahorro = st.checkbox(f"Multar a {no_cumplen_minimo} miembro(s) que no cumplen el mínimo", value=True, key=f"multas_{id_reunion}", disabled=solo_lectura)
                if st.button("⚠️ Aplicar Multas", type="secondary", use_container_width=True, disabled=not aplicar_multas_ahorro or solo_lectura, key=f"aplicar_multas_{id_reunion}"):
                    try:
                        usuario_id = st.session_state.get('usuario', {}).get('Id_usuario')
                        multas_aplicadas = 0
                        miembros_multados = []
                        for ahorro in ahorros_nuevos:
                            if not ahorro['cumple_minimo']:
                                cursor.execute("""
                                    SELECT Id_multa FROM Multas 
                                    WHERE Id_miembro = %s AND Id_reunion = %s AND Tipo_multa = 'Falta_Pago'
                                """, (ahorro['id_miembro'], id_reunion))
                                if not cursor.fetchone():
                                    descripcion = f"No cumplió monto mínimo de ahorro (${monto_minimo:.2f}). Ahorró: ${ahorro['monto']:.2f}"
                                    cursor.execute("""
                                        INSERT INTO Multas 
                                        (Id_miembro, Id_grupo, Id_Ciclo, Id_reunion, Tipo_multa, Monto, Descripcion, Fecha_multa, Aplicado_por)
                                        VALUES (%s, %s, %s, %s, 'Falta_Pago', %s, %s, CURDATE(), %s)
                                    """, (
                                        ahorro['id_miembro'],
                                        reunion['Id_grupo'],
                                        reunion['Id_Ciclo'],
                                        id_reunion,
                                        monto_multa,
                                        descripcion,
                                        usuario_id
                                    ))
                                    multas_aplicadas += 1
                                    miembros_multados.append(f"{ahorro['nombre']} (${monto_multa:.2f})")
                        conexion.commit()
                        if multas_aplicadas > 0:
                            st.success(f"✅ {multas_aplicadas} multa(s) aplicada(s)")
                            with st.expander("Ver miembros multados"):
                                for info in miembros_multados:
                                    st.write(f"- {info}")
                            st.rerun()
                        else:
                            st.info("ℹ️ No se aplicaron multas nuevas (ya existían)")
                    except Exception as e:
                        conexion.rollback()
                        st.error(f"❌ Error: {str(e)}")
    finally:
        conexion.close()


def configurar_monto_minimo(id_ciclo_filtro=None, id_distrito=None, id_grupo=None, solo_lectura=False):
    """
    Configuración del monto mínimo de ahorro requerido.
    """
    st.subheader("⚙️ Configuración de Monto Mínimo de Ahorro")
    
    st.info("💡 Establece el monto mínimo que cada miembro debe ahorrar en cada reunión. "
            "Si un miembro asiste pero no ahorra el mínimo, se puede aplicar una multa automática.")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    cursor = conexion.cursor(dictionary=True)
    try:
        # Solo filtrar por grupo si se recibe id_grupo (directiva), si no, usar configuración global
        if id_grupo is not None:
            # Si en el futuro se quiere configuración por grupo, aquí se puede implementar
            cursor.execute("SELECT * FROM Configuracion_Ahorros LIMIT 1")
        else:
            cursor.execute("SELECT * FROM Configuracion_Ahorros LIMIT 1")
        config = cursor.fetchone()
        if not config:
            st.warning("⚠️ No hay configuración registrada. Se creará una nueva.")
            config = {
                'Monto_minimo': 2.00,
                'Aplica_multa': 1,
                'Monto_multa': 1.00,
                'Descripcion': ''
            }
        
        with st.form("form_config_ahorro"):
            st.write("### 💰 Configuración de Monto Mínimo")
            
            col1, col2 = st.columns(2)
            
            with col1:
                monto_minimo = st.number_input(
                    "💵 Monto Mínimo de Ahorro por Reunión ($)",
                    min_value=0.0,
                    value=float(config['Monto_minimo']),
                    step=0.50,
                    format="%.2f",
                    help="Cantidad mínima que cada miembro debe ahorrar en cada reunión",
                    disabled=solo_lectura
                )
                
                aplica_multa = st.checkbox(
                    "⚠️ Aplicar multa automática si no cumple el mínimo",
                    value=bool(config['Aplica_multa']),
                    help="Si está activado, se aplicará una multa a los miembros que no ahorren el mínimo",
                    disabled=solo_lectura
                )
            
            with col2:
                monto_multa = st.number_input(
                    "💸 Monto de la Multa ($)",
                    min_value=0.0,
                    value=float(config['Monto_multa']),
                    step=0.50,
                    format="%.2f",
                    disabled=not aplica_multa or solo_lectura,
                    help="Cantidad a multar si no se cumple el monto mínimo"
                )
                
                st.write("")  # Espaciado
                st.write("")
                
                if monto_minimo > 0 and aplica_multa:
                    st.warning(f"⚠️ Se multará con ${monto_multa:.2f} a quien no ahorre mínimo ${monto_minimo:.2f}")
                elif monto_minimo > 0:
                    st.info(f"ℹ️ Se sugiere ahorrar mínimo ${monto_minimo:.2f} (sin multa)")
                else:
                    st.success("✅ Sin monto mínimo requerido")
            
            descripcion = st.text_area(
                "📝 Descripción/Notas",
                value=config.get('Descripcion', ''),
                placeholder="Ej: Acuerdo establecido en reunión del 01/01/2025",
                height=80,
                disabled=solo_lectura
            )
            
            st.divider()
            
            # Ejemplos
            st.write("### 📊 Ejemplos de Aplicación")
            
            col_ej1, col_ej2, col_ej3 = st.columns(3)
            
            with col_ej1:
                st.info("**Ejemplo 1:**\n\n"
                       f"Miembro ahorra: $0.00\n\n"
                       f"Resultado: {'❌ Multa de $' + f'{monto_multa:.2f}' if aplica_multa else '✅ Sin multa'}")
            
            with col_ej2:
                ejemplo_monto = monto_minimo / 2 if monto_minimo > 0 else 1.00
                st.info("**Ejemplo 2:**\n\n"
                       f"Miembro ahorra: ${ejemplo_monto:.2f}\n\n"
                       f"Resultado: {'❌ Multa de $' + f'{monto_multa:.2f}' if (aplica_multa and ejemplo_monto < monto_minimo) else '✅ Sin multa'}")
            
            with col_ej3:
                st.success("**Ejemplo 3:**\n\n"
                          f"Miembro ahorra: ${monto_minimo:.2f}\n\n"
                          f"Resultado: ✅ Cumple mínimo")
            
            submitted = st.form_submit_button("💾 Guardar Configuración", type="primary", disabled=solo_lectura)
            
            if submitted and not solo_lectura:
                try:
                    # Solo hay una configuración global, actualizar o insertar
                    cursor.execute("SELECT Id_config FROM Configuracion_Ahorros LIMIT 1")
                    existe = cursor.fetchone()
                    if existe:
                        cursor.execute("""
                            UPDATE Configuracion_Ahorros 
                            SET Monto_minimo = %s,
                                Aplica_multa = %s,
                                Monto_multa = %s,
                                Descripcion = %s
                            WHERE Id_config = %s
                        """, (monto_minimo, int(aplica_multa), monto_multa, descripcion, existe['Id_config']))
                    else:
                        cursor.execute("""
                            INSERT INTO Configuracion_Ahorros (Monto_minimo, Aplica_multa, Monto_multa, Descripcion)
                            VALUES (%s, %s, %s, %s)
                        """, (monto_minimo, int(aplica_multa), monto_multa, descripcion))
                    conexion.commit()
                    st.success("✅ Configuración guardada correctamente")
                    st.rerun()
                except Exception as e:
                    conexion.rollback()
                    st.error(f"❌ Error: {str(e)}")
    
    finally:
        conexion.close()


def ver_ahorros(id_ciclo_filtro=None, id_distrito=None, id_grupo=None):
    """
    Visualizar todos los ahorros registrados.
    """
    st.subheader("📋 Lista de Ahorros")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            if id_grupo is not None:
                # Solo mostrar el grupo de pertenencia, sin opción a elegir
                cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE Id_grupo = %s", (id_grupo,))
                grupo = cursor.fetchone()
                if grupo:
                    st.info(f"Grupo: {grupo['Nombre']}")
                    id_grupo_filtro = grupo['Id_grupo']
                else:
                    st.warning("No se encontró el grupo asignado.")
                    id_grupo_filtro = None
            else:
                if id_distrito is not None:
                    cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE distrito_id = %s ORDER BY Nombre", (id_distrito,))
                else:
                    cursor.execute("SELECT Id_grupo, Nombre FROM Grupos ORDER BY Nombre")
                grupos = cursor.fetchall()
                grupos_dict = {"Todos": None}
                grupos_dict.update({g['Nombre']: g['Id_grupo'] for g in grupos})
                grupo_filtro = st.selectbox("Filtrar por Grupo", list(grupos_dict.keys()))
                id_grupo_filtro = grupos_dict[grupo_filtro]
        
        with col2:
            # Obtener todos los ciclos (activos y completados)
            cursor.execute("""
                SELECT 
                    c.*,
                    CASE 
                        WHEN CURDATE() < c.Fecha_Inicio THEN 'Pendiente'
                        WHEN CURDATE() BETWEEN c.Fecha_Inicio AND c.Fecha_Fin THEN 'Activo'
                        WHEN CURDATE() > c.Fecha_Fin THEN 'Completado'
                    END as Estado
                FROM Ciclo c
                ORDER BY c.Fecha_Inicio DESC
            """)
            ciclos = cursor.fetchall()
            ciclos_dict = {"Todos": None}
            ciclos_dict.update({
                f"Ciclo {c['Id_Ciclo']} ({c['Estado']})": c['Id_Ciclo'] 
                for c in ciclos
            })
            if id_ciclo_filtro is None:
                ciclo_filtro = st.selectbox("Filtrar por Ciclo", list(ciclos_dict.keys()), key="ciclo_ver_ahorros")
                id_ciclo_filtro = ciclos_dict[ciclo_filtro]
        
        with col3:
            estado_filtro = st.selectbox("Estado", ["Todos", "Activo", "Devuelto"])
        
        # Construir consulta
        query = """
            SELECT 
                ah.Id_ahorro,
                ah.Fecha_ahorro,
                ah.Monto,
                ah.Estado,
                ah.Observaciones,
                m.nombre AS Nombre_Miembro,
                g.Nombre AS Nombre_Grupo,
                r.Numero_semana,
                r.Fecha_reunion,
                u.Nombre_Usuario AS Registrado_Por
            FROM Ahorros ah
            JOIN Miembros m ON ah.Id_miembro = m.id
            JOIN Grupos g ON ah.Id_grupo = g.Id_grupo
            LEFT JOIN Reuniones r ON ah.Id_reunion = r.Id_reunion
            LEFT JOIN Usuarios u ON ah.Registrado_por = u.Id_usuario
            WHERE 1=1
        """
        params = []
        if id_distrito is not None:
            query += " AND g.distrito_id = %s"
            params.append(id_distrito)
        if id_grupo_filtro:
            query += " AND ah.Id_grupo = %s"
            params.append(id_grupo_filtro)
        if id_ciclo_filtro:
            query += " AND ah.Id_Ciclo = %s"
            params.append(id_ciclo_filtro)
        if estado_filtro != "Todos":
            query += " AND ah.Estado = %s"
            params.append(estado_filtro)
        query += " ORDER BY ah.Fecha_ahorro DESC"
        cursor.execute(query, params)
        ahorros = cursor.fetchall()
        
        if not ahorros:
            st.info("📭 No hay ahorros registrados que coincidan con los filtros")
        else:
            # Estadísticas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Registros", len(ahorros))
            with col2:
                activos = [a for a in ahorros if a['Estado'] == 'Activo']
                monto_activo = sum([a['Monto'] for a in activos])
                st.metric("💰 Ahorros Activos", f"${monto_activo:.2f}")
            with col3:
                devueltos = [a for a in ahorros if a['Estado'] == 'Devuelto']
                monto_devuelto = sum([a['Monto'] for a in devueltos])
                st.metric("✅ Devueltos", f"${monto_devuelto:.2f}")
            with col4:
                total_monto = sum([a['Monto'] for a in ahorros])
                st.metric("💵 Total General", f"${total_monto:.2f}")
            
            st.divider()
            
            # Tabla de ahorros
            df = pd.DataFrame(ahorros)
            df = df.rename(columns={
                'Id_ahorro': 'ID',
                'Fecha_ahorro': 'Fecha',
                'Monto': 'Monto ($)',
                'Estado': 'Estado',
                'Nombre_Miembro': 'Miembro',
                'Nombre_Grupo': 'Grupo',
                'Numero_semana': 'Semana',
                'Registrado_Por': 'Registrado Por'
            })
            
            st.dataframe(
                df[['ID', 'Fecha', 'Miembro', 'Grupo', 'Semana', 'Monto ($)', 'Estado']],
                use_container_width=True,
                hide_index=True
            )
            
            # Detalles expandibles
            st.divider()
            st.write("### 📌 Detalles de Ahorros")
            
            for ahorro in ahorros[:20]:  # Limitar a 20 para no sobrecargar
                estado_emoji = {'Activo': '💰', 'Devuelto': '✅'}
                
                with st.expander(f"{estado_emoji.get(ahorro['Estado'], '💵')} {ahorro['Nombre_Miembro']} - ${ahorro['Monto']:.2f} ({ahorro['Fecha_ahorro']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**👤 Miembro:** {ahorro['Nombre_Miembro']}")
                        st.write(f"**👥 Grupo:** {ahorro['Nombre_Grupo']}")
                        st.write(f"**📅 Fecha:** {ahorro['Fecha_ahorro']}")
                        st.write(f"**💰 Monto:** ${ahorro['Monto']:.2f}")
                    
                    with col2:
                        st.write(f"**🔢 Semana:** {ahorro['Numero_semana'] or 'N/A'}")
                        st.write(f"**📋 Reunión:** {ahorro['Fecha_reunion'] or 'N/A'}")
                        st.write(f"**📊 Estado:** {ahorro['Estado']}")
                        st.write(f"**👤 Registrado por:** {ahorro['Registrado_Por'] or 'Sistema'}")
                    
                    if ahorro['Observaciones']:
                        st.info(f"📝 {ahorro['Observaciones']}")
    
    finally:
        conexion.close()


def reportes_ahorros(id_ciclo_filtro=None, id_distrito=None):
    """
    Reportes y estadísticas de ahorros.
    """
    st.subheader("📊 Reportes de Ahorros")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Reporte por miembro
        st.write("#### 👤 Ahorros por Miembro")
        
        query_miembros = """
            SELECT 
                m.nombre AS Miembro,
                g.Nombre AS Grupo,
                COUNT(ah.Id_ahorro) AS Total_Ahorros,
                SUM(CASE WHEN ah.Estado = 'Activo' THEN ah.Monto ELSE 0 END) AS Monto_Activo,
                SUM(CASE WHEN ah.Estado = 'Devuelto' THEN ah.Monto ELSE 0 END) AS Monto_Devuelto,
                SUM(ah.Monto) AS Total_Ahorado
            FROM Miembros m
            JOIN Grupos g ON m.grupo_id = g.Id_grupo
            LEFT JOIN Ahorros ah ON ah.Id_miembro = m.id
        """
        params_miembros = []
        where_clauses = []
        if id_ciclo_filtro:
            where_clauses.append("ah.Id_Ciclo = %s")
            params_miembros.append(id_ciclo_filtro)
        if id_distrito is not None:
            where_clauses.append("g.distrito_id = %s")
            params_miembros.append(id_distrito)
        if where_clauses:
            query_miembros += " WHERE " + " AND ".join(where_clauses)
        query_miembros += " GROUP BY m.id HAVING Total_Ahorros > 0 ORDER BY Total_Ahorado DESC"
        cursor.execute(query_miembros, params_miembros)
        
        reporte_miembros = cursor.fetchall()
        
        if reporte_miembros:
            df = pd.DataFrame(reporte_miembros)
            df = df.rename(columns={
                'Miembro': 'Miembro',
                'Grupo': 'Grupo',
                'Total_Ahorros': 'Nº Ahorros',
                'Monto_Activo': 'Activo ($)',
                'Monto_Devuelto': 'Devuelto ($)',
                'Total_Ahorrado': 'Total ($)'
            })
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos de ahorros")
        
        st.divider()
        
        # Reporte por grupo
        st.write("#### 👥 Ahorros por Grupo")
        
        query_grupos = """
            SELECT 
                g.Nombre AS Grupo,
                COUNT(DISTINCT ah.Id_miembro) AS Miembros_Ahorrando,
                COUNT(ah.Id_ahorro) AS Total_Ahorros,
                SUM(CASE WHEN ah.Estado = 'Activo' THEN ah.Monto ELSE 0 END) AS Monto_Activo,
                SUM(ah.Monto) AS Total_Ahorado
            FROM Grupos g
            LEFT JOIN Ahorros ah ON ah.Id_grupo = g.Id_grupo
        """
        params_grupos = []
        where_clauses_g = []
        if id_ciclo_filtro:
            where_clauses_g.append("ah.Id_Ciclo = %s")
            params_grupos.append(id_ciclo_filtro)
        if id_distrito is not None:
            where_clauses_g.append("g.distrito_id = %s")
            params_grupos.append(id_distrito)
        if where_clauses_g:
            query_grupos += " WHERE " + " AND ".join(where_clauses_g)
        query_grupos += " GROUP BY g.Id_grupo HAVING Total_Ahorros > 0 ORDER BY Total_Ahorado DESC"
        cursor.execute(query_grupos, params_grupos)
        
        reporte_grupos = cursor.fetchall()
        
        if reporte_grupos:
            df_grupos = pd.DataFrame(reporte_grupos)
            df_grupos = df_grupos.rename(columns={
                'Grupo': 'Grupo',
                'Miembros_Ahorrando': 'Miembros',
                'Total_Ahorros': 'Nº Ahorros',
                'Monto_Activo': 'Activo ($)',
                'Total_Ahorrado': 'Total ($)'
            })
            st.dataframe(df_grupos, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Reporte por ciclo
        st.write("#### 🔄 Ahorros por Ciclo")
        
        query_ciclos = """
            SELECT 
                c.Id_Ciclo AS Ciclo,
                c.Fecha_Inicio,
                c.Fecha_Fin,
                COUNT(ah.Id_ahorro) AS Total_Ahorros,
                COUNT(DISTINCT ah.Id_miembro) AS Miembros_Participantes,
                SUM(CASE WHEN ah.Estado = 'Activo' THEN ah.Monto ELSE 0 END) AS Pendiente_Devolver,
                SUM(CASE WHEN ah.Estado = 'Devuelto' THEN ah.Monto ELSE 0 END) AS Ya_Devuelto,
                SUM(ah.Monto) AS Total_Ahorrado
            FROM Ciclo c
            LEFT JOIN Ahorros ah ON ah.Id_Ciclo = c.Id_Ciclo
            LEFT JOIN Grupos g ON ah.Id_grupo = g.Id_grupo
        """
        params_ciclos = []
        where_clauses_c = []
        if id_distrito is not None:
            where_clauses_c.append("g.distrito_id = %s")
            params_ciclos.append(id_distrito)
        if where_clauses_c:
            query_ciclos += " WHERE " + " AND ".join(where_clauses_c)
        query_ciclos += " GROUP BY c.Id_Ciclo HAVING Total_Ahorros > 0 ORDER BY c.Fecha_Inicio DESC"
        cursor.execute(query_ciclos, params_ciclos)
        reporte_ciclos = cursor.fetchall()
        
        if reporte_ciclos:
            df_ciclos = pd.DataFrame(reporte_ciclos)
            df_ciclos = df_ciclos.rename(columns={
                'Ciclo': 'Ciclo',
                'Fecha_Inicio': 'Inicio',
                'Fecha_Fin': 'Fin',
                'Total_Ahorros': 'Nº Ahorros',
                'Miembros_Participantes': 'Miembros',
                'Pendiente_Devolver': 'Pendiente ($)',
                'Ya_Devuelto': 'Devuelto ($)',
                'Total_Ahorrado': 'Total ($)'
            })
            st.dataframe(df_ciclos, use_container_width=True, hide_index=True)
    
    finally:
        conexion.close()


def devolver_ahorros(id_ciclo, id_distrito=None, solo_lectura=False):
    """
    Proceso para devolver ahorros al final del ciclo seleccionado.
    """
    st.subheader("💸 Devolución de Ahorros")
    st.info("💡 Utiliza esta función al finalizar un ciclo para devolver los ahorros acumulados a los miembros.")
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    cursor = conexion.cursor(dictionary=True)
    try:
        # Obtener datos del ciclo seleccionado
        query_ciclo = """
            SELECT 
                c.Id_Ciclo,
                c.Fecha_Inicio,
                c.Fecha_Fin,
                COUNT(ah.Id_ahorro) AS Total_Ahorros,
                SUM(CASE WHEN ah.Estado = 'Activo' THEN ah.Monto ELSE 0 END) AS Monto_Pendiente
            FROM Ciclo c
            LEFT JOIN Ahorros ah ON ah.Id_Ciclo = c.Id_Ciclo
            LEFT JOIN Grupos g ON ah.Id_grupo = g.Id_grupo
            WHERE c.Id_Ciclo = %s
        """
        params_ciclo = [id_ciclo]
        if id_distrito is not None:
            query_ciclo += " AND g.distrito_id = %s"
            params_ciclo.append(id_distrito)
        query_ciclo += " GROUP BY c.Id_Ciclo"
        cursor.execute(query_ciclo, params_ciclo)
        ciclo = cursor.fetchone()
        if not ciclo or ciclo['Monto_Pendiente'] is None or ciclo['Monto_Pendiente'] == 0:
            st.info("📭 No hay ahorros activos pendientes de devolución en este ciclo")
            return
        st.write(f"**🔄 Ciclo:** {ciclo['Id_Ciclo']}")
        st.write(f"**📅 Período:** {ciclo['Fecha_Inicio']} - {ciclo['Fecha_Fin']}")
        st.write(f"**💰 Total a devolver:** ${ciclo['Monto_Pendiente']:.2f}")
        st.divider()
        # Obtener resumen de ahorros por miembro en este ciclo
        query_miembros = """
            SELECT 
                m.id,
                m.nombre AS Nombre_Miembro,
                g.Nombre AS Nombre_Grupo,
                COUNT(ah.Id_ahorro) AS Num_Ahorros,
                SUM(ah.Monto) AS Total_Ahorrado,
                SUM(CASE WHEN ah.Estado = 'Activo' THEN ah.Monto ELSE 0 END) AS Pendiente_Devolver
            FROM Miembros m
            JOIN Grupos g ON m.grupo_id = g.Id_grupo
            JOIN Ahorros ah ON ah.Id_miembro = m.id
            WHERE ah.Id_Ciclo = %s AND ah.Estado = 'Activo'
        """
        params_miembros = [id_ciclo]
        if id_distrito is not None:
            query_miembros += " AND g.distrito_id = %s"
            params_miembros.append(id_distrito)
        query_miembros += " GROUP BY m.id ORDER BY g.Nombre, m.nombre"
        cursor.execute(query_miembros, params_miembros)
        miembros_ahorros = cursor.fetchall()
        if not miembros_ahorros:
            st.info("✅ No hay ahorros activos pendientes de devolución en este ciclo")
            return
        st.write("### 📋 Detalles por Miembro")
        df = pd.DataFrame(miembros_ahorros)
        df = df.rename(columns={
            'Nombre_Miembro': 'Miembro',
            'Nombre_Grupo': 'Grupo',
            'Num_Ahorros': 'Nº Ahorros',
            'Pendiente_Devolver': 'A Devolver ($)'
        })
        st.dataframe(
            df[['Miembro', 'Grupo', 'Nº Ahorros', 'A Devolver ($)']],
            use_container_width=True,
            hide_index=True
        )
        st.divider()
        # Opciones de devolución
        col1, col2 = st.columns(2)
        with col1:
            st.write("### 💸 Devolución Individual")
            miembros_dict = {
                f"{ma['Nombre_Miembro']} ({ma['Nombre_Grupo']}) - ${ma['Pendiente_Devolver']:.2f}": ma['id']
                for ma in miembros_ahorros
            }
            if miembros_dict:
                miembro_sel = st.selectbox("Seleccionar miembro", list(miembros_dict.keys()), key=f"dev_ind_{id_ciclo}", disabled=solo_lectura)
                id_miembro_sel = miembros_dict[miembro_sel]
                if st.button("✅ Marcar como Devuelto", type="secondary", use_container_width=True, key=f"btn_dev_ind_{id_ciclo}", disabled=solo_lectura):
                    try:
                        update_query = "UPDATE Ahorros SET Estado = 'Devuelto', Fecha_devolucion = CURDATE() WHERE Id_miembro = %s AND Id_Ciclo = %s AND Estado = 'Activo'"
                        update_params = [id_miembro_sel, id_ciclo]
                        if id_distrito is not None:
                            update_query += " AND Id_grupo IN (SELECT Id_grupo FROM Grupos WHERE distrito_id = %s)"
                            update_params.append(id_distrito)
                        cursor.execute(update_query, update_params)
                        conexion.commit()
                        miembro_info = next(m for m in miembros_ahorros if m['id'] == id_miembro_sel)
                        st.success(f"✅ Ahorros devueltos: ${miembro_info['Pendiente_Devolver']:.2f}")
                        st.rerun()
                    except Exception as e:
                        conexion.rollback()
                        st.error(f"❌ Error: {str(e)}")
        with col2:
            st.write("### 💸 Devolución Masiva")
            st.warning("⚠️ Esta acción marcará TODOS los ahorros del ciclo como devueltos")
            confirmar = st.checkbox("Confirmo que todos los ahorros han sido devueltos físicamente", key=f"chk_dev_all_{id_ciclo}", disabled=solo_lectura)
            if st.button("✅ Devolver Todos los Ahorros", type="primary", use_container_width=True, disabled=not confirmar or solo_lectura, key=f"btn_dev_all_{id_ciclo}"):
                try:
                    update_query = "UPDATE Ahorros SET Estado = 'Devuelto', Fecha_devolucion = CURDATE() WHERE Id_Ciclo = %s AND Estado = 'Activo'"
                    update_params = [id_ciclo]
                    if id_distrito is not None:
                        update_query += " AND Id_grupo IN (SELECT Id_grupo FROM Grupos WHERE distrito_id = %s)"
                        update_params.append(id_distrito)
                    cursor.execute(update_query, update_params)
                    registros_actualizados = cursor.rowcount
                    conexion.commit()
                    st.success(f"✅ {registros_actualizados} ahorros marcados como devueltos. Total: ${ciclo['Monto_Pendiente']:.2f}")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    conexion.rollback()
                    st.error(f"❌ Error: {str(e)}")
    finally:
        conexion.close()
