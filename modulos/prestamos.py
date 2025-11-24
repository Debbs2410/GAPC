import pandas as pd

def obtener_datos_cartera_mora(id_grupo):
    from modulos.config.conexion import obtener_conexion
    conexion = obtener_conexion()
    if not conexion:
        return None
    cursor = conexion.cursor(dictionary=True)
    # Cartera de préstamos y mora por grupo
    cursor.execute('''
        SELECT p.Id_prestamo, m.nombre as Miembro, p.Monto_total, p.Estado
        FROM Prestamos p
        LEFT JOIN Miembros m ON p.Id_miembro = m.id
        WHERE p.Id_grupo = %s
    ''', (id_grupo,))
    rows = cursor.fetchall()
    conexion.close()
    if rows:
        return pd.DataFrame(rows)
    return None
"""
Módulo de Gestión de Préstamos
Permite a los miembros solicitar préstamos basados en sus ahorros acumulados
"""
import streamlit as st
from modulos.solo_lectura import es_administradora
import pandas as pd
from datetime import datetime, timedelta
from modulos.config.conexion import obtener_conexion

def gestionar_prestamos(id_distrito=None, id_grupo=None):
    """Función principal del módulo de préstamos. Si se proporciona id_distrito o id_grupo, filtra por ese contexto."""
    st.title("💰 Gestión de Préstamos")
    # Solo lectura para administradora
    solo_lectura = es_administradora()
    # Verificar autenticación
    if 'usuario' not in st.session_state:
        st.error("⛔ Debes iniciar sesión primero")
        return
    # Pestañas principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Solicitar Préstamo",
        "📋 Ver Préstamos", 
        "💵 Registrar Pago",
        "📊 Reportes",
        "⚙️ Configuración"
    ])
    with tab1:
        solicitar_prestamo(id_distrito=id_distrito, id_grupo=id_grupo, solo_lectura=solo_lectura)
    with tab2:
        ver_prestamos(id_distrito=id_distrito, id_grupo=id_grupo)
    with tab3:
        registrar_pago_prestamo(id_distrito=id_distrito, id_grupo=id_grupo, solo_lectura=solo_lectura)
    with tab4:
        reportes_prestamos(id_distrito=id_distrito, id_grupo=id_grupo)
    with tab5:
        configurar_prestamos(id_distrito=id_distrito, id_grupo=id_grupo, solo_lectura=solo_lectura)

def obtener_ahorro_disponible(id_miembro, id_ciclo):
    """Calcula el monto total ahorrado menos los préstamos activos"""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Total ahorrado en el ciclo actual (todos los ahorros registrados)
        cursor.execute("""
            SELECT COALESCE(SUM(Monto), 0) as total_ahorrado
            FROM Ahorros
            WHERE Id_miembro = %s 
            AND Id_Ciclo = %s
        """, (id_miembro, id_ciclo))
        ahorro = cursor.fetchone()
        total_ahorrado = float(ahorro['total_ahorrado'] or 0)
        
        # Total de préstamos pendientes (monto total menos lo pagado)
        cursor.execute("""
            SELECT COALESCE(SUM(Monto_total - COALESCE(
                (SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo), 0
            )), 0) as total_prestado
            FROM Prestamos p
            WHERE Id_miembro = %s 
            AND Id_Ciclo = %s
            AND Estado IN ('Pendiente', 'Vencido')
        """, (id_miembro, id_ciclo))
        prestamo = cursor.fetchone()
        total_prestado = float(prestamo['total_prestado'] or 0)
        
        disponible = total_ahorrado - total_prestado
        
        return {
            'total_ahorrado': total_ahorrado,
            'total_prestado': total_prestado,
            'disponible': max(0, disponible)
        }
        
    finally:
        cursor.close()
        conexion.close()

