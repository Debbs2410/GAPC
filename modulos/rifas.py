import streamlit as st
from modulos.solo_lectura import es_administradora
from modulos.config.conexion import obtener_conexion
import pandas as pd

def gestionar_rifas(id_distrito=None, id_grupo=None):
    st.title("🎟️ Gestión de Rifas para Fondo de Grupos")
    # Solo lectura para administradora
    solo_lectura = es_administradora()
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    cursor = conexion.cursor(dictionary=True)
    # Obtener grupos y ciclos filtrando por grupo, distrito o todos
    if id_grupo is not None:
        cursor.execute("SELECT Id_grupo, Nombre, Id_Ciclo FROM Grupos WHERE Id_grupo = %s ORDER BY Nombre", (id_grupo,))
    elif id_distrito is not None:
        cursor.execute("SELECT Id_grupo, Nombre, Id_Ciclo FROM Grupos WHERE distrito_id = %s ORDER BY Nombre", (id_distrito,))
    else:
        cursor.execute("SELECT Id_grupo, Nombre, Id_Ciclo FROM Grupos ORDER BY Nombre")
    grupos = cursor.fetchall()
    grupos_dict = {g['Nombre']: (g['Id_grupo'], g['Id_Ciclo']) for g in grupos}
    # Si solo hay un grupo (directiva), bloquear el selectbox
    if id_grupo is not None and len(grupos) == 1:
        grupo_nombre = list(grupos_dict.keys())[0]
        st.selectbox("Grupo", options=[grupo_nombre], index=0, disabled=True)
    else:
        grupo_nombre = st.selectbox("Grupo", list(grupos_dict.keys()), disabled=solo_lectura)

    # Obtener ciclos
    cursor.execute("SELECT Id_Ciclo, Fecha_Inicio, Fecha_Fin FROM Ciclo ORDER BY Fecha_Inicio DESC")
    ciclos = cursor.fetchall()
    ciclos_dict = {f"Ciclo {c['Id_Ciclo']} ({c['Fecha_Inicio']} - {c['Fecha_Fin']})": c['Id_Ciclo'] for c in ciclos}

    st.subheader("Registrar nueva rifa")
    if solo_lectura:
        st.info("🔒 Esta función no está habilitada para administradora. Solo puede ver el historial de rifas.")
    else:
        with st.form("form_rifa"):
            grupo_nombre = st.selectbox("Grupo", list(grupos_dict.keys()), disabled=solo_lectura)
            grupo_id, grupo_ciclo_id = grupos_dict[grupo_nombre]
            # Seleccionar ciclo (por defecto el del grupo)
            ciclo_opciones = list(ciclos_dict.keys())
            ciclo_default = ciclo_opciones.index(next((k for k, v in ciclos_dict.items() if v == grupo_ciclo_id), ciclo_opciones[0]))
            ciclo_sel = st.selectbox("Ciclo", ciclo_opciones, index=ciclo_default, disabled=solo_lectura)
            id_ciclo = ciclos_dict[ciclo_sel]
            nombre_rifa = st.text_input("Nombre de la rifa", disabled=solo_lectura)
            fecha = st.date_input("Fecha de la rifa", disabled=solo_lectura)
            monto = st.number_input("Monto recaudado ($)", min_value=0.0, step=0.01, format="%.2f", disabled=solo_lectura)
            descripcion = st.text_area("Descripción de la actividad", disabled=solo_lectura)
            submitted = st.form_submit_button("Registrar Rifa", type="primary", disabled=solo_lectura)
            if submitted:
                if not nombre_rifa or not monto:
                    st.warning("Completa todos los campos obligatorios.")
                else:
                    try:
                        # Verificar si ya existe una rifa igual para el mismo grupo y ciclo
                        cursor.execute("SELECT 1 FROM Rifas WHERE grupo_id = %s AND Id_Ciclo = %s AND nombre = %s", (grupo_id, id_ciclo, nombre_rifa))
                        if cursor.fetchone():
                            st.info("Ya existe una rifa con ese nombre para este grupo y ciclo.")
                        else:
                            sql = """
                            INSERT INTO Rifas (grupo_id, Id_Ciclo, nombre, fecha, monto, descripcion)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """
                            cursor.execute(sql, (grupo_id, id_ciclo, nombre_rifa, fecha, monto, descripcion))
                            conexion.commit()
                            st.success(f"Rifa '{nombre_rifa}' registrada para el grupo '{grupo_nombre}' en el ciclo {id_ciclo}.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error al registrar la rifa: {str(e)}")
    st.divider()
    st.subheader("Historial de Rifas por Grupo y Ciclo")
    col1, col2 = st.columns(2)
    # Si es directiva (id_grupo presente), solo mostrar rifas de su grupo
    if id_grupo is not None:
        grupo_filtro = list(grupos_dict.keys())[0]
        with col1:
            st.selectbox("Filtrar por grupo", [grupo_filtro], index=0, disabled=True, key="filtro_rifa_grupo")
    else:
        with col1:
            grupo_filtro = st.selectbox("Filtrar por grupo", ["Todos"] + list(grupos_dict.keys()), key="filtro_rifa_grupo")
    with col2:
        ciclo_filtro = st.selectbox("Filtrar por ciclo", ["Todos"] + list(ciclos_dict.keys()), key="filtro_rifa_ciclo")

    query = "SELECT r.*, g.Nombre as grupo_nombre, c.Fecha_Inicio, c.Fecha_Fin FROM Rifas r JOIN Grupos g ON r.grupo_id = g.Id_grupo JOIN Ciclo c ON r.Id_Ciclo = c.Id_Ciclo WHERE 1=1"
    params = []
    if id_grupo is not None:
        query += " AND g.Id_grupo = %s"
        params.append(id_grupo)
    elif grupo_filtro != "Todos":
        query += " AND g.Nombre = %s"
        params.append(grupo_filtro)
    if ciclo_filtro != "Todos":
        query += " AND r.Id_Ciclo = %s"
        params.append(ciclos_dict[ciclo_filtro])
    query += " ORDER BY r.fecha DESC"
    cursor.execute(query, params)
    rifas = cursor.fetchall()
    if rifas:
        df = pd.DataFrame(rifas)
        df = df.rename(columns={
            'nombre': 'Nombre Rifa',
            'fecha': 'Fecha',
            'monto': 'Monto ($)',
            'descripcion': 'Descripción',
            'grupo_nombre': 'Grupo',
            'Fecha_Inicio': 'Inicio Ciclo',
            'Fecha_Fin': 'Fin Ciclo'
        })
        st.dataframe(df[['Grupo', 'Nombre Rifa', 'Fecha', 'Monto ($)', 'Descripción', 'Inicio Ciclo', 'Fin Ciclo']], use_container_width=True, hide_index=True)
    else:
        st.info("No hay rifas registradas para este grupo/ciclo.")
    conexion.close()
