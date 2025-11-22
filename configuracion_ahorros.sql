-- Tabla para configurar el monto mínimo de ahorro requerido

CREATE TABLE IF NOT EXISTS Configuracion_Ahorros (
    Id_config INT AUTO_INCREMENT PRIMARY KEY,
    Monto_minimo DECIMAL(10,2) NOT NULL DEFAULT 1.00,
    Aplica_multa TINYINT(1) NOT NULL DEFAULT 1,
    Monto_multa DECIMAL(10,2) NOT NULL DEFAULT 1.00,
    Descripcion TEXT NULL,
    Fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertar configuración por defecto
INSERT INTO Configuracion_Ahorros (Monto_minimo, Aplica_multa, Monto_multa, Descripcion)
VALUES (2.00, 1, 1.00, 'Monto mínimo de ahorro requerido por reunión. Si no se cumple, se aplica multa automática.')
ON DUPLICATE KEY UPDATE Monto_minimo = Monto_minimo;
