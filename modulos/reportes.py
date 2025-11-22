import streamlit as st
from modulos.config.conexion import obtener_conexion

# Reporte general de todo lo que ocurre en un ciclo

def generar_reporte_ciclo(id_distrito=None, id_grupo=None):
    st.title("📊 Reporte General de Ciclo")
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ No se pudo conectar con la base de datos.")
        return
    cursor = conexion.cursor(dictionary=True)
    # Selección de ciclo (solo ciclos del grupo, distrito o todos)
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
    ciclo_sel = st.selectbox("Selecciona un ciclo", list(ciclos_dict.keys()))
    id_ciclo = ciclos_dict[ciclo_sel]
    st.header("Resumen del Ciclo")
    # Grupos en el ciclo (filtrar por grupo, distrito o todos)
    if id_grupo is not None:
        cursor.execute("""
            SELECT g.Id_grupo, g.Nombre, g.Numero_miembros, d.nombre_distrito
            FROM Grupos g
            LEFT JOIN Distrito d ON g.distrito_id = d.distrito_id
            WHERE g.Id_Ciclo = %s AND g.Id_grupo = %s
            ORDER BY g.Nombre
        """, (id_ciclo, id_grupo))
    elif id_distrito is not None:
        cursor.execute("""
            SELECT g.Id_grupo, g.Nombre, g.Numero_miembros, d.nombre_distrito
            FROM Grupos g
            LEFT JOIN Distrito d ON g.distrito_id = d.distrito_id
            WHERE g.Id_Ciclo = %s AND g.distrito_id = %s
            ORDER BY g.Nombre
        """, (id_ciclo, id_distrito))
    else:
        cursor.execute("""
            SELECT g.Id_grupo, g.Nombre, g.Numero_miembros, d.nombre_distrito
            FROM Grupos g
            LEFT JOIN Distrito d ON g.distrito_id = d.distrito_id
            WHERE g.Id_Ciclo = %s
            ORDER BY g.Nombre
        """, (id_ciclo,))
    grupos = cursor.fetchall()
    import pandas as pd
    st.subheader("Grupos en el ciclo")
    if grupos:
        df_grupos = pd.DataFrame(grupos)
        st.dataframe(df_grupos, use_container_width=True, hide_index=True)
    else:
        st.info("No hay grupos en este ciclo.")


    # Ahorros (solo del ciclo seleccionado)
    cursor.execute("SELECT COUNT(*) as total_ahorros, SUM(Monto) as total_monto FROM Ahorros WHERE Id_Ciclo = %s", (id_ciclo,))
    ahorros = cursor.fetchone()

    # Multas (solo del ciclo seleccionado)
    cursor.execute("SELECT COUNT(*) as total_multas, SUM(Monto) as total_monto FROM Multas WHERE Id_Ciclo = %s", (id_ciclo,))
    multas = cursor.fetchone()

    # Rifas (solo del ciclo seleccionado)
    cursor.execute("SELECT COUNT(*) as total_rifas, SUM(monto) as total_monto FROM Rifas WHERE Id_Ciclo = %s", (id_ciclo,))
    rifas = cursor.fetchone()

    # Préstamos (solo del ciclo seleccionado)
    cursor.execute("SELECT COUNT(*) as total_prestamos, SUM(Monto_prestado) as total_monto FROM Prestamos WHERE Id_Ciclo = %s", (id_ciclo,))
    prestamos = cursor.fetchone()

    # Calcular monto total del ciclo: ingresos - egresos
    monto_ahorros = ahorros['total_monto'] or 0
    monto_multas = multas['total_monto'] or 0
    monto_rifas = rifas['total_monto'] or 0
    monto_prestamos = prestamos['total_monto'] or 0
    monto_total_ciclo = monto_ahorros + monto_multas + monto_rifas - monto_prestamos

    # Mostrar totales en una tabla
    resumen = pd.DataFrame([
        {
            "Tipo": "Ahorros",
            "Total": ahorros['total_ahorros'],
            "Monto": monto_ahorros
        },
        {
            "Tipo": "Multas",
            "Total": multas['total_multas'],
            "Monto": monto_multas
        },
        {
            "Tipo": "Rifas",
            "Total": rifas['total_rifas'],
            "Monto": monto_rifas
        },
        {
            "Tipo": "Préstamos",
            "Total": prestamos['total_prestamos'],
            "Monto": monto_prestamos
        },
        {
            "Tipo": "TOTAL CICLO (ingresos - egresos)",
            "Total": "-",
            "Monto": monto_total_ciclo
        }
    ])
    resumen["Monto"] = resumen["Monto"].apply(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x)
    st.subheader("Resumen General")
    st.dataframe(resumen, use_container_width=True, hide_index=True)
    st.metric("Monto total en el ciclo (ingresos - egresos)", f"${monto_total_ciclo:,.2f}")
    conexion.close()
