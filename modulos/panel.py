def mostrar_panel():
    import streamlit as st
    # Aseguramos que las funciones que usaremos estén disponibles:
    from modulos.registro_beneficiarios import registrar_beneficiario, ver_todos_miembros, crear_miembro
    from modulos.registro_usuarios import registrar_usuario
    
    # --- VALIDACIÓN ROBUSTA DE SESIÓN (CORRECCIÓN DE ERROR) ---
    # Aseguramos que la clave "usuario" exista Y que su valor no sea None.
    if "usuario" not in st.session_state or st.session_state["usuario"] is None:
        st.error("No hay usuario en sesión. Por favor inicia sesión.")
        return

    usuario = st.session_state["usuario"]
    # Intentamos obtener el rol, cubriendo mayúsculas y minúsculas de la columna de la DB.
    rol_raw = usuario.get("rol") or usuario.get("Rol")
    
    # Normalizamos el rol a minúsculas y sin espacios para una comparación segura
    if rol_raw:
        rol_limpio = rol_raw.strip().lower()
    else:
        rol_limpio = ""

    # --- Menú lateral ---
    st.sidebar.title("📋 Menú de navegación")
    st.sidebar.write(f"👤 {usuario.get('Nombre_Usuario', usuario.get('nombre', 'Sin nombre'))} ({rol_raw})")

    # --- ADMINISTRADORA ---
    if rol_limpio == "administradora":
        st.title("Panel de Administradora")
        st.sidebar.success("✅ Control total del sistema.")
        st.write("Acceso completo a todos los distritos, grupos y configuraciones.")

        opcion = st.sidebar.radio(
            "Selecciona una acción:",
            # Opciones completas de la Administradora, incluyendo Ciclos y Caja
            ["Registrar usuario", "Gestionar Miembros", "Grupo", "Ciclos", "Caja", "Ver reportes", "Configuraciones"],
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
            st.info("📦 Módulo de Grupos.")
        elif opcion == "Ciclos":
            st.info("⏳ Módulo de Ciclos.")
        elif opcion == "Caja":
            st.info("💰 Módulo de Caja.")

        elif opcion == "Ver reportes":
            st.info("📊 Módulo de reportes en desarrollo...")
        
        elif opcion == "Configuraciones":
            st.info("⚙️ Opciones de configuración del sistema próximamente...")

    # --- PROMOTORA ---
    elif rol_limpio == "promotora":
        st.title("Panel de Promotora")
        id_distrito = usuario.get('id_distrito') or usuario.get('ID_Distrito')
        st.sidebar.success(f"✅ Acceso al distrito {id_distrito}")
        st.write(f"Puedes gestionar los grupos del distrito {id_distrito}.")
        
        # Aquí iría el st.sidebar.radio con las opciones de Promotora (ej: Ver Grupos de mi Distrito, Reportes)

    # --- DIRECTIVA ---
    elif rol_limpio == "directiva":
        st.title("Panel de Directiva")
        id_grupo = usuario.get('id_grupo') or usuario.get('ID_Grupo')
        id_distrito = usuario.get('id_distrito') or usuario.get('ID_Distrito')
        st.sidebar.success(f"✅ Grupo {id_grupo} del distrito {id_distrito}")
        registrar_beneficiario(id_grupo)
        
        # Aquí iría el st.sidebar.radio con las opciones de Directiva (ej: Registrar Aportes, Autorizar Préstamos)

    else:
        st.error("❌ Rol no reconocido. Contacta al administrador.")


