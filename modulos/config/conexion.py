import mysql.connector
import streamlit as st

def obtener_conexion():
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",   # tu contraseña de MySQL
            database="cooperativa_db"
        )
        return conexion
    except mysql.connector.Error as e:
        st.error(f"Error de conexión: {e}")
        return None
