import streamlit as st
from modulos.registro_beneficiarios import registrar_beneficiario
from modulos.registro_usuarios import registrar_usuario

def mostrar_panel():
    # Aseguramos que haya un usuario en session_state
    if "usuario" not in st.session_state:
        st.error("No hay usuario en sesión. Por favor inicia sesión.")
        return

    usuario = st.session_state["usuario"]
    rol = usuario.get("rol")

    # --- Menú lateral ---
    st.sidebar.title("📋 Menú de navegación")
    st.sidebar.write(f"👤 {usuario.get('nombre', 'Sin nombre')} ({rol})")

    # --- ADMINISTRADORA ---
    if rol == "Administradora":
        st.title("Panel de Administradora")
        st.sidebar.success("✅ Control total del sistema.")
        st.write("Acceso completo a todos los distritos y grupos.")

        opcion = st.sidebar.radio(
            "Selecciona una acción:",
            ["Registrar usuario", "Ver reportes", "Configuraciones"],
        )

        if opcion == "Registrar usuario":
            registrar_usuario()
        elif opcion == "Ver reportes":
            st.info("📊 Módulo de reportes en desarrollo...")
            # Aquí puedes añadir show_all_users() u otras funciones
        elif opcion == "Configuraciones":
            st.info("⚙️ Opciones de configuración del sistema próximamente...")

    # --- PROMOTORA ---
    elif rol == "Promotora":
        st.title("Panel de Promotora")
        st.sidebar.success(f"✅ Acceso al distrito {usuario.get('id_distrito')}")
        st.write(f"Puedes gestionar los grupos del distrito {usuario.get('id_distrito')}.")

    # --- DIRECTIVA ---
    elif rol == "Directiva":
        st.title("Panel de Directiva")
        st.sidebar.success(f"✅ Grupo {usuario.get('id_grupo')} del distrito {usuario.get('id_distrito')}")
        registrar_beneficiario(usuario.get("id_grupo"))

    else:
        st.error("❌ Rol no reconocido.")



