import streamlit as st
from modulos.registro_beneficiarios import registrar_beneficiario, ver_todos_miembros, crear_miembro
from modulos.registro_usuarios import registrar_usuario

def mostrar_panel():
    # Aseguramos que haya un usuario en session_state
    if "usuario" not in st.session_state:
        st.error("No hay usuario en sesión. Por favor inicia sesión.")
        return

    usuario = st.session_state["usuario"]
    rol = usuario.get("rol") or usuario.get("Rol")

    # --- Menú lateral ---
    st.sidebar.title("📋 Menú de navegación")
    st.sidebar.write(f"👤 {usuario.get('Nombre_Usuario', usuario.get('nombre', 'Sin nombre'))} ({rol})")

    # --- ADMINISTRADORA ---
    if rol == "Administradora":
        st.title("Panel de Administradora")
        st.sidebar.success("✅ Control total del sistema.")
        st.write("Acceso completo a todos los distritos y grupos.")

        opcion = st.selectbox(
            "Selecciona una acción:",
            ["Registrar usuario", "Gestionar Miembros", "Ver reportes", "Configuraciones", "Grupo", "Ciclos", "Caja"],
        )

        if opcion == "Registrar usuario":
            registrar_usuario()
        elif opcion == "Gestionar Miembros":
            tab1, tab2 = st.tabs(["👥 Ver Todos los Miembros", "➕ Crear Nuevo Miembro"])
            with tab1:
                ver_todos_miembros()
            with tab2:
                crear_miembro()
        elif opcion == "Ver reportes":
            st.info("📊 Módulo de reportes en desarrollo...")
        elif opcion == "Configuraciones":
            st.info("⚙️ Opciones de configuración del sistema próximamente...")

    # --- PROMOTORA ---
    elif rol == "Promotora":
        st.title("Panel de Promotora")
        id_distrito = usuario.get('id_distrito') or usuario.get('ID_Distrito')
        st.sidebar.success(f"✅ Acceso al distrito {id_distrito}")
        st.write(f"Puedes gestionar los grupos del distrito {id_distrito}.")

    # --- DIRECTIVA ---
    elif rol == "Directiva":
        st.title("Panel de Directiva")
        id_grupo = usuario.get('id_grupo') or usuario.get('ID_Grupo')
        id_distrito = usuario.get('id_distrito') or usuario.get('ID_Distrito')
        st.sidebar.success(f"✅ Grupo {id_grupo} del distrito {id_distrito}")
        registrar_beneficiario(id_grupo)

    else:
        st.error("❌ Rol no reconocido.")



