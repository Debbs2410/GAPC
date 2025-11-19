import streamlit as st
from modulos.config.conexion import obtener_conexion
import pandas as pd


def gestionar_grupos():
    """
    Función principal para gestionar grupos.
    Permite crear, ver, editar y eliminar grupos.
    """
    st.title("👥 Gestión de Grupos")
    
    # Tabs para organizar las funcionalidades
    tab1, tab2, tab3 = st.tabs(["📋 Ver Grupos", "➕ Crear Grupo", "✏️ Editar/Eliminar"])
    
    with tab1:
        ver_todos_grupos()
    
    with tab2:
        crear_grupo()
    
    with tab3:
        editar_eliminar_grupo()


def ver_todos_grupos():
    """
    Muestra todos los grupos registrados en el sistema con su información completa.
    """
    st.subheader("📋 Lista de Grupos Registrados")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Consulta para obtener grupos con información adicional
        cursor.execute("""
            SELECT 
                g.Id_grupo,
                g.Nombre,
                g.Numero_miembros,
                g.Id_Ciclo,
                g.Id_caja,
                ci.Fecha_Inicio as ciclo_inicio,
                ci.Fecha_Fin as ciclo_fin,
                ca.Fondo_Comun as fondo_comun,
                COUNT(DISTINCT u.Id_usuario) as num_promotoras
            FROM Grupos g
            LEFT JOIN Ciclo ci ON g.Id_Ciclo = ci.Id_Ciclo
            LEFT JOIN Caja ca ON g.Id_caja = ca.Id_caja
            LEFT JOIN Usuarios u ON u.Id_grupo = g.Id_grupo AND u.Rol = 'Promotora'
            GROUP BY g.Id_grupo
            ORDER BY g.Id_grupo
        """)
        
        grupos = cursor.fetchall()
        
        if not grupos:
            st.info("📭 No hay grupos registrados aún.")
        else:
            # Convertir a DataFrame para mejor visualización
            df = pd.DataFrame(grupos)
            
            # Renombrar columnas para mostrar
            df = df.rename(columns={
                'Id_grupo': 'ID',
                'Nombre': 'Nombre del Grupo',
                'Numero_miembros': 'Nº Miembros',
                'Id_Ciclo': 'ID Ciclo',
                'Id_caja': 'ID Caja',
                'ciclo_inicio': 'Ciclo Inicio',
                'ciclo_fin': 'Ciclo Fin',
                'fondo_comun': 'Fondo Común ($)',
                'num_promotoras': 'Promotoras'
            })
            
            # Mostrar tabla
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Métricas generales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Grupos", len(grupos))
            with col2:
                total_miembros = sum([g['Numero_miembros'] or 0 for g in grupos])
                st.metric("👥 Total Miembros", total_miembros)
            with col3:
                grupos_con_ciclo = len([g for g in grupos if g['Id_Ciclo']])
                st.metric("🔄 Con Ciclo Activo", grupos_con_ciclo)
            with col4:
                fondo_total = sum([g['fondo_comun'] or 0 for g in grupos])
                st.metric("💰 Fondo Total", f"${fondo_total:.2f}")
            
            # Mostrar detalles expandibles de cada grupo
            st.divider()
            st.subheader("📌 Detalles por Grupo")
            
            for grupo in grupos:
                with st.expander(f"🔍 {grupo['Nombre']} (ID: {grupo['Id_grupo']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Miembros:** {grupo['Numero_miembros'] or 0}")
                        st.write(f"**ID Ciclo:** {grupo['Id_Ciclo'] or 'Sin ciclo'}")
                        st.write(f"**ID Caja:** {grupo['Id_caja'] or 'Sin caja'}")
                    
                    with col2:
                        if grupo['ciclo_inicio']:
                            st.write(f"**Ciclo Inicio:** {grupo['ciclo_inicio']}")
                        if grupo['ciclo_fin']:
                            st.write(f"**Ciclo Fin:** {grupo['ciclo_fin']}")
                        st.write(f"**Fondo Común:** ${grupo['fondo_comun'] or 0:.2f}")
                    
                    # Mostrar promotoras asignadas
                    cursor.execute("""
                        SELECT Nombre_Usuario as nombre, Correo as correo
                        FROM Usuarios 
                        WHERE Id_grupo = %s AND Rol = 'Promotora'
                    """, (grupo['Id_grupo'],))
                    promotoras = cursor.fetchall()
                    
                    if promotoras:
                        st.write("**👩‍💼 Promotoras asignadas:**")
                        for p in promotoras:
                            st.write(f"- {p['nombre']} ({p['correo']})")
                    else:
                        st.warning("⚠️ Sin promotoras asignadas")
                    
                    # Mostrar miembros del grupo
                    cursor.execute("""
                        SELECT nombre, sexo, Numero_Telefono 
                        FROM Miembros 
                        WHERE grupo_id = %s
                        ORDER BY nombre
                    """, (grupo['Id_grupo'],))
                    miembros = cursor.fetchall()
                    
                    if miembros:
                        st.write(f"**👤 Miembros del grupo ({len(miembros)}):**")
                        for m in miembros:
                            st.write(f"- {m['nombre']} ({m['sexo']}) - Tel: {m['Numero_Telefono']}")
                    else:
                        st.info("Sin miembros registrados")
    
    finally:
        conexion.close()


