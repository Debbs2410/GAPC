import mysql.connector
import streamlit as st

def obtener_conexion():
    try:
        return mysql.connector.connect(
            host="bnsf0ymzpvkirhrcgqov-mysql.services.clever-cloud.com",        # o el nombre de tu servidor
            user="uz0ilcx1uwofz9ys",             # tu usuario MySQL
            password="Q8EPNcwHwEh7PScgYUkT",             # tu contraseña MySQL
            database="bnsf0ymzpvkirhrcgqov"   # nombre de tu base de datos
        )
    except mysql.connector.Error as e:
        st.error(f"Error de conexión: {e}")
        return None

