
import streamlit as st
from modulos.solo_lectura import es_administradora
from modulos.config.conexion import obtener_conexion
import pandas as pd

def generar_reporte_ciclo(id_distrito=None, id_grupo=None):
    st.title("📊 Reportes y Estado del Sistema")
    # Obtener usuario de sesión
    usuario = None
    try:
        import streamlit as st2
        usuario = st2.session_state.get("usuario")
    except Exception:
        pass
    rol = (usuario.get("rol") or usuario.get("Rol") or "").strip().lower() if usuario else ""
    id_distrito_usuario = usuario.get("id_distrito") or usuario.get("Id_distrito") if usuario else None
    id_grupo_usuario = usuario.get("id_grupo") or usuario.get("Id_grupo") if usuario else None
    # Selección de grupo para descarga (solo si promotora)
    grupo_descarga = id_grupo
    if rol == "promotora" and id_distrito_usuario:
        # Permitir seleccionar grupo de su distrito
        from modulos.config.conexion import obtener_conexion
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT Id_grupo, Nombre FROM Grupos WHERE distrito_id = %s", (id_distrito_usuario,))
            grupos = cursor.fetchall()
            if grupos:
                opciones = {f"{g['Nombre']} (ID {g['Id_grupo']})": g['Id_grupo'] for g in grupos}
                nombre_sel = st.selectbox("Selecciona el grupo para descargar el reporte", list(opciones.keys()), key="grupo_reporte_descarga")
                grupo_descarga = opciones[nombre_sel]
            conexion.close()
    elif rol == "directiva" and id_grupo_usuario:
        grupo_descarga = id_grupo_usuario
    # Botón de descarga
    if st.button("Descargar reporte completo del grupo", key="descargar_reporte_grupo"):
        import io
        output = io.BytesIO()
        # Obtener todos los dataframes primero
        df_caja = obtener_reporte_caja(grupo_descarga)
        df_ahorros = obtener_reporte_completo_grupo(grupo_descarga)
        df_cartera = obtener_reporte_cartera_mora(grupo_descarga)
        df_reuniones = obtener_reporte_reuniones_actas(grupo_descarga)
        df_utilidades = obtener_reporte_utilidades(grupo_descarga)
        hojas = []
        if df_caja is not None and not df_caja.empty:
            hojas.append((df_caja, "Caja"))
        if df_ahorros is not None and not df_ahorros.empty:
            hojas.append((df_ahorros, "Ahorros y Prestamos"))
        if df_cartera is not None and not df_cartera.empty:
            hojas.append((df_cartera, "Cartera y Mora"))
        if df_reuniones is not None and not df_reuniones.empty:
            hojas.append((df_reuniones, "Reuniones y Actas"))
        if df_utilidades is not None and not df_utilidades.empty:
            hojas.append((df_utilidades, "Utilidades Ciclo"))
        if not hojas:
            st.warning("No hay datos para exportar en ninguna sección del reporte.")
        else:
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                for df, nombre in hojas:
                    df.to_excel(writer, index=False, sheet_name=nombre)
            output.seek(0)
            st.download_button(
                label="Descargar Excel",
                data=output,
                file_name=f"reporte_grupo_{grupo_descarga}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # Mostrar los reportes en pantalla como antes
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Caja (Ingresos/Egresos)",
        "Ahorros y Préstamos por Miembro",
        "Cartera y Mora",
        "Reuniones y Actas",
        "Utilidades al Cierre"
    ])

    with tab1:
        mostrar_reporte_caja(id_distrito, id_grupo)
    with tab2:
        mostrar_estado_ahorros_prestamos(id_distrito, id_grupo)
    with tab3:
        mostrar_cartera_mora(id_distrito, id_grupo)
    with tab4:
        mostrar_historial_reuniones_actas(id_distrito, id_grupo)
    with tab5:
        mostrar_resumen_utilidades(id_distrito, id_grupo)

# --- Funciones para cada hoja del reporte ---
def obtener_reporte_caja(id_grupo):
    from modulos.caja import obtener_datos_caja
    df = obtener_datos_caja(id_grupo)
    return df

def obtener_reporte_cartera_mora(id_grupo):
    from modulos.prestamos import obtener_datos_cartera_mora
    df = obtener_datos_cartera_mora(id_grupo)
    return df

