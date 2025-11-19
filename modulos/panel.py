import streamlit as st
from modulos.registro_beneficiarios import registrar_beneficiario, crear_miembro, ver_todos_miembros
from modulos.registro_usuarios import registrar_usuario
from modulos.grupos import gestionar_grupos
from modulos.ciclos import gestionar_ciclos
from modulos.asistencia_multas import gestionar_asistencia_multas


def mostrar_panel():
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
            ["Registrar usuario", "Gestionar Miembros", "Grupo", "Ciclos", "Asistencia y Multas", "Caja", "Ver reportes", "Configuraciones"],
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
        elif opcion == "Caja":
            st.info("Módulo de Caja.")

        elif opcion == "Ver reportes":
            st.info("Módulo de reportes en desarrollo...")
        
        elif opcion == "Configuraciones":
            st.info("Opciones de configuración del sistema próximamente...")

    # --- PROMOTORA ---
    elif rol_limpio == "promotora":
        st.title("Panel de Promotora")
        st.sidebar.success(f"Acceso a mis grupos asignados.")
        st.write(f"Puedes gestionar tus grupos.")

    # --- DIRECTIVA ---
    elif rol_limpio == "directiva":
        st.title("Panel de Directiva")
        id_grupo = usuario.get('id_grupo') or usuario.get('ID_Grupo')
        st.sidebar.success(f"✅ Grupo {id_grupo}")
        registrar_beneficiario(id_grupo)

    else:
        st.error("❌ Rol no reconocido. Contacta al administrador.")
