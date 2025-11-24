import pandas as pd

def obtener_datos_caja(id_grupo):
    from modulos.config.conexion import obtener_conexion
    conexion = obtener_conexion()
    if not conexion:
        return None
    cursor = conexion.cursor(dictionary=True)
    # Resumen de caja por grupo
    cursor.execute('''
        SELECT 'Ahorros' as Tipo, COALESCE(SUM(Monto),0) as Monto FROM Ahorros WHERE Id_grupo = %s
        UNION ALL
        SELECT 'Multas', COALESCE(SUM(Monto),0) FROM Multas WHERE Id_grupo = %s
        UNION ALL
        SELECT 'Rifas', COALESCE(SUM(monto),0) FROM Rifas WHERE grupo_id = %s
        UNION ALL
        SELECT 'Préstamos', COALESCE(SUM(Monto_prestado),0) FROM Prestamos WHERE Id_grupo = %s
    ''', (id_grupo, id_grupo, id_grupo, id_grupo))
    rows = cursor.fetchall()
    conexion.close()
    if rows:
        return pd.DataFrame(rows)
    return None
import streamlit as st
from modulos.solo_lectura import es_administradora
from modulos.config.conexion import obtener_conexion
import pandas as pd

def gestionar_caja(id_distrito=None, id_grupo=None):
    # Solo lectura para administradora
    solo_lectura = es_administradora()
    if id_grupo is not None:
        st.title("🗃️ Caja de Ahorros por Grupo")
    else:
        st.title("🗃️ Caja de Ahorros por Distrito")
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    cursor = conexion.cursor(dictionary=True)
    # Obtener todos los grupos con su distrito, filtrando por grupo, distrito o todos
    if id_grupo is not None:
        cursor.execute("""
            SELECT g.Id_grupo, g.Nombre as nombre_grupo, g.distrito_id, d.nombre_distrito
            FROM Grupos g
            LEFT JOIN Distrito d ON g.distrito_id = d.distrito_id
            WHERE g.Id_grupo = %s
            ORDER BY d.nombre_distrito, g.Nombre
        """, (id_grupo,))
    elif id_distrito is not None:
        cursor.execute("""
            SELECT g.Id_grupo, g.Nombre as nombre_grupo, g.distrito_id, d.nombre_distrito
            FROM Grupos g
            LEFT JOIN Distrito d ON g.distrito_id = d.distrito_id
            WHERE g.distrito_id = %s
            ORDER BY d.nombre_distrito, g.Nombre
        """, (id_distrito,))
    else:
        cursor.execute("""
            SELECT g.Id_grupo, g.Nombre as nombre_grupo, g.distrito_id, d.nombre_distrito
            FROM Grupos g
            LEFT JOIN Distrito d ON g.distrito_id = d.distrito_id
            ORDER BY d.nombre_distrito, g.Nombre
        """)
    grupos = cursor.fetchall()
    if not grupos:
        st.info("No hay grupos registrados.")
        conexion.close()
        return
    # Agrupar grupos por distrito
    distritos = {}
    for grupo in grupos:
        distrito = grupo['nombre_distrito'] or 'Sin distrito'
        if distrito not in distritos:
            distritos[distrito] = []
        distritos[distrito].append(grupo)

    # Si solo hay un grupo (directiva), mostrar solo ese grupo y distrito
    if id_grupo is not None and len(grupos) == 1:
        distrito_sel = list(distritos.keys())[0]
        grupo = grupos[0]
        grupo_id = grupo['Id_grupo']
        grupo_nombre = grupo['nombre_grupo']
        st.header(f"Caja de Grupo_{grupo_id}")
        # Mostrar el expander igual que la promotora, aunque solo haya un grupo
        with st.expander(f"🔍 Grupo: {grupo_nombre}", expanded=True):
            # Total ahorrado
            cursor.execute("SELECT SUM(Monto) as total_ahorrado FROM Ahorros WHERE Id_grupo = %s", (grupo_id,))
            total_ahorrado = cursor.fetchone()['total_ahorrado'] or 0
            # Total multas
            cursor.execute("SELECT SUM(Monto) as total_multas FROM Multas WHERE Id_grupo = %s AND Estado_pago = 'Pagada'", (grupo_id,))
            total_multas = cursor.fetchone()['total_multas'] or 0
            # Total rifas
            cursor.execute("SELECT SUM(monto) as total_rifas FROM Rifas WHERE grupo_id = %s", (grupo_id,))
            total_rifas = cursor.fetchone()['total_rifas'] or 0
            # Total intereses realmente pagados (proporcional a pagos realizados)
            cursor.execute("""
                SELECT COALESCE(SUM((pp.Monto_pagado / p.Monto_total) * p.Monto_interes), 0) as total_intereses
                FROM Pagos_Prestamos pp
                INNER JOIN Prestamos p ON pp.Id_prestamo = p.Id_prestamo
                WHERE p.Id_grupo = %s
            """, (grupo_id,))
            total_intereses = cursor.fetchone()['total_intereses'] or 0
            # Total mora recaudada
            cursor.execute("""
                SELECT COALESCE(SUM(pp.Monto_pagado - LEAST(pp.Monto_pagado, (p.Monto_total - COALESCE((SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo AND Id_pago < pp.Id_pago), 0)))), 0) as total_mora
                FROM Pagos_Prestamos pp
                INNER JOIN Prestamos p ON pp.Id_prestamo = p.Id_prestamo
                WHERE p.Id_grupo = %s
            """, (grupo_id,))
            total_mora = cursor.fetchone()['total_mora'] or 0
            # Calcular préstamos activos (capital no pagado)
            cursor.execute("""
                SELECT COALESCE(SUM(p.Monto_total - COALESCE((SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo), 0)), 0) as prestamos_activos
                FROM Prestamos p
                WHERE p.Id_grupo = %s AND p.Estado IN ('Pendiente', 'Vencido')
            """, (grupo_id,))
            prestamos_activos = cursor.fetchone()['prestamos_activos'] or 0
            # Fondo común = ahorros + multas + rifas + intereses + mora - préstamos activos
            fondo_comun = (total_ahorrado or 0) + (total_multas or 0) + (total_rifas or 0) + (total_intereses or 0) + (total_mora or 0) - (prestamos_activos or 0)
            st.metric("💰 Fondo Común", f"${fondo_comun:.2f}")
            st.metric("💳 Préstamos Activos (por cobrar)", f"-${prestamos_activos:.2f}")
            st.metric("💵 Ahorros", f"${total_ahorrado:.2f}")
            st.metric("💸 Multas Pagadas", f"${total_multas:.2f}")
            st.metric("🎟️ Rifas", f"${total_rifas:.2f}")
            st.metric("⚡ Mora Recaudada", f"${total_mora:.2f}")
            # Reparto proporcional de multas y rifas según ahorro acumulado
            cursor.execute("SELECT id, nombre FROM Miembros WHERE grupo_id = %s", (grupo_id,))
            miembros = cursor.fetchall()
            n_miembros = len(miembros)
            total_repartir = (total_multas or 0) + (total_rifas or 0) + (total_intereses or 0) + (total_mora or 0)
            st.markdown("---")
            st.markdown(f"### 📦 Resumen de Caja del Grupo **{grupo_nombre}**")
            st.markdown(f"<div style='margin-bottom: 10px;'><b>Fondo Común:</b> <span style='color:#2E8B57;font-size:1.2em;'>${fondo_comun:.2f}</span></div>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Ahorros", f"${total_ahorrado:.2f}")
            col2.metric("Multas (pagadas)", f"${total_multas:.2f}")
            col3.metric("Rifas", f"${total_rifas:.2f}")
            col4.metric("Intereses Préstamos", f"${total_intereses:.2f}")
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            st.markdown(f"<b>Mora recaudada:</b> <span style='color:#FF8C00;'>${total_mora:.2f}</span>", unsafe_allow_html=True)
            st.markdown(f"<b>Total a repartir (multas + rifas + intereses + mora):</b> <span style='color:#1E90FF;'>${total_repartir:.2f}</span>", unsafe_allow_html=True)
            st.markdown(
                "<span style='font-size:1em;'>El total recaudado por <b>multas</b>, <b>rifas</b>, <b>intereses de préstamos</b> y <b>moras</b> se reparte <b>proporcionalmente al ahorro acumulado</b> de cada miembro.</span>",
                unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
            st.markdown(f"Miembros en el grupo: {n_miembros}")
            if n_miembros > 0:
                # Obtener ahorro individual de cada miembro
                ahorros_dict = {}
                cursor.execute("SELECT Id_miembro, SUM(Monto) as ahorro FROM Ahorros WHERE Id_grupo = %s GROUP BY Id_miembro", (grupo_id,))
                for row in cursor.fetchall():
                    ahorros_dict[row['Id_miembro']] = row['ahorro'] or 0
                suma_ahorros = sum(ahorros_dict.values())
                detalle_reparto = []
                for m in miembros:
                    ahorro = ahorros_dict.get(m['id'], 0)
                    if suma_ahorros > 0:
                        proporcion = ahorro / suma_ahorros
                    else:
                        proporcion = 0
                    monto_reparto = total_repartir * proporcion
                    total_recibido = ahorro + monto_reparto
                    detalle_reparto.append({
                        "Miembro": m['nombre'],
                        "Ahorro": f"${ahorro:.2f}",
                        "% del ahorro": f"{proporcion*100:.1f}%" if suma_ahorros > 0 else "0%",
                        "Multas+Rifas+InterésPréstamos+Mora": f"${monto_reparto:.2f}",
                        "Total Recibido": total_recibido
                    })
                df_reparto = pd.DataFrame(detalle_reparto)
                st.markdown("#### Tabla de Repartición Proporcional por Miembro")
                st.dataframe(df_reparto.rename(columns={"Total Recibido": "Total Recibido ($)"}), hide_index=True)
                # Diagrama de pastel con leyenda a un costado (solo leyenda, sin etiquetas ni porcentajes sobre el gráfico)
                import matplotlib.pyplot as plt
                st.markdown("#### Diagrama de Pastel: Distribución del Dinero entre Miembros")
                valores = df_reparto['Total Recibido'].astype(float).values
                labels = df_reparto['Miembro'].tolist()
                if len(valores) > 0 and valores.sum() > 0:
                    fig, ax = plt.subplots(figsize=(6, 6))
                    wedges, _ = ax.pie(
                        valores,
                        labels=None,  # No mostrar etiquetas directamente
                        startangle=90,
                        radius=1.1
                    )
                    # Calcular porcentajes manualmente
                    total = valores.sum()
                    porcentajes = [(v / total) * 100 if total > 0 else 0 for v in valores]
                    legend_labels = [f"{label} ({porc:.1f}%)" for label, porc in zip(labels, porcentajes)]
                    # Añadir leyenda con nombres, porcentajes y colores
                    ax.legend(wedges, legend_labels, title="Miembro", loc="center left", bbox_to_anchor=(1, 0.5))
                    ax.set_title('Distribución del dinero a recibir por miembro')
                    st.pyplot(fig)
                else:
                    st.info('No hay datos suficientes para mostrar el diagrama de pastel.')
        conexion.close()
        return
    # Si hay filtro de distrito, seleccionar automáticamente
    if id_distrito is not None and len(distritos) == 1:
        distrito_sel = list(distritos.keys())[0]
    else:
        distrito_sel = st.selectbox("Selecciona un distrito", list(distritos.keys()), key="distrito_caja")
    st.header(f"Resumen de Caja - {distrito_sel}")
    for grupo in distritos[distrito_sel]:
        grupo_id = grupo['Id_grupo']
        grupo_nombre = grupo['nombre_grupo']
        with st.expander(f"🔍 Grupo: {grupo_nombre}", expanded=False):
            # Total ahorrado
            cursor.execute("SELECT SUM(Monto) as total_ahorrado FROM Ahorros WHERE Id_grupo = %s", (grupo_id,))
            total_ahorrado = cursor.fetchone()['total_ahorrado'] or 0
            # Total multas
            cursor.execute("SELECT SUM(Monto) as total_multas FROM Multas WHERE Id_grupo = %s AND Estado_pago = 'Pagada'", (grupo_id,))
            total_multas = cursor.fetchone()['total_multas'] or 0
            # Total rifas
            cursor.execute("SELECT SUM(monto) as total_rifas FROM Rifas WHERE grupo_id = %s", (grupo_id,))
            total_rifas = cursor.fetchone()['total_rifas'] or 0
            # Total intereses realmente pagados (proporcional a pagos realizados)
            cursor.execute("""
                SELECT COALESCE(SUM((pp.Monto_pagado / p.Monto_total) * p.Monto_interes), 0) as total_intereses
                FROM Pagos_Prestamos pp
                INNER JOIN Prestamos p ON pp.Id_prestamo = p.Id_prestamo
                WHERE p.Id_grupo = %s
            """, (grupo_id,))
            total_intereses = cursor.fetchone()['total_intereses'] or 0
            # Total mora recaudada
            cursor.execute("""
                SELECT COALESCE(SUM(pp.Monto_pagado - LEAST(pp.Monto_pagado, (p.Monto_total - COALESCE((SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo AND Id_pago < pp.Id_pago), 0)))), 0) as total_mora
                FROM Pagos_Prestamos pp
                INNER JOIN Prestamos p ON pp.Id_prestamo = p.Id_prestamo
                WHERE p.Id_grupo = %s
            """, (grupo_id,))
            total_mora = cursor.fetchone()['total_mora'] or 0
            # Calcular préstamos activos (capital no pagado)
            cursor.execute("""
                SELECT COALESCE(SUM(p.Monto_total - COALESCE((SELECT SUM(Monto_pagado) FROM Pagos_Prestamos WHERE Id_prestamo = p.Id_prestamo), 0)), 0) as prestamos_activos
                FROM Prestamos p
                WHERE p.Id_grupo = %s AND p.Estado IN ('Pendiente', 'Vencido')
            """, (grupo_id,))
            prestamos_activos = cursor.fetchone()['prestamos_activos'] or 0
            # Fondo común = ahorros + multas + rifas + intereses + mora - préstamos activos
            fondo_comun = (total_ahorrado or 0) + (total_multas or 0) + (total_rifas or 0) + (total_intereses or 0) + (total_mora or 0) - (prestamos_activos or 0)
            st.metric("💰 Fondo Común", f"${fondo_comun:.2f}")
            st.metric("💳 Préstamos Activos (por cobrar)", f"-${prestamos_activos:.2f}")
            st.metric("💵 Ahorros", f"${total_ahorrado:.2f}")
            st.metric("💸 Multas Pagadas", f"${total_multas:.2f}")
            st.metric("🎟️ Rifas", f"${total_rifas:.2f}")
            st.metric("⚡ Mora Recaudada", f"${total_mora:.2f}")
            # Reparto proporcional de multas, rifas, intereses y mora según ahorro acumulado
            cursor.execute("SELECT id, nombre FROM Miembros WHERE grupo_id = %s", (grupo_id,))
            miembros = cursor.fetchall()
            n_miembros = len(miembros)
            total_repartir = (total_multas or 0) + (total_rifas or 0) + (total_intereses or 0) + (total_mora or 0)
            st.markdown("---")
            st.markdown(f"### 📦 Resumen de Caja del Grupo **{grupo_nombre}**")
            st.markdown(
                f"<div style='margin-bottom: 10px;'><b>Fondo Común:</b> <span style='color:#2E8B57;font-size:1.2em;'>${fondo_comun:.2f}</span></div>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Ahorros", f"${total_ahorrado:.2f}")
            col2.metric("Multas (pagadas)", f"${total_multas:.2f}")
            col3.metric("Rifas", f"${total_rifas:.2f}")
            col4.metric("Intereses Préstamos", f"${total_intereses:.2f}")
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            st.markdown(f"<b>Mora recaudada:</b> <span style='color:#FF8C00;'>${total_mora:.2f}</span>", unsafe_allow_html=True)
            st.markdown(f"<b>Total a repartir (multas + rifas + intereses + mora):</b> <span style='color:#1E90FF;'>${total_repartir:.2f}</span>", unsafe_allow_html=True)
            st.markdown(
                "<span style='font-size:1em;'>El total recaudado por <b>multas</b>, <b>rifas</b>, <b>intereses de préstamos</b> y <b>moras</b> se reparte <b>proporcionalmente al ahorro acumulado</b> de cada miembro.</span>",
                unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
            st.markdown(f"Miembros en el grupo: {n_miembros}")
            if n_miembros > 0:
                # Obtener ahorro individual de cada miembro
                ahorros_dict = {}
                cursor.execute("SELECT Id_miembro, SUM(Monto) as ahorro FROM Ahorros WHERE Id_grupo = %s GROUP BY Id_miembro", (grupo_id,))
                for row in cursor.fetchall():
                    ahorros_dict[row['Id_miembro']] = row['ahorro'] or 0
                suma_ahorros = sum(ahorros_dict.values())
                detalle_reparto = []
                if n_miembros > 0:
                    # Obtener ahorro individual de cada miembro
                    ahorros_dict = {}
                    cursor.execute("SELECT Id_miembro, SUM(Monto) as ahorro FROM Ahorros WHERE Id_grupo = %s GROUP BY Id_miembro", (grupo_id,))
                    for row in cursor.fetchall():
                        ahorros_dict[row['Id_miembro']] = row['ahorro'] or 0
                    suma_ahorros = sum(ahorros_dict.values())
                    detalle_reparto = []
                    for m in miembros:
                        ahorro = ahorros_dict.get(m['id'], 0)
                        if suma_ahorros > 0:
                            proporcion = ahorro / suma_ahorros
                        else:
                            proporcion = 0
                        monto_reparto = total_repartir * proporcion
                        total_recibido = ahorro + monto_reparto
                        detalle_reparto.append({
                            "Miembro": m['nombre'],
                            "Ahorro": f"${ahorro:.2f}",
                            "% del ahorro": f"{proporcion*100:.1f}%" if suma_ahorros > 0 else "0%",
                            "Multas+Rifas+InterésPréstamos+Mora": f"${monto_reparto:.2f}",
                            "Total Recibido": total_recibido
                        })
                    df_reparto = pd.DataFrame(detalle_reparto)
                    st.markdown("#### Tabla de Repartición Proporcional por Miembro")
                    st.dataframe(df_reparto.rename(columns={"Total Recibido": "Total Recibido ($)"}), use_container_width=True, hide_index=True)
                    # Diagrama de pastel dentro del expander de cada grupo
                    import matplotlib.pyplot as plt
                    st.markdown("#### Diagrama de Pastel: Distribución del Dinero entre Miembros")
                    valores = df_reparto['Total Recibido'].astype(float).values
                    labels = df_reparto['Miembro'].tolist()
                    if len(valores) > 0 and valores.sum() > 0:
                        fig, ax = plt.subplots(figsize=(6, 6))
                        wedges, _ = ax.pie(
                            valores,
                            labels=None,  # No mostrar etiquetas directamente
                            startangle=90,
                            radius=1.1
                        )
                        # Calcular porcentajes manualmente
                        total = valores.sum()
                        porcentajes = [(v / total) * 100 if total > 0 else 0 for v in valores]
                        legend_labels = [f"{label} ({porc:.1f}%)" for label, porc in zip(labels, porcentajes)]
                        # Añadir leyenda con nombres, porcentajes y colores
                        ax.legend(wedges, legend_labels, title="Miembro", loc="center left", bbox_to_anchor=(1, 0.5))
                        ax.set_title('Distribución del dinero a recibir por miembro')
                        st.pyplot(fig)
                    else:
                        st.info('No hay datos suficientes para mostrar el diagrama de pastel.')
