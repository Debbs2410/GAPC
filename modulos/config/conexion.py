import mysql.connector
import streamlit as st

def obtener_conexion():
    try:
        conexion = mysql.connector.connect(
            host="bnsf0ymzpvkirhrcgqov-mysql.services.clever-cloud.com",
            user="uz0ilcx1uwofz9ys",
            password="Q8EPNcwHwEh7PScgYUkT",   # tu contraseña de MySQL
            database="bnsf0ymzpvkirhrcgqov"
        )
        return conexion
    except mysql.connector.Error as e:
        st.error(f"Error de conexión: {e}")
        return None
