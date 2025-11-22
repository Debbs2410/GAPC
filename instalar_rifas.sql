-- Script para crear la tabla Rifas
CREATE TABLE IF NOT EXISTS Rifas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grupo_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    fecha DATE NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    descripcion TEXT,
    FOREIGN KEY (grupo_id) REFERENCES Grupos(Id_grupo)
);