def solicitar_prestamo(id_distrito=None, id_grupo=None, solo_lectura=False):
    """Registrar un nuevo préstamo"""
    st.header("📝 Solicitar Préstamo")
    if solo_lectura:
        st.info("🔒 La administradora solo puede ver los préstamos y reportes. No puede solicitar préstamos.")
        return
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        # Obtener rol del usuario
        usuario = st.session_state.get('usuario', {}) if 'usuario' in st.session_state else {}
        rol = (usuario.get('Rol') or usuario.get('rol') or '').strip().lower()
        # Filtrar ciclos solo para directiva
        if rol == 'directiva' and id_grupo is not None:
            cursor.execute("""
                SELECT c.*,
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
        elif id_distrito is not None:
            cursor.execute("""
                SELECT DISTINCT c.*,
                    CASE 
                        WHEN CURDATE() < c.Fecha_Inicio THEN 'Pendiente'
                        WHEN CURDATE() BETWEEN c.Fecha_Inicio AND c.Fecha_Fin THEN 'Activo'
                        WHEN CURDATE() > c.Fecha_Fin THEN 'Completado'
                    END as Estado
                FROM Ciclo c
                INNER JOIN Grupos g ON g.Id_Ciclo = c.Id_Ciclo
                WHERE g.distrito_id = %s
                HAVING Estado = 'Activo'
                ORDER BY c.Fecha_Inicio DESC
            """, (id_distrito,))
        else:
            cursor.execute("""
                SELECT 
                    c.*,
                    CASE 
                        WHEN CURDATE() < c.Fecha_Inicio THEN 'Pendiente'
                        WHEN CURDATE() BETWEEN c.Fecha_Inicio AND c.Fecha_Fin THEN 'Activo'
                        WHEN CURDATE() > c.Fecha_Fin THEN 'Completado'
                    END as Estado
                FROM Ciclo c
                HAVING Estado = 'Activo'
                ORDER BY c.Fecha_Inicio DESC
            """)
        ciclos_activos = cursor.fetchall()
        if not ciclos_activos:
            st.warning("⚠️ No hay ningún ciclo activo")
            return
        # Selector de ciclo
        if len(ciclos_activos) > 1:
            ciclo_opciones = {
                f"Ciclo {c['Id_Ciclo']} ({c['Fecha_Inicio']} - {c['Fecha_Fin']})": c['Id_Ciclo'] 
                for c in ciclos_activos
            }
            ciclo_seleccionado = st.selectbox("📅 Selecciona el Ciclo", options=list(ciclo_opciones.keys()))
            id_ciclo = ciclo_opciones[ciclo_seleccionado]
        else:
            id_ciclo = ciclos_activos[0]['Id_Ciclo']
            st.info(f"📅 **Ciclo Activo:** Ciclo {id_ciclo} ({ciclos_activos[0]['Fecha_Inicio']} - {ciclos_activos[0]['Fecha_Fin']})")
        
        # Seleccionar grupo según el rol
        if id_grupo is not None:
            cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE Id_grupo = %s ORDER BY Nombre", (id_grupo,))
        elif id_distrito is not None:
            cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE distrito_id = %s ORDER BY Nombre", (id_distrito,))
        else:
            cursor.execute("SELECT Id_grupo, Nombre FROM Grupos ORDER BY Nombre")
        grupos = cursor.fetchall()
        if not grupos:
            st.warning("⚠️ No hay grupos registrados")
            return
        grupo_opciones = {f"{g['Nombre']}": g['Id_grupo'] for g in grupos}
        if id_grupo is not None and len(grupos) == 1:
            grupo_seleccionado = list(grupo_opciones.keys())[0]
            st.selectbox("Selecciona el Grupo", options=[grupo_seleccionado], index=0, disabled=True)
        else:
            grupo_seleccionado = st.selectbox("Selecciona el Grupo", options=list(grupo_opciones.keys()))
            id_grupo = grupo_opciones[grupo_seleccionado]
        
        # Obtener miembros del grupo
        cursor.execute("""
            SELECT id, nombre 
            FROM Miembros 
            WHERE grupo_id = %s
            ORDER BY nombre
        """, (id_grupo,))
        miembros = cursor.fetchall()
        if not miembros:
            st.warning("⚠️ No hay miembros en este grupo")
            return

        # Filtrar miembros que NO tienen préstamos activos (Pendiente o Vencido) en este ciclo y grupo
        miembros_disponibles = []
        for m in miembros:
            cursor.execute("""
                SELECT COUNT(*) as tiene_activo
                FROM Prestamos
                WHERE Id_miembro = %s AND Id_grupo = %s AND Id_Ciclo = %s AND Estado IN ('Pendiente', 'Vencido')
            """, (m['id'], id_grupo, id_ciclo))
            tiene_activo = cursor.fetchone()['tiene_activo']
            if tiene_activo == 0:
                miembros_disponibles.append(m)

        if not miembros_disponibles:
            st.warning("⚠️ Todos los miembros de este grupo ya tienen un préstamo en curso. No pueden solicitar otro hasta pagar el actual.")
            return

        miembro_opciones = {m['nombre']: m['id'] for m in miembros_disponibles}
        miembro_seleccionado = st.selectbox("Selecciona el Miembro", options=list(miembro_opciones.keys()))
        id_miembro = miembro_opciones[miembro_seleccionado]

        # Obtener ahorro disponible
        saldo = obtener_ahorro_disponible(id_miembro, id_ciclo)
        
        st.divider()
        
        # Mostrar información del ahorro
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Total Ahorrado", f"${saldo['total_ahorrado']:.2f}")
        with col2:
            st.metric("📉 Préstamos Activos", f"${saldo['total_prestado']:.2f}")
        with col3:
            st.metric("✅ Disponible para Préstamo", f"${saldo['disponible']:.2f}")
        
        if saldo['disponible'] <= 0:
            st.error("❌ Este miembro no tiene saldo disponible para préstamos")
            st.info("💡 **Debe tener ahorros activos y sin préstamos pendientes para poder solicitar un préstamo**")
            return
        
        st.divider()
        st.write("### 📄 Detalles del Préstamo")
        
        # Formulario de préstamo
        col1, col2 = st.columns(2)
        
        with col1:
            monto_prestamo = st.number_input(
                "Monto del Préstamo ($)",
                min_value=0.01,
                max_value=float(saldo['disponible']),
                value=min(50.0, float(saldo['disponible'])),
                step=0.50,
                help=f"Máximo disponible: ${saldo['disponible']:.2f}"
            )
            
            interes = st.number_input(
                "Tasa de Interés (%)",
                min_value=0.0,
                max_value=100.0,
                value=5.0,
                step=0.5,
                help="Porcentaje de interés sobre el monto prestado"
            )
            
            forma_pago = st.selectbox(
                "Forma de Pago",
                options=["Único", "Cuotas"],
                help="Pago único o en cuotas"
            )
        
        with col2:
            fecha_prestamo = st.date_input(
                "Fecha del Préstamo",
                value=datetime.now(),
                help="Fecha en que se otorga el préstamo"
            )
            
            if forma_pago == "Cuotas":
                numero_cuotas = st.number_input(
                    "Número de Cuotas",
                    min_value=2,
                    max_value=52,
                    value=4,
                    step=1
                )
            else:
                numero_cuotas = 1
            
            semanas_plazo = st.number_input(
                "Plazo (semanas)",
                min_value=1,
                max_value=52,
                value=4 if forma_pago == "Cuotas" else 4,
                step=1,
                help="Plazo para pagar el préstamo"
            )
            
            fecha_vencimiento = fecha_prestamo + timedelta(weeks=semanas_plazo)
            st.info(f"📅 Vencimiento: **{fecha_vencimiento.strftime('%d/%m/%Y')}**")
        
        # Calcular montos
        monto_interes = monto_prestamo * (interes / 100)
        monto_total = monto_prestamo + monto_interes
        monto_cuota = monto_total / numero_cuotas if numero_cuotas > 0 else monto_total
        
        # Validación
        if monto_prestamo > saldo['disponible']:
            st.error(f"❌ El monto solicitado (${monto_prestamo:.2f}) excede el disponible (${saldo['disponible']:.2f})")
            return
        
        st.divider()
        
        # Resumen del préstamo
        st.write("### 📊 Resumen del Préstamo")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💵 Monto Prestado", f"${monto_prestamo:.2f}")
        with col2:
            st.metric("📈 Interés", f"${monto_interes:.2f}", delta=f"{interes}%")
        with col3:
            st.metric("💰 Total a Pagar", f"${monto_total:.2f}")
        with col4:
            if numero_cuotas > 1:
                st.metric("📅 Cuota", f"${monto_cuota:.2f}", delta=f"{numero_cuotas}x")
            else:
                st.metric("📅 Pago Único", f"${monto_total:.2f}")
        
        descripcion = st.text_area(
            "Descripción / Motivo del Préstamo",
            placeholder="Ej: Para emergencia médica, inversión en negocio, etc.",
            help="Opcional: describe el motivo del préstamo"
        )
        
        st.divider()
        
        # Botón de registro
        if st.button("💰 Aprobar y Registrar Préstamo", type="primary", use_container_width=True):
            # Validar de nuevo que el miembro no tenga préstamo activo (por si cambia el estado en paralelo)
            cursor.execute("""
                SELECT COUNT(*) as tiene_activo
                FROM Prestamos
                WHERE Id_miembro = %s AND Id_grupo = %s AND Id_Ciclo = %s AND Estado IN ('Pendiente', 'Vencido')
            """, (id_miembro, id_grupo, id_ciclo))
            tiene_activo = cursor.fetchone()['tiene_activo']
            if tiene_activo > 0:
                st.error("❌ Este miembro ya tiene un préstamo en curso y no puede solicitar otro hasta pagarlo.")
                return
            try:
                usuario_id = st.session_state.usuario['Id_usuario']
                cursor.execute("""
                    INSERT INTO Prestamos 
                    (Id_miembro, Id_grupo, Id_Ciclo, Monto_prestado, Monto_disponible_ahorro,
                     Interes_porcentaje, Monto_interes, Monto_total, Fecha_prestamo, 
                     Fecha_vencimiento, Estado, Forma_pago, Numero_cuotas, Monto_cuota,
                     Descripcion, Aprobado_por)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pendiente', %s, %s, %s, %s, %s)
                """, (
                    id_miembro, id_grupo, id_ciclo, monto_prestamo, saldo['disponible'],
                    interes, monto_interes, monto_total, fecha_prestamo,
                    fecha_vencimiento, forma_pago, numero_cuotas, monto_cuota,
                    descripcion, usuario_id
                ))
                conexion.commit()
                st.success(f"✅ Préstamo aprobado y registrado exitosamente")
                st.balloons()
                st.info(f"💡 El miembro **{miembro_seleccionado}** debe pagar **${monto_total:.2f}** antes del **{fecha_vencimiento.strftime('%d/%m/%Y')}**")
                st.rerun()
            except Exception as e:
                conexion.rollback()
                st.error(f"❌ Error al registrar el préstamo: {str(e)}")
    
    finally:
        cursor.close()
        conexion.close()

def ver_prestamos(id_distrito=None, id_grupo=None):
    """Visualizar todos los préstamos"""
    st.header("📋 Préstamos Registrados")
    
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cursor.execute("""
                SELECT 
                    c.Id_Ciclo,
                    CONCAT('Ciclo ', c.Id_Ciclo, ' (', DATE_FORMAT(c.Fecha_Inicio, '%d/%m/%Y'), ' - ', DATE_FORMAT(c.Fecha_Fin, '%d/%m/%Y'), ')') as Nombre_ciclo
                FROM Ciclo c
                ORDER BY c.Fecha_Inicio DESC
            """)
            ciclos = cursor.fetchall()
            ciclo_opciones = ["Todos"] + [f"{c['Nombre_ciclo']}" for c in ciclos]
            ciclo_filtro = st.selectbox("Filtrar por Ciclo", ciclo_opciones)
        
        with col2:
            if id_grupo is not None:
                cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE Id_grupo = %s ORDER BY Nombre", (id_grupo,))
            elif id_distrito is not None:
                cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE distrito_id = %s ORDER BY Nombre", (id_distrito,))
            else:
                cursor.execute("SELECT Id_grupo, Nombre FROM Grupos ORDER BY Nombre")
            grupos = cursor.fetchall()
            if id_grupo is not None and len(grupos) == 1:
                grupo_opciones = [grupos[0]['Nombre']]
                grupo_filtro = st.selectbox("Filtrar por Grupo", grupo_opciones, index=0, disabled=True)
            else:
                grupo_opciones = ["Todos"] + [f"{g['Nombre']}" for g in grupos]
                grupo_filtro = st.selectbox("Filtrar por Grupo", grupo_opciones)
        
        with col3:
            estado_filtro = st.selectbox("Filtrar por Estado", ["Todos", "Pendiente", "Pagado", "Vencido"])
        
        # Construir query con filtros
        query = """
            SELECT 
                p.*,
                m.nombre as Nombre_Miembro,
                g.Nombre as Nombre_Grupo,
                CONCAT('Ciclo ', c.Id_Ciclo, ' (', DATE_FORMAT(c.Fecha_Inicio, '%d/%m/%Y'), ')') as Nombre_ciclo,
                u.Nombre_Usuario as Aprobado_Por_Nombre,
                COALESCE((SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo), 0) as Total_Pagado,
                (p.Monto_total - COALESCE((SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo), 0)) as Saldo_Pendiente
            FROM Prestamos p
            INNER JOIN Miembros m ON p.Id_miembro = m.id
            INNER JOIN Grupos g ON p.Id_grupo = g.Id_grupo
            INNER JOIN Ciclo c ON p.Id_Ciclo = c.Id_Ciclo
            INNER JOIN Usuarios u ON p.Aprobado_por = u.Id_usuario
            WHERE 1=1
        """
        params = []
        if id_grupo is not None:
            query += " AND g.Id_grupo = %s"
            params.append(id_grupo)
        elif id_distrito is not None:
            query += " AND g.distrito_id = %s"
            params.append(id_distrito)
        if ciclo_filtro != "Todos":
            # Extraer el ID del ciclo del texto seleccionado
            # Formato: "Ciclo 1 (01/01/2025 - 31/12/2025)"
            if "Ciclo " in ciclo_filtro:
                id_ciclo = int(ciclo_filtro.split("Ciclo ")[1].split(" ")[0])
                query += " AND c.Id_Ciclo = %s"
                params.append(id_ciclo)
        if grupo_filtro != "Todos" and id_grupo is None:
            query += " AND g.Nombre = %s"
            params.append(grupo_filtro)
        if estado_filtro != "Todos":
            query += " AND p.Estado = %s"
            params.append(estado_filtro)
        query += " ORDER BY p.Fecha_prestamo DESC, p.Id_prestamo DESC"
        cursor.execute(query, params)
        prestamos = cursor.fetchall()
        
        if not prestamos:
            st.info("ℹ️ No se encontraron préstamos con los filtros seleccionados")
            return
        
        # Estadísticas generales
        total_prestado = sum(p['Monto_prestado'] for p in prestamos)
        total_intereses = sum(p['Monto_interes'] for p in prestamos)
        total_a_pagar = sum(p['Monto_total'] for p in prestamos)
        total_pagado = sum(p['Total_Pagado'] for p in prestamos)
        total_pendiente = sum(p['Saldo_Pendiente'] for p in prestamos)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("📝 Total Préstamos", len(prestamos))
        with col2:
            st.metric("💵 Monto Prestado", f"${total_prestado:.2f}")
        with col3:
            st.metric("📈 Intereses", f"${total_intereses:.2f}")
        with col4:
            st.metric("💰 Total Pagado", f"${total_pagado:.2f}")
        with col5:
            st.metric("⏳ Saldo Pendiente", f"${total_pendiente:.2f}")
        
        st.divider()
        
        # Mostrar préstamos
        for prestamo in prestamos:
            with st.expander(
                f"💰 {prestamo['Nombre_Miembro']} - ${prestamo['Monto_prestado']:.2f} | "
                f"Estado: {prestamo['Estado']} | {prestamo['Fecha_prestamo'].strftime('%d/%m/%Y')}"
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**📋 Información General**")
                    st.write(f"**ID Préstamo:** {prestamo['Id_prestamo']}")
                    st.write(f"**Miembro:** {prestamo['Nombre_Miembro']}")
                    st.write(f"**Grupo:** {prestamo['Nombre_Grupo']}")
                    st.write(f"**Ciclo:** {prestamo['Nombre_ciclo']}")
                    st.write(f"**Aprobado por:** {prestamo['Aprobado_Por_Nombre']}")
                    
                    if prestamo['Descripcion']:
                        st.write(f"**Motivo:** {prestamo['Descripcion']}")
                
                with col2:
                    st.write("**💵 Información Financiera**")
                    st.write(f"**Monto Prestado:** ${prestamo['Monto_prestado']:.2f}")
                    st.write(f"**Interés ({prestamo['Interes_porcentaje']}%):** ${prestamo['Monto_interes']:.2f}")
                    st.write(f"**Total a Pagar:** ${prestamo['Monto_total']:.2f}")
                    st.write(f"**Total Pagado:** ${prestamo['Total_Pagado']:.2f}")
                    st.write(f"**Saldo Pendiente:** ${prestamo['Saldo_Pendiente']:.2f}")
                    
                    progreso = (float(prestamo['Total_Pagado']) / float(prestamo['Monto_total']) * 100) if float(prestamo['Monto_total']) > 0 else 0
                    st.progress(min(float(progreso) / 100, 1.0))
                    st.write(f"**Progreso:** {progreso:.1f}%")
                
                col3, col4 = st.columns(2)
                with col3:
                    st.write("**📅 Fechas**")
                    st.write(f"**Préstamo:** {prestamo['Fecha_prestamo'].strftime('%d/%m/%Y')}")
                    if prestamo['Fecha_vencimiento']:
                        st.write(f"**Vencimiento:** {prestamo['Fecha_vencimiento'].strftime('%d/%m/%Y')}")
                        dias_restantes = (prestamo['Fecha_vencimiento'] - datetime.now().date()).days
                        if dias_restantes < 0 and prestamo['Estado'] == 'Pendiente':
                            st.error(f"⚠️ Vencido hace {abs(dias_restantes)} días")
                        elif dias_restantes <= 7 and prestamo['Estado'] == 'Pendiente':
                            st.warning(f"⚠️ Vence en {dias_restantes} días")
                
                with col4:
                    st.write("**📊 Forma de Pago**")
                    st.write(f"**Tipo:** {prestamo['Forma_pago']}")
                    if prestamo['Numero_cuotas'] > 1:
                        st.write(f"**Cuotas:** {prestamo['Numero_cuotas']}")
                        st.write(f"**Monto por Cuota:** ${prestamo['Monto_cuota']:.2f}")
                
                # Mostrar historial de pagos
                cursor.execute("""
                    SELECT * FROM Pagos_Prestamos 
                    WHERE Id_prestamo = %s 
                    ORDER BY Fecha_pago DESC
                """, (prestamo['Id_prestamo'],))
                pagos = cursor.fetchall()
                
                if pagos:
                    st.write("**💳 Historial de Pagos**")
                    df_pagos = pd.DataFrame(pagos)
                    df_pagos['Fecha_pago'] = pd.to_datetime(df_pagos['Fecha_pago']).dt.strftime('%d/%m/%Y')
                    st.dataframe(
                        df_pagos[['Numero_cuota', 'Monto_pagado', 'Fecha_pago', 'Metodo_pago', 'Observaciones']],
                        hide_index=True,
                        use_container_width=True
                    )
    
    finally:
        cursor.close()
        conexion.close()

def registrar_pago_prestamo(id_distrito=None, id_grupo=None, solo_lectura=False):
    """Registrar pago de un préstamo"""
    st.header("💵 Registrar Pago de Préstamo")
    if solo_lectura:
        st.info("🔒 La administradora solo puede ver los préstamos y reportes. No puede registrar pagos de préstamos.")
        return
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        # Obtener préstamos pendientes (filtrados por distrito si corresponde)
        if id_distrito is not None:
            cursor.execute("""
                SELECT 
                    p.*,
                    m.nombre as Nombre_Miembro,
                    g.Nombre as Nombre_Grupo,
                    COALESCE((SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo), 0) as Total_Pagado,
                    (p.Monto_total - COALESCE((SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo), 0)) as Saldo_Pendiente
                FROM Prestamos p
                INNER JOIN Miembros m ON p.Id_miembro = m.id
                INNER JOIN Grupos g ON p.Id_grupo = g.Id_grupo
                WHERE p.Estado IN ('Pendiente', 'Vencido')
                AND g.distrito_id = %s
                ORDER BY p.Fecha_prestamo DESC
            """, (id_distrito,))
        else:
            cursor.execute("""
                SELECT 
                    p.*,
                    m.nombre as Nombre_Miembro,
                    g.Nombre as Nombre_Grupo,
                    COALESCE((SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo), 0) as Total_Pagado,
                    (p.Monto_total - COALESCE((SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo), 0)) as Saldo_Pendiente
                FROM Prestamos p
                INNER JOIN Miembros m ON p.Id_miembro = m.id
                INNER JOIN Grupos g ON p.Id_grupo = g.Id_grupo
                WHERE p.Estado IN ('Pendiente', 'Vencido')
                ORDER BY p.Fecha_prestamo DESC
            """)
        prestamos_pendientes = cursor.fetchall()
        
        if not prestamos_pendientes:
            st.info("ℹ️ No hay préstamos pendientes de pago")
            return
        
        # Seleccionar préstamo
        prestamo_opciones = {
            f"{p['Nombre_Miembro']} - {p['Nombre_Grupo']} - ${p['Saldo_Pendiente']:.2f} pendiente (ID: {p['Id_prestamo']})": p['Id_prestamo']
            for p in prestamos_pendientes
        }
        
        prestamo_seleccionado = st.selectbox("Selecciona el Préstamo", options=list(prestamo_opciones.keys()))
        id_prestamo = prestamo_opciones[prestamo_seleccionado]
        
        # Obtener detalles del préstamo
        prestamo = next(p for p in prestamos_pendientes if p['Id_prestamo'] == id_prestamo)

        # Calcular mora automática como porcentaje semanal configurable por grupo
        mora_valor = 0.0
        if prestamo['Id_grupo']:
            cursor.execute("SELECT mora_valor FROM Grupos WHERE Id_grupo = %s", (prestamo['Id_grupo'],))
            grupo = cursor.fetchone()
            if grupo and grupo['mora_valor'] is not None:
                mora_valor = float(grupo['mora_valor'])

        mora = 0.0
        dias_vencido = 0
        semanas_vencidas = 0
        fecha_pago_preview = datetime.now().date()
        if 'fecha_pago' in locals():
            if isinstance(fecha_pago, datetime):
                fecha_pago_preview = fecha_pago.date()
            else:
                fecha_pago_preview = fecha_pago
        saldo_pendiente = float(prestamo['Saldo_Pendiente'])
        if prestamo['Fecha_vencimiento'] and prestamo['Estado'] in ('Pendiente', 'Vencido'):
            dias_vencido = (prestamo['Fecha_vencimiento'] - fecha_pago_preview).days
            if dias_vencido < 0:
                semanas_vencidas = abs(dias_vencido) // 7 + (1 if abs(dias_vencido) % 7 > 0 else 0)
                mora = saldo_pendiente * (mora_valor / 100) * semanas_vencidas

        total_con_mora = saldo_pendiente + mora

        st.divider()

        # Información del préstamo
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Total a Pagar", f"${prestamo['Monto_total']:.2f}")
        with col2:
            st.metric("✅ Total Pagado", f"${prestamo['Total_Pagado']:.2f}")
        with col3:
            st.metric("⏳ Saldo Pendiente", f"${prestamo['Saldo_Pendiente']:.2f}")
        with col4:
            if prestamo['Numero_cuotas'] > 1:
                cursor.execute("""
                    SELECT COUNT(*) as cuotas_pagadas 
                    FROM Pagos_Prestamos 
                    WHERE Id_prestamo = %s
                """, (id_prestamo,))
                cuotas_pagadas = cursor.fetchone()['cuotas_pagadas']
                st.metric("📊 Cuotas", f"{cuotas_pagadas}/{prestamo['Numero_cuotas']}")

        if mora > 0:
            st.warning(f"⚠️ Este préstamo tiene pagos atrasados. Se aplican ${mora:.2f} de multa por mora.")

        st.divider()
        
        # Formulario de pago
        col1, col2 = st.columns(2)

        with col1:
            # Calcular número de cuota
            cursor.execute("""
                SELECT COALESCE(MAX(Numero_cuota), 0) + 1 as siguiente_cuota
                FROM Pagos_Prestamos
                WHERE Id_prestamo = %s
            """, (id_prestamo,))
            siguiente_cuota = cursor.fetchone()['siguiente_cuota']

            if prestamo['Numero_cuotas'] > 1:
                numero_cuota = st.number_input(
                    "Número de Cuota",
                    min_value=1,
                    max_value=prestamo['Numero_cuotas'],
                    value=min(siguiente_cuota, prestamo['Numero_cuotas']),
                    help=f"Siguiente cuota sugerida: {siguiente_cuota}"
                )
                monto_sugerido = prestamo['Monto_cuota']
            else:
                numero_cuota = 1
                st.info("**Pago Único**")
                monto_sugerido = prestamo['Saldo_Pendiente']

            if mora > 0:
                label_pago = f"Monto del Pago con mora (${float(monto_sugerido) + float(mora):.2f})"
            else:
                label_pago = f"Monto del Pago (${float(monto_sugerido):.2f})"
            monto_pago = st.number_input(
                label_pago,
                min_value=0.01,
                max_value=float(total_con_mora),
                value=min(float(monto_sugerido) + float(mora), float(total_con_mora)),
                step=0.50,
                key=f"monto_pago_{id_prestamo}_{numero_cuota}"
            )

        with col2:
            fecha_pago = st.date_input(
                "Fecha del Pago",
                value=datetime.now()
            )

            metodo_pago = st.selectbox(
                "Método de Pago",
                options=["Efectivo", "Transferencia", "Descuento_Ahorro"],
                help="Forma en que se recibe el pago"
            )

        # --- Recalcular mora y total a pagar según la fecha seleccionada ---
        mora = 0.0
        dias_vencido = 0
        semanas_vencidas = 0
        fecha_pago_preview = fecha_pago.date() if isinstance(fecha_pago, datetime) else fecha_pago
        saldo_pendiente = float(prestamo['Saldo_Pendiente'])
        if prestamo['Fecha_vencimiento'] and prestamo['Estado'] in ('Pendiente', 'Vencido'):
            dias_vencido = (prestamo['Fecha_vencimiento'] - fecha_pago_preview).days
            if dias_vencido < 0:
                semanas_vencidas = abs(dias_vencido) // 7 + (1 if abs(dias_vencido) % 7 > 0 else 0)
                mora = saldo_pendiente * (mora_valor / 100) * semanas_vencidas
        total_con_mora = saldo_pendiente + mora

        # Actualizar label y valor sugerido
        if mora > 0:
            label_pago = f"Monto del Pago con mora (${float(monto_sugerido) + float(mora):.2f})"
        else:
            label_pago = f"Monto del Pago (${float(monto_sugerido):.2f})"
        monto_pago = st.number_input(
            label_pago,
            min_value=0.01,
            max_value=float(total_con_mora),
            value=min(float(monto_sugerido) + float(mora), float(total_con_mora)),
            step=0.50,
            key=f"monto_pago_{id_prestamo}_{numero_cuota}_preview"
        )

        observaciones = st.text_area(
            "Observaciones",
            placeholder="Notas adicionales sobre el pago (opcional)"
        )

        # Validación
        if monto_pago > total_con_mora:
            st.error(f"❌ El monto del pago (${monto_pago:.2f}) no puede ser mayor al saldo pendiente + mora (${total_con_mora:.2f})")
            return

        # Calcular nuevo saldo (convertir ambos a float)
        nuevo_saldo = float(total_con_mora) - float(monto_pago)

        col1, col2 = st.columns(2)
        with col1:
            st.info(f"💵 **Monto a Pagar (incluye mora si aplica):** ${float(monto_pago):.2f}")
        with col2:
            st.info(f"⏳ **Nuevo Saldo:** ${nuevo_saldo:.2f}")

        if nuevo_saldo == 0:
            st.success("✅ Este pago liquidará completamente el préstamo y la mora")

        st.divider()

        # Botón de registro
        if st.button("💳 Registrar Pago", type="primary", use_container_width=True):
            try:
                usuario_id = st.session_state.usuario['Id_usuario']

                # Insertar pago
                cursor.execute("""
                    INSERT INTO Pagos_Prestamos 
                    (Id_prestamo, Numero_cuota, Monto_pagado, Fecha_pago, Metodo_pago, Observaciones, Registrado_por)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (id_prestamo, numero_cuota, monto_pago, fecha_pago, metodo_pago, observaciones, usuario_id))

                # Actualizar estado del préstamo si está completamente pagado
                if nuevo_saldo == 0:
                    cursor.execute("""
                        UPDATE Prestamos 
                        SET Estado = 'Pagado'
                        WHERE Id_prestamo = %s
                    """, (id_prestamo,))

                conexion.commit()
                st.success(f"✅ Pago registrado exitosamente")

                if nuevo_saldo == 0:
                    st.balloons()
                    st.success(f"🎉 ¡Préstamo completamente pagado!")
                else:
                    st.info(f"💡 Saldo restante: **${nuevo_saldo:.2f}**")

                st.rerun()

            except Exception as e:
                conexion.rollback()
                st.error(f"❌ Error al registrar el pago: {str(e)}")

    finally:
        cursor.close()
        conexion.close()

