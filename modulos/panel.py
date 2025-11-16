def mostrar_panel():
    # ... (código previo) ...
    
    usuario = st.session_state["usuario"]
    # 1. Obtenemos el rol y lo convertimos a minúsculas y limpiamos espacios
    rol_raw = usuario.get("rol") or usuario.get("Rol")
    
    # 2. Convertimos a minúsculas y quitamos espacios para asegurar la comparación
    if rol_raw:
        rol_limpio = rol_raw.strip().lower()
    else:
        rol_limpio = "" # Si no hay rol, queda vacío

    # Mostramos el nombre de usuario y el rol limpio en el sidebar
    st.sidebar.title("📋 Menú de navegación")
    st.sidebar.write(f"👤 {usuario.get('Nombre_Usuario', usuario.get('nombre', 'Sin nombre'))} ({rol_raw})")
    
    # --- ADMINISTRADORA ---
    # 3. Comparamos con la cadena en minúsculas y sin espacios
    if rol_limpio == "administradora":
        st.title("Panel de Administradora")
        st.sidebar.success("✅ Control total del sistema.")
        st.write("Acceso completo a todos los distritos y grupos.")

        opcion = st.sidebar.radio(
            "Selecciona una acción:",
            # Las opciones de Ciclos y Caja SÍ ESTÁN INCLUIDAS AQUÍ
            ["Registrar usuario", "Gestionar Miembros", "Ver reportes", "Configuraciones", "Grupo", "Ciclos", "Caja"],
        )

        # ... (el resto de tu lógica de Administradora es correcta) ...

    # --- PROMOTORA ---
    elif rol_limpio == "promotora":
        st.title("Panel de Promotora")
        # ... (código de Promotora) ...

    # --- DIRECTIVA ---
    elif rol_limpio == "directiva":
        st.title("Panel de Directiva")
        # ... (código de Directiva) ...

    else:
        st.error("❌ Rol no reconocido.")



