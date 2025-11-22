import streamlit as st

def mostrar_configuraciones(id_distrito=None):
    st.title("⚙️ Configuración del Sistema")
    if id_distrito is not None:
        st.caption(f"Configuración para el distrito: {id_distrito}")
    st.info("Aquí puedes personalizar parámetros generales del sistema. (Ejemplo: tasas, límites, mensajes, etc.)")

    # Parámetro de ejemplo: tasa de interés por defecto
    tasa_interes = st.number_input(
        "Tasa de interés por defecto (%)",
        min_value=0.0, max_value=100.0, value=5.0, step=0.1,
        help="Esta tasa se usará como sugerencia al crear nuevos grupos o préstamos."
    )

    # Parámetro de ejemplo: monto mínimo de ahorro
    monto_min_ahorro = st.number_input(
        "Monto mínimo de ahorro ($)",
        min_value=0.0, value=10.0, step=1.0,
        help="Este monto se sugerirá como mínimo en los formularios de ahorro."
    )

    # Mensaje institucional
    mensaje = st.text_area(
        "Mensaje institucional (opcional)",
        value="Bienvenido al sistema GAPC. Recuerda mantener tus datos actualizados.",
        help="Este mensaje puede mostrarse en la pantalla de inicio o panel."
    )

    if st.button("Guardar configuración", type="primary"):
        st.success("Configuración guardada (simulada, no persistente).")
        st.info(f"Tasa de interés: {tasa_interes}% | Monto mínimo ahorro: ${monto_min_ahorro} | Mensaje: {mensaje}")

    st.caption("Puedes agregar más parámetros según las necesidades del sistema.")
