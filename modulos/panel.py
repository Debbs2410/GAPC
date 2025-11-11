import streamlit as st
from modulos.registro_beneficiarios import registrar_beneficiario

def mostrar_panel():
    usuario = st.session_state["usuario"]
    rol = usuario["rol"]

    st.sidebar.title("📋 Menú de navegación")
    st.sidebar.write(f"👤 {usuario['nombre']} ({rol})")

    if rol == "Administradora":
        st.title("Panel de Administradora")
        st.write("Acceso completo a todos los distritos y grupos.")
        st.sidebar.success("✅ Control total del sistema.")
        # Aquí se agregan funcionalidades como gestión de usuarios, reportes, etc.

    elif rol == "Promotora":
        st.title("Panel de Promotora")
        st.sidebar.success(f"✅ Acceso al distrito {usuario['id_distrito']}")
        st.write(f"Puedes gestionar los grupos del distrito {usuario['id_distrito']}.")

    elif rol == "Directiva":
        st.title("Panel de Directiva")
        st.sidebar.success(f"✅ Grupo {usuario['id_grupo']} del distrito {usuario['id_distrito']}")
        registrar_beneficiario(usuario["id_grupo"])

    else:
        st.error("Rol no reconocido.")

