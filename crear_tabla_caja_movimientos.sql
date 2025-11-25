-- Script para crear la tabla Caja_Movimientos
CREATE TABLE IF NOT EXISTS Caja_Movimientos (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    Id_grupo INT NOT NULL,
    Monto DECIMAL(10,2) NOT NULL,
    Tipo VARCHAR(50) NOT NULL,
    Fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    Descripcion VARCHAR(255)
    -- Agrega aquí otros campos si tu aplicación los requiere
);
