-- Tabla de Préstamos
CREATE TABLE IF NOT EXISTS Prestamos (
    Id_prestamo INT AUTO_INCREMENT PRIMARY KEY,
    Id_miembro INT NOT NULL,
    Id_grupo INT NOT NULL,
    Id_Ciclo INT NOT NULL,
    Monto_prestado DECIMAL(10,2) NOT NULL,
    Monto_disponible_ahorro DECIMAL(10,2) NOT NULL COMMENT 'Monto total ahorrado al momento del préstamo',
    Interes_porcentaje DECIMAL(5,2) DEFAULT 0.00 COMMENT 'Porcentaje de interés aplicado',
    Monto_interes DECIMAL(10,2) DEFAULT 0.00 COMMENT 'Monto del interés calculado',
    Monto_total DECIMAL(10,2) NOT NULL COMMENT 'Monto prestado + interés',
    Fecha_prestamo DATE NOT NULL,
    Fecha_vencimiento DATE NULL COMMENT 'Fecha límite para pagar',
    Estado ENUM('Pendiente', 'Pagado', 'Vencido') DEFAULT 'Pendiente',
    Forma_pago ENUM('Unico', 'Cuotas') DEFAULT 'Unico',
    Numero_cuotas INT DEFAULT 1,
    Monto_cuota DECIMAL(10,2) NULL,
    Descripcion TEXT NULL,
    Aprobado_por INT NOT NULL COMMENT 'Usuario que aprobó el préstamo',
    Fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Id_miembro) REFERENCES Miembros(id) ON DELETE CASCADE,
    FOREIGN KEY (Id_grupo) REFERENCES Grupos(Id_grupo) ON DELETE CASCADE,
    FOREIGN KEY (Id_Ciclo) REFERENCES Ciclo(Id_Ciclo) ON DELETE CASCADE,
    FOREIGN KEY (Aprobado_por) REFERENCES Usuarios(Id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla de Pagos de Préstamos
CREATE TABLE IF NOT EXISTS Pagos_Prestamos (
    Id_pago INT AUTO_INCREMENT PRIMARY KEY,
    Id_prestamo INT NOT NULL,
    Numero_cuota INT NOT NULL DEFAULT 1,
    Monto_pagado DECIMAL(10,2) NOT NULL,
    Fecha_pago DATE NOT NULL,
    Metodo_pago ENUM('Efectivo', 'Transferencia', 'Descuento_Ahorro') DEFAULT 'Efectivo',
    Observaciones TEXT NULL,
    Registrado_por INT NOT NULL,
    Fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Id_prestamo) REFERENCES Prestamos(Id_prestamo) ON DELETE CASCADE,
    FOREIGN KEY (Registrado_por) REFERENCES Usuarios(Id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Índices para optimizar consultas
CREATE INDEX idx_prestamo_miembro ON Prestamos(Id_miembro);
CREATE INDEX idx_prestamo_grupo ON Prestamos(Id_grupo);
CREATE INDEX idx_prestamo_ciclo ON Prestamos(Id_Ciclo);
CREATE INDEX idx_prestamo_estado ON Prestamos(Estado);
CREATE INDEX idx_pago_prestamo ON Pagos_Prestamos(Id_prestamo);