def reportes_prestamos(id_distrito=None, id_grupo=None):
    """Reportes y estadísticas de préstamos"""
    st.header("📊 Reportes de Préstamos")
    
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Estadísticas generales (filtradas por distrito si corresponde)
        if id_distrito is not None:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_prestamos,
                    SUM(Monto_prestado) as total_prestado,
                    SUM(Monto_interes) as total_intereses,
                    SUM(Monto_total) as total_a_cobrar,
                    COALESCE(SUM(
                        (SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo)
                    ), 0) as total_pagado,
                    SUM(CASE WHEN Estado = 'Pendiente' THEN 1 ELSE 0 END) as prestamos_pendientes,
                    SUM(CASE WHEN Estado = 'Pagado' THEN 1 ELSE 0 END) as prestamos_pagados,
                    SUM(CASE WHEN Estado = 'Vencido' THEN 1 ELSE 0 END) as prestamos_vencidos
                FROM Prestamos p
                INNER JOIN Grupos g ON p.Id_grupo = g.Id_grupo
                WHERE g.distrito_id = %s
            """, (id_distrito,))
        else:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_prestamos,
                    SUM(Monto_prestado) as total_prestado,
                    SUM(Monto_interes) as total_intereses,
                    SUM(Monto_total) as total_a_cobrar,
                    COALESCE(SUM(
                        (SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo)
                    ), 0) as total_pagado,
                    SUM(CASE WHEN Estado = 'Pendiente' THEN 1 ELSE 0 END) as prestamos_pendientes,
                    SUM(CASE WHEN Estado = 'Pagado' THEN 1 ELSE 0 END) as prestamos_pagados,
                    SUM(CASE WHEN Estado = 'Vencido' THEN 1 ELSE 0 END) as prestamos_vencidos
                FROM Prestamos p
            """)
        stats = cursor.fetchone()
        
        if stats['total_prestamos'] == 0:
            st.info("ℹ️ No hay préstamos registrados aún")
            return
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📝 Total Préstamos", stats['total_prestamos'])
        with col2:
            st.metric("💵 Total Prestado", f"${stats['total_prestado']:.2f}")
        with col3:
            st.metric("📈 Total Intereses", f"${stats['total_intereses']:.2f}")
        with col4:
            tasa_recuperacion = (stats['total_pagado'] / stats['total_a_cobrar'] * 100) if stats['total_a_cobrar'] > 0 else 0
            st.metric("💰 Tasa Recuperación", f"{tasa_recuperacion:.1f}%")
        
        col5, col6, col7 = st.columns(3)
        with col5:
            st.metric("✅ Pagados", stats['prestamos_pagados'], delta="Completos")
        with col6:
            st.metric("⏳ Pendientes", stats['prestamos_pendientes'], delta="Activos")
        with col7:
            st.metric("⚠️ Vencidos", stats['prestamos_vencidos'], delta="Mora")
        
        st.divider()
        
        # Préstamos por miembro
        st.subheader("👥 Préstamos por Miembro")
        if id_distrito is not None:
            cursor.execute("""
                SELECT 
                    m.nombre as Miembro,
                    g.Nombre as Grupo,
                    COUNT(p.Id_prestamo) as Total_Prestamos,
                    SUM(p.Monto_prestado) as Total_Prestado,
                    SUM(p.Monto_total) as Total_Debe,
                    COALESCE(SUM(
                        (SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo)
                    ), 0) as Total_Pagado,
                    SUM(p.Monto_total) - COALESCE(SUM(
                        (SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo)
                    ), 0) as Saldo_Pendiente
                FROM Prestamos p
                INNER JOIN Miembros m ON p.Id_miembro = m.id
                INNER JOIN Grupos g ON p.Id_grupo = g.Id_grupo
                WHERE g.distrito_id = %s
                GROUP BY m.id, m.nombre, g.Nombre
                ORDER BY Saldo_Pendiente DESC
            """, (id_distrito,))
        else:
            cursor.execute("""
                SELECT 
                    m.nombre as Miembro,
                    g.Nombre as Grupo,
                    COUNT(p.Id_prestamo) as Total_Prestamos,
                    SUM(p.Monto_prestado) as Total_Prestado,
                    SUM(p.Monto_total) as Total_Debe,
                    COALESCE(SUM(
                        (SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo)
                    ), 0) as Total_Pagado,
                    SUM(p.Monto_total) - COALESCE(SUM(
                        (SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo)
                    ), 0) as Saldo_Pendiente
                FROM Prestamos p
                INNER JOIN Miembros m ON p.Id_miembro = m.id
                INNER JOIN Grupos g ON p.Id_grupo = g.Id_grupo
                GROUP BY m.id, m.nombre, g.Nombre
                ORDER BY Saldo_Pendiente DESC
            """)
        prestamos_miembros = cursor.fetchall()
        
        if prestamos_miembros:
            df_miembros = pd.DataFrame(prestamos_miembros)
            st.dataframe(df_miembros, hide_index=True, use_container_width=True)
        
        st.divider()
        
        # Préstamos por grupo
        st.subheader("🏢 Préstamos por Grupo")
        if id_distrito is not None:
            cursor.execute("""
                SELECT 
                    g.Nombre as Grupo,
                    COUNT(p.Id_prestamo) as Total_Prestamos,
                    SUM(p.Monto_prestado) as Total_Prestado,
                    SUM(p.Monto_interes) as Total_Intereses,
                    COALESCE(SUM(
                        (SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo)
                    ), 0) as Total_Recuperado,
                    SUM(p.Monto_total) - COALESCE(SUM(
                        (SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo)
                    ), 0) as Saldo_Pendiente
                FROM Prestamos p
                INNER JOIN Grupos g ON p.Id_grupo = g.Id_grupo
                WHERE g.distrito_id = %s
                GROUP BY g.Id_grupo, g.Nombre
                ORDER BY Total_Prestado DESC
            """, (id_distrito,))
        else:
            cursor.execute("""
                SELECT 
                    g.Nombre as Grupo,
                    COUNT(p.Id_prestamo) as Total_Prestamos,
                    SUM(p.Monto_prestado) as Total_Prestado,
                    SUM(p.Monto_interes) as Total_Intereses,
                    COALESCE(SUM(
                        (SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo)
                    ), 0) as Total_Recuperado,
                    SUM(p.Monto_total) - COALESCE(SUM(
                        (SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo)
                    ), 0) as Saldo_Pendiente
                FROM Prestamos p
                INNER JOIN Grupos g ON p.Id_grupo = g.Id_grupo
                GROUP BY g.Id_grupo, g.Nombre
                ORDER BY Total_Prestado DESC
            """)
        prestamos_grupos = cursor.fetchall()
        
        if prestamos_grupos:
            df_grupos = pd.DataFrame(prestamos_grupos)
            st.dataframe(df_grupos, hide_index=True, use_container_width=True)
        
    finally:
        cursor.close()
        conexion.close()

