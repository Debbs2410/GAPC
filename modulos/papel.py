import streamlit as st

def panel():
    usuario = st.session_state["usuario"]
    st.title(f"Panel de {usuario['rol'].capitalize()}")

    if usuario["rol"] == "administradora":
        st.write("✅ Acceso total al sistema.")
    elif usuario["rol"] == "promotora":
        st.write(f"🔷 Acceso solo al distrito {usuario['id_distrito']}")
    elif usuario["rol"] == "directiva":
        st.write(f"🟢 Acceso al grupo {usuario['id_grupo']}")
    else:
        st.write("👤 Acceso limitado a su perfil personal.")
