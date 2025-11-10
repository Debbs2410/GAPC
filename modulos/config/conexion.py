import mysql.connector
from mysql.connector import Error

def obtener_conexion():
    try:
        conexion = mysql.connector.connect(
            host='bnsf0ymzpvkirhrcgqov-mysql.services.clever-cloud.com',
            user='uz0ilcx1uwofz9ys',
            password='Q8EPNcwHwEh7PScgYUkT',
            database='bnsf0ymzpvkirhrcgqov',
            port=3306
        )
        if conexion.is_connected():
            print("✅ Conexión establecida")
            return conexion
        else:
            print("❌ Conexión fallida (is_connected = False)")
            return None
    except mysql.connector.Error as e:
        print(f"❌ Error al conectar: {e}")
        return None