def configurar_prestamos(id_distrito=None, id_grupo=None, solo_lectura=False):
    # --- Configuración editable de mora por grupo ---
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        if id_grupo:
            cursor.execute("SELECT mora_valor FROM Grupos WHERE Id_grupo = %s", (id_grupo,))
            mora_config = cursor.fetchone()
        else:
            mora_config = None
    finally:
        cursor.close()
        conexion.close()

    st.header("⚙️ Configuración de Préstamos")
    st.info("🔧 Esta sección permite configurar las políticas de préstamos del sistema")
    st.subheader("📋 Reglas Actuales")
    st.write("""
    ### 🎯 Políticas de Préstamos

    1. **Monto Máximo de Préstamo:**
        - Los miembros solo pueden pedir prestado hasta el monto que tienen ahorrado
        - El sistema verifica automáticamente el saldo disponible
        - Se descuentan los préstamos activos del saldo disponible

    2. **Requisitos:**
        - Tener ahorros activos en el ciclo actual
        - No tener préstamos vencidos sin pagar
        - El monto del préstamo no puede exceder el ahorro disponible

    3. **Tasas de Interés:**
        - Configurable por préstamo
        - Se calcula sobre el monto prestado
        - El interés se suma al total a pagar

    4. **Formas de Pago:**
        - **Pago Único:** Un solo pago al vencimiento
        - **Cuotas:** Pagos distribuidos en varias cuotas

    5. **Estados de Préstamos:**
        - **Pendiente:** Préstamo activo con saldo por pagar
        - **Pagado:** Préstamo completamente liquidado
        - **Vencido:** Préstamo con fecha de vencimiento pasada
    """)
    st.divider()
    st.subheader("⚡ Configuración de Mora por Grupo")
    from modulos.solo_lectura import es_administradora
    solo_lectura = es_administradora()
    mora_valor = st.number_input(
        "Porcentaje de mora semanal (%)",
        min_value=0.0,
        value=float(mora_config['mora_valor']) if mora_config and mora_config['mora_valor'] is not None else 2.0,
        step=0.1,
        help="Porcentaje semanal que se aplicará como multa sobre el saldo pendiente por cada semana de atraso",
        disabled=solo_lectura
    )
    if st.button("Guardar configuración de mora", use_container_width=True, disabled=solo_lectura):
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                "UPDATE Grupos SET mora_valor = %s WHERE Id_grupo = %s",
                (mora_valor, id_grupo)
            )
            conexion.commit()
            st.success("Configuración de mora guardada correctamente.")
        except Exception as e:
            conexion.rollback()
            st.error(f"Error al guardar configuración: {e}")
        finally:
            cursor.close()
            conexion.close()