def obtener_reporte_reuniones_actas(id_grupo):
    from modulos.asistencia_multas import obtener_datos_reuniones_actas
    df = obtener_datos_reuniones_actas(id_grupo)
    return df

def obtener_reporte_utilidades(id_grupo):
    from modulos.ciclos import obtener_datos_utilidades_ciclo
    df = obtener_datos_utilidades_ciclo(id_grupo)
    return df
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Caja (Ingresos/Egresos)",
        "Ahorros y Préstamos por Miembro",
        "Cartera y Mora",
        "Reuniones y Actas",
        "Utilidades al Cierre"
    ])

    with tab1:
        mostrar_reporte_caja(id_distrito, id_grupo)
    with tab2:
        mostrar_estado_ahorros_prestamos(id_distrito, id_grupo)
    with tab3:
        mostrar_cartera_mora(id_distrito, id_grupo)
    with tab4:
        mostrar_historial_reuniones_actas(id_distrito, id_grupo)
    with tab5:
        mostrar_resumen_utilidades(id_distrito, id_grupo)

def obtener_reporte_completo_grupo(id_grupo):
    # Ejemplo: unificar info de miembros, ahorros, préstamos activos, etc.
    from modulos.config.conexion import obtener_conexion
    import pandas as pd
    conexion = obtener_conexion()
    if not conexion:
        return None
    cursor = conexion.cursor(dictionary=True)
    query = '''
        SELECT m.nombre AS Miembro, g.Nombre AS Grupo, SUM(a.Monto) AS Ahorros,
            COALESCE(SUM(CASE WHEN p.Estado IN ('Pendiente', 'Vencido') THEN p.Monto_total - COALESCE((SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo), 0) ELSE 0 END), 0) AS Prestamos_Activos
        FROM Miembros m
        LEFT JOIN Grupos g ON m.grupo_id = g.Id_grupo
        LEFT JOIN Ahorros a ON m.id = a.Id_miembro
        LEFT JOIN Prestamos p ON m.id = p.Id_miembro
        WHERE g.Id_grupo = %s
        GROUP BY m.id, g.Nombre
    '''
    cursor.execute(query, (id_grupo,))
    rows = cursor.fetchall()
    conexion.close()
    if rows:
        return pd.DataFrame(rows)
    return None
# --- TAB 1: Caja (Ingresos/Egresos) ---
def mostrar_reporte_caja(id_distrito=None, id_grupo=None):
    st.header("🗃️ Reporte de Caja (Ingresos/Egresos)")
    # Solo mostrar el título de reporte de caja, no "Caja de Ahorros por Grupo"
    from modulos.caja import gestionar_caja
    gestionar_caja(id_distrito=id_distrito, id_grupo=id_grupo)

# --- TAB 2: Estado de ahorros y préstamos por miembro ---
def mostrar_estado_ahorros_prestamos(id_distrito=None, id_grupo=None):
    st.header("👥 Estado de Ahorros y Préstamos por Miembro")
    # Mostrar tabla de miembros, ahorros y préstamos activos
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ No se pudo conectar con la base de datos.")
        return
    cursor = conexion.cursor(dictionary=True)
    query = """
        SELECT m.nombre AS Miembro, g.Nombre AS Grupo, SUM(a.Monto) AS Ahorros,
            COALESCE(SUM(CASE WHEN p.Estado IN ('Pendiente', 'Vencido') THEN p.Monto_total - COALESCE((SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo), 0) ELSE 0 END), 0) AS Prestamos_Activos
        FROM Miembros m
        LEFT JOIN Grupos g ON m.grupo_id = g.Id_grupo
        LEFT JOIN Ahorros a ON m.id = a.Id_miembro
        LEFT JOIN Prestamos p ON m.id = p.Id_miembro
        WHERE 1=1
    """
    params = []
    if id_grupo:
        query += " AND g.Id_grupo = %s"
        params.append(id_grupo)
    elif id_distrito:
        query += " AND g.distrito_id = %s"
        params.append(id_distrito)
    query += " GROUP BY m.id, g.Nombre"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de miembros para mostrar.")
    conexion.close()

# --- TAB 3: Cartera de préstamos y porcentaje de mora ---
def mostrar_cartera_mora(id_distrito=None, id_grupo=None):
    st.header("💼 Cartera de Préstamos y Porcentaje de Mora")
    from modulos.prestamos import reportes_prestamos
    reportes_prestamos(id_distrito=id_distrito, id_grupo=id_grupo)

