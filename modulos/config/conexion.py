import mysql.connector
from mysql.connector import Error

def obtener_conexion():
    try:
        conexion = mysql.connector.connect(
            host='b7jbqyqg9ohuymynhssb-mysql.services.clever-cloud.com',
            user='urnv2oekoqjvm502',
            password='jnnALKYuBFm2WxRs8Vwv',
            database='b7jbqyqg9ohuymynhssb',
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
