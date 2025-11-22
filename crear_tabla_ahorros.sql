-- Script para crear la tabla de Ahorros en la base de datos

-- Tabla de Ahorros
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
    
    -- Claves foráneas
    FOREIGN KEY (Id_miembro) REFERENCES Miembros(id) ON DELETE CASCADE,
    FOREIGN KEY (Id_grupo) REFERENCES Grupos(Id_grupo) ON DELETE CASCADE,
    FOREIGN KEY (Id_Ciclo) REFERENCES Ciclo(Id_Ciclo) ON DELETE CASCADE,
    FOREIGN KEY (Id_reunion) REFERENCES Reuniones(Id_reunion) ON DELETE SET NULL,
    FOREIGN KEY (Registrado_por) REFERENCES Usuarios(Id_usuario) ON DELETE SET NULL,
    
    -- Índices para mejorar rendimiento
    INDEX idx_miembro (Id_miembro),
    INDEX idx_grupo (Id_grupo),
    INDEX idx_ciclo (Id_Ciclo),
    INDEX idx_reunion (Id_reunion),
    INDEX idx_estado (Estado),
    INDEX idx_fecha (Fecha_ahorro),
    
    -- Evitar duplicados de ahorro para el mismo miembro en la misma reunión
    UNIQUE KEY unique_ahorro_reunion (Id_miembro, Id_reunion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Comentarios para documentación
ALTER TABLE Ahorros COMMENT = 'Tabla para registrar los ahorros de los miembros en cada reunión';