# --- TAB 4: Historial de reuniones y actas ---
def mostrar_historial_reuniones_actas(id_distrito=None, id_grupo=None):
    st.header("📅 Historial de Reuniones y Actas")
    from modulos.asistencia_multas import gestionar_reuniones
    gestionar_reuniones(id_distrito=id_distrito, id_grupo=id_grupo)

# --- TAB 5: Resumen de utilidades al cierre del ciclo ---
def mostrar_resumen_utilidades(id_distrito=None, id_grupo=None):
    st.header("📈 Resumen de Utilidades al Cierre del Ciclo")
    # Aquí se puede mostrar el resumen general del ciclo, reutilizando la lógica previa
    # (Se puede mejorar con más detalles si se requiere)
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ No se pudo conectar con la base de datos.")
        return
    cursor = conexion.cursor(dictionary=True)
    # Selección de ciclo
    if id_grupo is not None:
        cursor.execute("""
            SELECT DISTINCT c.Id_Ciclo, c.Fecha_Inicio, c.Fecha_Fin
            FROM Ciclo c
            INNER JOIN Grupos g ON g.Id_Ciclo = c.Id_Ciclo
            WHERE g.Id_grupo = %s
            ORDER BY c.Fecha_Inicio DESC
        """, (id_grupo,))
    elif id_distrito is not None:
        cursor.execute("""
            SELECT DISTINCT c.Id_Ciclo, c.Fecha_Inicio, c.Fecha_Fin
            FROM Ciclo c
            INNER JOIN Grupos g ON g.Id_Ciclo = c.Id_Ciclo
            WHERE g.distrito_id = %s
            ORDER BY c.Fecha_Inicio DESC
        """, (id_distrito,))
    else:
        cursor.execute("SELECT Id_Ciclo, Fecha_Inicio, Fecha_Fin FROM Ciclo ORDER BY Fecha_Inicio DESC")
    ciclos = cursor.fetchall()
    if not ciclos:
        st.info("No hay ciclos registrados.")
        return
    ciclos_dict = {f"{c['Id_Ciclo']} ({c['Fecha_Inicio']} a {c['Fecha_Fin']})": c['Id_Ciclo'] for c in ciclos}
    ciclo_sel = st.selectbox("Selecciona un ciclo", list(ciclos_dict.keys()), key="ciclo_utilidades")
    id_ciclo = ciclos_dict[ciclo_sel]
    # Resumen general del ciclo
    cursor.execute("SELECT COUNT(*) as total_ahorros, SUM(Monto) as total_monto FROM Ahorros WHERE Id_Ciclo = %s", (id_ciclo,))
    ahorros = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) as total_multas, SUM(Monto) as total_monto FROM Multas WHERE Id_Ciclo = %s", (id_ciclo,))
    multas = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) as total_rifas, SUM(monto) as total_monto FROM Rifas WHERE Id_Ciclo = %s", (id_ciclo,))
    rifas = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) as total_prestamos, SUM(Monto_prestado) as total_monto FROM Prestamos WHERE Id_Ciclo = %s", (id_ciclo,))
    prestamos = cursor.fetchone()
    monto_ahorros = ahorros['total_monto'] or 0
    monto_multas = multas['total_monto'] or 0
    monto_rifas = rifas['total_monto'] or 0
    monto_prestamos = prestamos['total_monto'] or 0
    monto_total_ciclo = monto_ahorros + monto_multas + monto_rifas - monto_prestamos
    resumen = pd.DataFrame([
        {"Tipo": "Ahorros", "Total": ahorros['total_ahorros'], "Monto": monto_ahorros},
        {"Tipo": "Multas", "Total": multas['total_multas'], "Monto": monto_multas},
        {"Tipo": "Rifas", "Total": rifas['total_rifas'], "Monto": monto_rifas},
        {"Tipo": "Préstamos", "Total": prestamos['total_prestamos'], "Monto": monto_prestamos},
        {"Tipo": "TOTAL CICLO (ingresos - egresos)", "Total": "-", "Monto": monto_total_ciclo}
    ])
    resumen["Monto"] = resumen["Monto"].apply(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x)
    st.subheader("Resumen General del Ciclo")
    st.dataframe(resumen, use_container_width=True, hide_index=True)
    st.metric("Monto total en el ciclo (ingresos - egresos)", f"${monto_total_ciclo:,.2f}")
    conexion.close()
