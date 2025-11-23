-- Tabla para asignar los roles de directiva por grupo
CREATE TABLE IF NOT EXISTS Directiva_Grupo (
    id_directiva INT AUTO_INCREMENT PRIMARY KEY,
    id_grupo INT NOT NULL,
    id_miembro INT NOT NULL,
    rol_directiva ENUM('Presidenta', 'Secretaria', 'Tesorero') NOT NULL,
    fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_grupo) REFERENCES Grupos(Id_grupo) ON DELETE CASCADE,
    FOREIGN KEY (id_miembro) REFERENCES Miembros(id) ON DELETE CASCADE,
    UNIQUE KEY unique_rol_grupo (id_grupo, rol_directiva)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Cada grupo puede tener solo una presidenta, una secretaria y un tesorero activos a la vez.