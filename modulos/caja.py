import streamlit as st
from modulos.config.conexion import obtener_conexion
import pandas as pd

def gestionar_caja(id_distrito=None, id_grupo=None):
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
            # Fondo común = ahorros + multas + rifas
            fondo_comun = (total_ahorrado or 0) + (total_multas or 0) + (total_rifas or 0)
            st.metric("💰 Fondo Común", f"${fondo_comun:.2f}")
            st.metric("💵 Ahorros", f"${total_ahorrado:.2f}")
            st.metric("💸 Multas Pagadas", f"${total_multas:.2f}")
            st.metric("🎟️ Rifas", f"${total_rifas:.2f}")
            # Reparto de dinero al final del ciclo
            cursor.execute("SELECT id, nombre FROM Miembros WHERE grupo_id = %s", (grupo_id,))
            miembros = cursor.fetchall()
            n_miembros = len(miembros)
            total_repartir = (total_multas or 0) + (total_rifas or 0)
            st.markdown("---")
            st.markdown(f"### 📦 Resumen de Caja del Grupo **{grupo_nombre}**")
            st.markdown(f"<div style='margin-bottom: 10px;'><b>Fondo Común:</b> <span style='color:#2E8B57;font-size:1.2em;'>${fondo_comun:.2f}</span></div>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            col1.metric("Ahorros", f"${total_ahorrado:.2f}")
            col2.metric("Multas (pagadas)", f"${total_multas:.2f}")
            col3.metric("Rifas", f"${total_rifas:.2f}")
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            st.markdown(f"<b>Total a repartir (multas + rifas):</b> <span style='color:#1E90FF;'>${total_repartir:.2f}</span>", unsafe_allow_html=True)
            st.markdown(
                "<span style='font-size:1em;'>El total recaudado por <b>multas</b> y <b>rifas</b> se reparte en partes iguales entre todos los miembros del grupo, como incentivo y beneficio colectivo.</span>",
                unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
            st.markdown(f"Miembros en el grupo: {n_miembros}")
            if n_miembros > 0:
                parte_igual = total_repartir / n_miembros
                st.success(f"Cada miembro recibe ${parte_igual:.2f} de multas y rifas, además de su ahorro individual.", icon="💸")
                # Mostrar tabla de miembros y reparto
                # Obtener ahorro individual de cada miembro
                ahorros_dict = {}
                cursor.execute("SELECT Id_miembro, SUM(Monto) as ahorro FROM Ahorros WHERE Id_grupo = %s GROUP BY Id_miembro", (grupo_id,))
                for row in cursor.fetchall():
                    ahorros_dict[row['Id_miembro']] = row['ahorro'] or 0
                df_reparto = pd.DataFrame([
                    {
                        "Miembro": m['nombre'],
                        "Ahorro": f"${ahorros_dict.get(m['id'], 0):.2f}",
                        "Multas+Rifas": f"${parte_igual:.2f}",
                        "Total Recibido": f"${ahorros_dict.get(m['id'], 0) + parte_igual:.2f}"
                    } for m in miembros
                ])
                st.markdown("#### Tabla de Repartición por Miembro")
                st.dataframe(df_reparto, hide_index=True)
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
            # Fondo común = ahorros + multas + rifas
            fondo_comun = (total_ahorrado or 0) + (total_multas or 0) + (total_rifas or 0)
            # Actualizar el fondo común en la tabla Caja si existe
            cursor.execute("UPDATE Caja SET Fondo_Comun = %s WHERE Id_caja = (SELECT Id_caja FROM Grupos WHERE Id_grupo = %s)", (fondo_comun, grupo_id))
            # Miembros
            cursor.execute("SELECT id, nombre FROM Miembros WHERE grupo_id = %s", (grupo_id,))
            miembros = cursor.fetchall()
            n_miembros = len(miembros)
            # Total a repartir
            total_repartir = (total_multas or 0) + (total_rifas or 0)
            st.markdown("---")
            st.markdown(f"### 📦 Resumen de Caja del Grupo **{grupo_nombre}**")
            st.markdown(
                f"<div style='margin-bottom: 10px;'><b>Fondo Común:</b> <span style='color:#2E8B57;font-size:1.2em;'>${fondo_comun:.2f}</span></div>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            col1.metric("Ahorros", f"${total_ahorrado:.2f}")
            col2.metric("Multas (pagadas)", f"${total_multas:.2f}")
            col3.metric("Rifas", f"${total_rifas:.2f}")
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            st.markdown(f"<b>Total a repartir (multas + rifas):</b> <span style='color:#1E90FF;'>${total_repartir:.2f}</span>", unsafe_allow_html=True)
            st.markdown(
                "<span style='font-size:1em;'>El total recaudado por <b>multas</b> y <b>rifas</b> se reparte en partes iguales entre todos los miembros del grupo, como incentivo y beneficio colectivo.</span>",
                unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
            st.markdown(f"Miembros en el grupo: {n_miembros}")
            if n_miembros > 0:
                parte_igual = total_repartir / n_miembros
                st.success(f"Cada miembro recibe ${parte_igual:.2f} de multas y rifas, además de su ahorro individual.", icon="💸")
                st.markdown("<b>Detalle de reparto:</b>", unsafe_allow_html=True)
                detalle = []
                for m in miembros:
                    cursor.execute("SELECT SUM(Monto) as ahorrado FROM Ahorros WHERE Id_miembro = %s AND Id_grupo = %s", (m['id'], grupo_id))
                    ahorrado = cursor.fetchone()['ahorrado'] or 0
                    total_miembro = ahorrado + parte_igual
                    detalle.append({
                        'Miembro': m['nombre'],
                        'Ahorro': ahorrado,
                        'Multas+Rifas': parte_igual,
                        'Total a Recibir': total_miembro
                    })
                df = pd.DataFrame(detalle)
                df = df.rename(columns={
                    'Miembro': 'Miembro',
                    'Ahorro': 'Ahorro ($)',
                    'Multas+Rifas': 'Multas+Rifas ($)',
                    'Total a Recibir': 'Total a Recibir ($)'
                })
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No hay miembros en este grupo.")
    conexion.close()
