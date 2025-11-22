"""
Script para instalar las configuraciones de ahorro con monto mínimo
"""
from modulos.config.conexion import obtener_conexion

def instalar_configuracion_ahorros():
    print("🔧 Instalando configuración de ahorros...")
    
    conexion = obtener_conexion()
    if not conexion:
        print("❌ Error de conexión a la base de datos.")
        return False
    
    cursor = conexion.cursor()
    
    try:
        # 1. Crear tabla Configuracion_Ahorros
        print("📋 Creando tabla Configuracion_Ahorros...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Configuracion_Ahorros (
                Id_config INT AUTO_INCREMENT PRIMARY KEY,
                Monto_minimo DECIMAL(10,2) NOT NULL DEFAULT 1.00,
                Aplica_multa TINYINT(1) NOT NULL DEFAULT 1,
                Monto_multa DECIMAL(10,2) NOT NULL DEFAULT 1.00,
                Descripcion TEXT NULL,
                Fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 2. Insertar configuración por defecto
        print("💾 Insertando configuración por defecto...")
        cursor.execute("""
            INSERT INTO Configuracion_Ahorros (Monto_minimo, Aplica_multa, Monto_multa, Descripcion)
            VALUES (2.00, 1, 1.00, 'Monto mínimo de ahorro requerido por reunión. Si no se cumple, se aplica multa automática.')
            ON DUPLICATE KEY UPDATE Id_config = Id_config
        """)
        
        # 3. Agregar tipo de multa Falta_Ahorro
        print("⚠️ Agregando tipo de multa por falta de ahorro...")
        cursor.execute("""
            INSERT INTO Configuracion_Multas (Tipo_multa, Monto_default, Descripcion)
            VALUES ('Falta_Ahorro', 1.00, 'Multa por no cumplir el monto mínimo de ahorro requerido')
            ON DUPLICATE KEY UPDATE Tipo_multa = Tipo_multa
        """)
        
        conexion.commit()
        print("✅ Configuración de ahorros instalada correctamente!")
        print("\n📝 Próximos pasos:")
        print("   1. Reinicia la aplicación Streamlit")
        print("   2. Ve a: Ahorros > Configuración")
        print("   3. Ajusta el monto mínimo según necesites")
        print("   4. Comienza a registrar ahorros con validación automática")
        
        return True
        
    except Exception as e:
        conexion.rollback()
        print(f"❌ Error durante la instalación: {str(e)}")
        return False
    
    finally:
        conexion.close()

if __name__ == "__main__":
    instalar_configuracion_ahorros()
