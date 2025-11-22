import streamlit as st
from modulos.registro_beneficiarios import registrar_beneficiario, crear_miembro, ver_todos_miembros
from modulos.registro_usuarios import registrar_usuario
from modulos.grupos import gestionar_grupos
from modulos.ciclos import gestionar_ciclos
from modulos.asistencia_multas import gestionar_asistencia_multas
from modulos.ahorros import gestionar_ahorros

from modulos.prestamos import gestionar_prestamos


def mostrar_panel():

    # Botón para cerrar sesión
    if st.sidebar.button("Cerrar sesión", type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Sesión cerrada correctamente.")
        st.rerun()

    if "usuario" not in st.session_state or st.session_state["usuario"] is None:
        st.error("No hay usuario en sesión. Por favor inicia sesión.")
        return

    usuario = st.session_state["usuario"]
    rol_raw = usuario.get("rol") or usuario.get("Rol")
    
    if rol_raw:
        rol_limpio = rol_raw.strip().lower()
    else:
        rol_limpio = ""

    st.sidebar.title("📋 Menú de navegación")
    st.sidebar.write(f"👤 {usuario.get('Nombre_Usuario', usuario.get('nombre', 'Sin nombre'))} ({rol_raw})")

    if rol_limpio == "administradora":
        st.title("Panel de Administradora")
        st.sidebar.success("Control total del sistema.")
        st.write("Acceso completo a todos los grupos y configuraciones.")

        opcion = st.sidebar.radio(
            "Selecciona una acción:",
            [
                "Registrar usuario",
                "Gestionar Miembros",
                "Grupo",
                "Ciclos",
                "Asistencia y Multas",
                "Ahorros",
                "Préstamos",
                "Rifas",
                "Caja",
                "Ver reportes",
                "Configuraciones"
            ],
        )

        if opcion == "Registrar usuario":
            registrar_usuario()
        elif opcion == "Gestionar Miembros":
            tab1, tab2 = st.tabs(["👥 Ver Todos los Miembros", "➕ Crear Nuevo Miembro"])
            with tab1:
                ver_todos_miembros()
            with tab2:
                crear_miembro()
        elif opcion == "Grupo":
            gestionar_grupos()
        elif opcion == "Ciclos":
            gestionar_ciclos()
        elif opcion == "Asistencia y Multas":
            gestionar_asistencia_multas()
        elif opcion == "Ahorros":
            gestionar_ahorros()
        elif opcion == "Préstamos":
            gestionar_prestamos()
        elif opcion == "Caja":
            from modulos.caja import gestionar_caja
            gestionar_caja()
        elif opcion == "Rifas":
            from modulos.rifas import gestionar_rifas
            gestionar_rifas()
        elif opcion == "Ver reportes":
            from modulos.reportes import generar_reporte_ciclo
            generar_reporte_ciclo()
        elif opcion == "Configuraciones":
            from modulos.configuracion import mostrar_configuraciones
            mostrar_configuraciones()

    # --- PROMOTORA ---
    elif rol_limpio == "promotora":
        id_distrito = usuario.get("Id_distrito") or usuario.get("id_distrito")
        # Obtener nombre del distrito (requiere conexión a la base de datos)
        nombre_distrito = None
        if id_distrito:
            conexion_tmp = None
            try:
                from modulos.config.conexion import obtener_conexion
                conexion_tmp = obtener_conexion()
                if conexion_tmp:
                    cursor_tmp = conexion_tmp.cursor(dictionary=True)
                    cursor_tmp.execute("SELECT nombre_distrito FROM Distrito WHERE distrito_id = %s", (id_distrito,))
                    row = cursor_tmp.fetchone()
                    if row:
                        nombre_distrito = row['nombre_distrito']
            except Exception:
                pass
            finally:
                if conexion_tmp:
                    conexion_tmp.close()
        if nombre_distrito:
            st.title(f"Panel de Promotora - {nombre_distrito}")
        else:
            st.title("Panel de Promotora")
        st.sidebar.success("Acceso a todo su distrito.")
        opcion = st.sidebar.radio(
            "Selecciona una acción:",
            [
                "Registrar usuario",
                "Gestionar Miembros",
                "Grupo",
                "Ciclos",
                "Asistencia y Multas",
                "Ahorros",
                "Préstamos",
                "Rifas",
                "Caja",
                "Ver reportes",
                "Configuraciones"
            ],
        )

        if opcion == "Registrar usuario":
            registrar_usuario()
        elif opcion == "Gestionar Miembros":
            tab1, tab2 = st.tabs(["👥 Ver Todos los Miembros", "➕ Crear Nuevo Miembro"])
            with tab1:
                ver_todos_miembros(id_distrito=id_distrito)
            with tab2:
                crear_miembro(id_distrito=id_distrito)
        elif opcion == "Grupo":
            gestionar_grupos(id_distrito=id_distrito)
        elif opcion == "Ciclos":
            gestionar_ciclos(id_distrito=id_distrito)
        elif opcion == "Asistencia y Multas":
            gestionar_asistencia_multas(id_distrito=id_distrito)
        elif opcion == "Ahorros":
            gestionar_ahorros(id_distrito=id_distrito)
        elif opcion == "Préstamos":
            gestionar_prestamos(id_distrito=id_distrito)
        elif opcion == "Caja":
            from modulos.caja import gestionar_caja
            gestionar_caja(id_distrito=id_distrito)
        elif opcion == "Rifas":
            from modulos.rifas import gestionar_rifas
            gestionar_rifas(id_distrito=id_distrito)
        elif opcion == "Ver reportes":
            from modulos.reportes import generar_reporte_ciclo
            generar_reporte_ciclo(id_distrito=id_distrito)
        elif opcion == "Configuraciones":
            from modulos.configuracion import mostrar_configuraciones
            mostrar_configuraciones(id_distrito=id_distrito)

    # --- DIRECTIVA ---
    elif rol_limpio == "directiva":
        id_grupo = usuario.get('id_grupo') or usuario.get('ID_Grupo') or usuario.get('Id_grupo')
        id_distrito = usuario.get('id_distrito') or usuario.get('Id_distrito') or usuario.get('ID_DISTRITO') or usuario.get('ID_distrito')
        nombre_grupo = None
        nombre_distrito = None
        try:
            if id_grupo is not None:
                id_grupo_int = int(id_grupo)
                from modulos.config.conexion import obtener_conexion
                conexion_tmp = obtener_conexion()
                if conexion_tmp:
                    cursor_tmp = conexion_tmp.cursor(dictionary=True)
                    cursor_tmp.execute("SELECT Nombre, distrito_id FROM Grupos WHERE Id_grupo = %s", (id_grupo_int,))
                    row = cursor_tmp.fetchone()
                    if row:
                        nombre_grupo = row['Nombre']
                        id_distrito_grupo = row['distrito_id']
                        # Obtener nombre del distrito
                        cursor_tmp.execute("SELECT nombre_distrito FROM Distrito WHERE distrito_id = %s", (id_distrito_grupo,))
                        row_dist = cursor_tmp.fetchone()
                        if row_dist:
                            nombre_distrito = row_dist['nombre_distrito']
                    conexion_tmp.close()
        except Exception:
            pass
        if id_grupo is not None:
            st.title(f"Panel de Directiva - Grupo {id_grupo}")
        else:
            st.title("Panel de Directiva - Grupo no asignado")
        st.sidebar.success(f"Acceso solo a su grupo.")
        if id_grupo is not None:
            st.sidebar.info(f"ID de Grupo: {id_grupo}")
        opcion = st.sidebar.radio(
            "Selecciona una acción:",
            [
                "Gestionar Miembros",
                "Asistencia y Multas",
                "Ahorros",
                "Préstamos",
                "Rifas",
                "Caja",
                "Ver reportes"
            ],
        )

        if opcion == "Gestionar Miembros":
            tab1, tab2 = st.tabs(["👥 Ver Todos los Miembros", "➕ Crear Nuevo Miembro"])
            with tab1:
                try:
                    id_grupo_int = int(id_grupo)
                    ver_todos_miembros(id_grupo=id_grupo_int)
                except Exception:
                    st.warning("No se pudo determinar el grupo asignado. Contacta al administrador.")
            with tab2:
                try:
                    id_grupo_int = int(id_grupo)
                    crear_miembro(id_grupo=id_grupo_int)
                except Exception:
                    st.warning("No se pudo determinar el grupo asignado. Contacta al administrador.")
        elif opcion == "Asistencia y Multas":
            gestionar_asistencia_multas(id_grupo=id_grupo)
        elif opcion == "Ahorros":
            gestionar_ahorros(id_grupo=id_grupo)
        elif opcion == "Préstamos":
            gestionar_prestamos(id_grupo=id_grupo)
        elif opcion == "Caja":
            from modulos.caja import gestionar_caja
            gestionar_caja(id_grupo=id_grupo)
        elif opcion == "Rifas":
            from modulos.rifas import gestionar_rifas
            gestionar_rifas(id_grupo=id_grupo)
        elif opcion == "Ver reportes":
            from modulos.reportes import generar_reporte_ciclo
            generar_reporte_ciclo(id_grupo=id_grupo)

    else:
        st.error("❌ Rol no reconocido. Contacta al administrador.")
