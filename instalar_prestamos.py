"""
Script de instalación para el módulo de Préstamos
Crea las tablas necesarias en la base de datos
"""
import mysql.connector
from modulos.config.conexion import obtener_conexion

def instalar_prestamos():
    print("🔧 Instalando módulo de Préstamos...")
    
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        # Leer el archivo SQL
        print("📋 Creando tablas Prestamos y Pagos_Prestamos...")
        with open('crear_tabla_prestamos.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Ejecutar cada sentencia SQL
        for statement in sql_script.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        conexion.commit()
        print("✅ Módulo de Préstamos instalado correctamente!")
        print("\n📝 Próximos pasos:")
        print("   1. Reinicia la aplicación Streamlit")
        print("   2. Ve a: Préstamos en el menú principal")
        print("   3. Los miembros solo pueden pedir prestado hasta el monto que tienen ahorrado")
        
    except mysql.connector.Error as e:
        print(f"❌ Error de base de datos: {e}")
    except FileNotFoundError:
        print("❌ Error: No se encuentra el archivo crear_tabla_prestamos.sql")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()

if __name__ == "__main__":
    instalar_prestamos()