def crear_grupo():
    """
    Formulario para crear un nuevo grupo.
    """
    st.subheader("➕ Crear Nuevo Grupo")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Formulario de creación
        with st.form("form_crear_grupo"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre_grupo = st.text_input(
                    "📝 Nombre del Grupo*",
                    placeholder="Ej: Grupo Esperanza, Grupo Unidos, etc."
                )
                
                numero_miembros = st.number_input(
                    "👥 Número de Miembros*",
                    min_value=1,
                    max_value=50,
                    value=1,
                    help="Cantidad inicial de miembros (puedes actualizarlo después)"
                )
            
            with col2:
                # Obtener ciclos disponibles
                cursor.execute("SELECT Id_Ciclo, Fecha_Inicio, Fecha_Fin FROM Ciclo ORDER BY Id_Ciclo DESC")
                ciclos = cursor.fetchall()
                
                ciclos_dict = {"Sin ciclo asignado": None}
                if ciclos:
                    for c in ciclos:
                        ciclos_dict[f"Ciclo {c['Id_Ciclo']} ({c['Fecha_Inicio']} - {c['Fecha_Fin']})"] = c['Id_Ciclo']
                
                ciclo_seleccionado = st.selectbox("🔄 Ciclo", list(ciclos_dict.keys()))
                id_ciclo = ciclos_dict[ciclo_seleccionado]
                
                # Obtener cajas disponibles
                cursor.execute("SELECT Id_caja, Fondo_Comun FROM Caja ORDER BY Id_caja DESC")
                cajas = cursor.fetchall()
                
                cajas_dict = {"Sin caja asignada": None}
                if cajas:
                    for ca in cajas:
                        cajas_dict[f"Caja {ca['Id_caja']} (Fondo: ${ca['Fondo_Comun']:.2f})"] = ca['Id_caja']
                
                caja_seleccionada = st.selectbox("💰 Caja", list(cajas_dict.keys()))
                id_caja = cajas_dict[caja_seleccionada]
            
            st.divider()
            st.write("**👩‍💼 Asignar Promotoras** (opcional)")
            
            # Obtener promotoras disponibles
            cursor.execute("""
                SELECT Id_usuario, Nombre_Usuario as nombre, Correo as correo
                FROM Usuarios 
                WHERE Rol = 'Promotora'
                ORDER BY Nombre_Usuario
            """)
            promotoras = cursor.fetchall()
            
            promotoras_seleccionadas = []
            if promotoras:
                promotoras_dict = {f"{p['nombre']} ({p['correo']})": p['Id_usuario'] for p in promotoras}
                promotoras_seleccionadas = st.multiselect(
                    "Selecciona promotoras para asignar al grupo",
                    list(promotoras_dict.keys())
                )
                ids_promotoras = [promotoras_dict[p] for p in promotoras_seleccionadas]
            else:
                st.info("ℹ️ No hay promotoras disponibles en el sistema")
                ids_promotoras = []
            
            submitted = st.form_submit_button("✅ Crear Grupo", type="primary")
            
            if submitted:
                # Validaciones
                if not nombre_grupo:
                    st.error("❌ El nombre del grupo es obligatorio.")
                    return
                
                # Verificar que el nombre no esté duplicado
                cursor.execute("SELECT COUNT(*) as total FROM Grupos WHERE Nombre = %s", (nombre_grupo,))
                if cursor.fetchone()['total'] > 0:
                    st.error(f"❌ Ya existe un grupo con el nombre '{nombre_grupo}'.")
                    return
                
                # Insertar el grupo
                try:
                    sql = """
                    INSERT INTO Grupos (Nombre, Numero_miembros, Id_Ciclo, Id_caja)
                    VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(sql, (nombre_grupo, numero_miembros, id_ciclo, id_caja))
                    
                    # Obtener el ID del grupo recién creado
                    id_grupo_nuevo = cursor.lastrowid
                    
                    # Asignar promotoras al grupo
                    if ids_promotoras:
                        for id_promotora in ids_promotoras:
                            cursor.execute(
                                "UPDATE Usuarios SET Id_grupo = %s WHERE Id_usuario = %s",
                                (id_grupo_nuevo, id_promotora)
                            )
                    
                    conexion.commit()
                    st.success(f"✅ Grupo '{nombre_grupo}' creado exitosamente con ID {id_grupo_nuevo}!")
                    
                    if ids_promotoras:
                        st.info(f"👩‍💼 {len(ids_promotoras)} promotora(s) asignada(s) al grupo.")
                    
                    st.balloons()
                    st.rerun()
                
                except Exception as e:
                    conexion.rollback()
                    st.error(f"❌ Error al crear el grupo: {str(e)}")
    
    finally:
        conexion.close()


def editar_eliminar_grupo():
    """
    Permite editar o eliminar grupos existentes.
    """
    st.subheader("✏️ Editar o Eliminar Grupo")
    
    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ Error de conexión a la base de datos.")
        return
    
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Obtener lista de grupos
        cursor.execute("SELECT Id_grupo, Nombre FROM Grupos ORDER BY Nombre")
        grupos = cursor.fetchall()
        
        if not grupos:
            st.info("📭 No hay grupos registrados para editar.")
            return
        
        # Selector de grupo
        grupos_dict = {f"{g['Nombre']} (ID: {g['Id_grupo']})": g['Id_grupo'] for g in grupos}
        grupo_seleccionado = st.selectbox("🔍 Selecciona un grupo", list(grupos_dict.keys()))
        id_grupo = grupos_dict[grupo_seleccionado]
        
        # Obtener datos del grupo seleccionado
        cursor.execute("""
            SELECT * FROM Grupos WHERE Id_grupo = %s
        """, (id_grupo,))
        grupo = cursor.fetchone()
        
        if not grupo:
            st.error("❌ Grupo no encontrado.")
            return
        
        # Tabs para editar o eliminar
        tab1, tab2 = st.tabs(["✏️ Editar", "🗑️ Eliminar"])
        
        with tab1:
            st.write("**Información actual del grupo:**")
            
            with st.form("form_editar_grupo"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nuevo_nombre = st.text_input(
                        "📝 Nombre del Grupo",
                        value=grupo['Nombre']
                    )
                    
                    nuevo_numero_miembros = st.number_input(
                        "👥 Número de Miembros",
                        min_value=0,
                        max_value=50,
                        value=int(grupo['Numero_miembros'] or 0)
                    )
                
                with col2:
                    # Ciclos
                    cursor.execute("SELECT Id_Ciclo, Fecha_Inicio, Fecha_Fin FROM Ciclo ORDER BY Id_Ciclo DESC")
                    ciclos = cursor.fetchall()
                    
                    ciclos_dict = {"Sin ciclo asignado": None}
                    if ciclos:
                        for c in ciclos:
                            ciclos_dict[f"Ciclo {c['Id_Ciclo']} ({c['Fecha_Inicio']} - {c['Fecha_Fin']})"] = c['Id_Ciclo']
                    
                    # Encontrar el ciclo actual
                    ciclo_actual = None
                    for key, val in ciclos_dict.items():
                        if val == grupo['Id_Ciclo']:
                            ciclo_actual = key
                            break
                    if not ciclo_actual:
                        ciclo_actual = "Sin ciclo asignado"
                    
                    nuevo_ciclo = st.selectbox(
                        "🔄 Ciclo",
                        list(ciclos_dict.keys()),
                        index=list(ciclos_dict.keys()).index(ciclo_actual)
                    )
                    nuevo_id_ciclo = ciclos_dict[nuevo_ciclo]
                    
                    # Cajas
                    cursor.execute("SELECT Id_caja, Fondo_Comun FROM Caja ORDER BY Id_caja DESC")
                    cajas = cursor.fetchall()
                    
                    cajas_dict = {"Sin caja asignada": None}
                    if cajas:
                        for ca in cajas:
                            cajas_dict[f"Caja {ca['Id_caja']} (Fondo: ${ca['Fondo_Comun']:.2f})"] = ca['Id_caja']
                    
                    # Encontrar la caja actual
                    caja_actual = None
                    for key, val in cajas_dict.items():
                        if val == grupo['Id_caja']:
                            caja_actual = key
                            break
                    if not caja_actual:
                        caja_actual = "Sin caja asignada"
                    
                    nueva_caja = st.selectbox(
                        "💰 Caja",
                        list(cajas_dict.keys()),
                        index=list(cajas_dict.keys()).index(caja_actual)
                    )
                    nueva_id_caja = cajas_dict[nueva_caja]
                
                st.divider()
                st.write("**👩‍💼 Promotoras Asignadas**")
                
                # Obtener promotoras actuales del grupo
                cursor.execute("""
                    SELECT Id_usuario, Nombre_Usuario as nombre, Correo as correo
                    FROM Usuarios 
                    WHERE Id_grupo = %s AND Rol = 'Promotora'
                """, (id_grupo,))
                promotoras_actuales = cursor.fetchall()
                
                # Obtener todas las promotoras disponibles
                cursor.execute("""
                    SELECT Id_usuario, Nombre_Usuario as nombre, Correo as correo
                    FROM Usuarios 
                    WHERE Rol = 'Promotora'
                    ORDER BY Nombre_Usuario
                """)
                todas_promotoras = cursor.fetchall()
                
                if todas_promotoras:
                    promotoras_dict = {f"{p['nombre']} ({p['correo']})": p['Id_usuario'] for p in todas_promotoras}
                    
                    # Pre-seleccionar las promotoras actuales
                    promotoras_actuales_nombres = [
                        f"{p['nombre']} ({p['correo']})" for p in promotoras_actuales
                    ]
                    
                    nuevas_promotoras = st.multiselect(
                        "Actualizar promotoras del grupo",
                        list(promotoras_dict.keys()),
                        default=promotoras_actuales_nombres
                    )
                    nuevos_ids_promotoras = [promotoras_dict[p] for p in nuevas_promotoras]
                else:
                    st.info("ℹ️ No hay promotoras disponibles")
                    nuevos_ids_promotoras = []
                
                submitted = st.form_submit_button("💾 Guardar Cambios", type="primary")
                
                if submitted:
                    try:
                        # Actualizar datos del grupo
                        sql = """
                        UPDATE Grupos 
                        SET Nombre = %s, Numero_miembros = %s, Id_Ciclo = %s, Id_caja = %s
                        WHERE Id_grupo = %s
                        """
                        cursor.execute(sql, (
                            nuevo_nombre,
                            nuevo_numero_miembros,
                            nuevo_id_ciclo,
                            nueva_id_caja,
                            id_grupo
                        ))
                        
                        # Actualizar asignación de promotoras
                        # 1. Quitar el grupo a todas las promotoras que lo tenían
                        cursor.execute("""
                            UPDATE Usuarios 
                            SET Id_grupo = NULL 
                            WHERE Id_grupo = %s AND Rol = 'Promotora'
                        """, (id_grupo,))
                        
                        # 2. Asignar el grupo a las nuevas promotoras seleccionadas
                        if nuevos_ids_promotoras:
                            for id_promotora in nuevos_ids_promotoras:
                                cursor.execute(
                                    "UPDATE Usuarios SET Id_grupo = %s WHERE Id_usuario = %s",
                                    (id_grupo, id_promotora)
                                )
                        
                        conexion.commit()
                        st.success(f"✅ Grupo '{nuevo_nombre}' actualizado correctamente!")
                        st.rerun()
                    
                    except Exception as e:
                        conexion.rollback()
                        st.error(f"❌ Error al actualizar el grupo: {str(e)}")
        
        with tab2:
            st.warning("⚠️ **Advertencia**: Esta acción no se puede deshacer.")
            
            # Verificar dependencias
            cursor.execute("SELECT COUNT(*) as total FROM Miembros WHERE grupo_id = %s", (id_grupo,))
            num_miembros = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM Usuarios WHERE Id_grupo = %s", (id_grupo,))
            num_usuarios = cursor.fetchone()['total']
            
            st.write(f"**Información del grupo a eliminar:**")
            st.write(f"- Nombre: **{grupo['Nombre']}**")
            st.write(f"- Miembros asociados: **{num_miembros}**")
            st.write(f"- Usuarios asignados: **{num_usuarios}**")
            
            if num_miembros > 0 or num_usuarios > 0:
                st.error("❌ No se puede eliminar el grupo porque tiene miembros o usuarios asociados.")
                st.info("💡 Primero debes reasignar o eliminar los miembros y usuarios del grupo.")
            else:
                confirmar = st.checkbox("Confirmo que deseo eliminar este grupo")
                
                if st.button("🗑️ Eliminar Grupo", type="secondary", disabled=not confirmar):
                    try:
                        cursor.execute("DELETE FROM Grupos WHERE Id_grupo = %s", (id_grupo,))
                        conexion.commit()
                        st.success(f"✅ Grupo '{grupo['Nombre']}' eliminado correctamente.")
                        st.rerun()
                    except Exception as e:
                        conexion.rollback()
                        st.error(f"❌ Error al eliminar el grupo: {str(e)}")
    
    finally:
        conexion.close()
