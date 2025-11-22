"""
Script para crear la tabla de Ahorros en la base de datos.
Ejecutar este archivo una sola vez para crear la tabla.
"""

from modulos.config.conexion import obtener_conexion

def crear_tabla_ahorros():
    """Crea la tabla de Ahorros en la base de datos."""
    
    conexion = obtener_conexion()
    if not conexion:
        print("❌ Error de conexión a la base de datos.")
        return False
    
    cursor = conexion.cursor()
    
    try:
        print("🔄 Creando tabla Ahorros...")
        
        # SQL para crear la tabla
        sql_create_table = """
        CREATE TABLE IF NOT EXISTS Ahorros (
            Id_ahorro INT AUTO_INCREMENT PRIMARY KEY,
            Id_miembro INT NOT NULL,
            Id_grupo INT NOT NULL,
            Id_Ciclo INT NOT NULL,
            Id_reunion INT NULL,
            Monto DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
            Fecha_ahorro DATE NOT NULL,
            Fecha_devolucion DATE NULL,
            Estado ENUM('Activo', 'Devuelto') DEFAULT 'Activo',
            Observaciones TEXT NULL,
            Registrado_por INT NULL,
            Fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (Id_miembro) REFERENCES Miembros(id) ON DELETE CASCADE,
            FOREIGN KEY (Id_grupo) REFERENCES Grupos(Id_grupo) ON DELETE CASCADE,
            FOREIGN KEY (Id_Ciclo) REFERENCES Ciclo(Id_Ciclo) ON DELETE CASCADE,
            FOREIGN KEY (Id_reunion) REFERENCES Reuniones(Id_reunion) ON DELETE SET NULL,
            FOREIGN KEY (Registrado_por) REFERENCES Usuarios(Id_usuario) ON DELETE SET NULL,
            
            INDEX idx_miembro (Id_miembro),
            INDEX idx_grupo (Id_grupo),
            INDEX idx_ciclo (Id_Ciclo),
            INDEX idx_reunion (Id_reunion),
            INDEX idx_estado (Estado),
            INDEX idx_fecha (Fecha_ahorro),
            
            UNIQUE KEY unique_ahorro_reunion (Id_miembro, Id_reunion)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        cursor.execute(sql_create_table)
        conexion.commit()
        
        print("✅ Tabla Ahorros creada exitosamente!")
        
        # Verificar que la tabla se creó
        cursor.execute("SHOW TABLES LIKE 'Ahorros'")
        result = cursor.fetchone()
        
        if result:
            print("✅ Verificación: La tabla Ahorros existe en la base de datos")
            
            # Mostrar estructura de la tabla
            cursor.execute("DESCRIBE Ahorros")
            columns = cursor.fetchall()
            print("\n📋 Estructura de la tabla Ahorros:")
            print("-" * 80)
            for col in columns:
                print(f"  {col[0]:20} | {col[1]:20} | Null: {col[2]:5} | Key: {col[3]:5}")
            print("-" * 80)
            
            return True
        else:
            print("⚠️ Advertencia: No se pudo verificar la tabla")
            return False
            
    except Exception as e:
        print(f"❌ Error al crear la tabla: {str(e)}")
        conexion.rollback()
        return False
    finally:
        cursor.close()
        conexion.close()


if __name__ == "__main__":
    print("=" * 80)
    print("🚀 INSTALACIÓN DEL MÓDULO DE AHORROS")
    print("=" * 80)
    print()
    
    resultado = crear_tabla_ahorros()
    
    print()
    if resultado:
        print("=" * 80)
        print("✅ ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!")
        print("=" * 80)
        print()
        print("📝 Próximos pasos:")
        print("  1. Reinicia la aplicación Streamlit")
        print("  2. Ve al Panel de Administradora")
        print("  3. Selecciona 'Ahorros' en el menú")
        print("  4. ¡Comienza a registrar ahorros!")
        print()
    else:
        print("=" * 80)
        print("❌ LA INSTALACIÓN FALLÓ")
        print("=" * 80)
        print()
        print("🔧 Posibles soluciones:")
        print("  1. Verifica tu conexión a la base de datos")
        print("  2. Asegúrate de tener permisos para crear tablas")
        print("  3. Revisa que las tablas referenciadas existan:")
        print("     - Miembros")
        print("     - Grupos")
        print("     - Ciclo")
        print("     - Reuniones")
        print("     - Usuarios")
        print()
