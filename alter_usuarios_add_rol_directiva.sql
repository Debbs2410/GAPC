-- Agrega la columna Rol_Directiva a la tabla Usuarios
ALTER TABLE Usuarios 
ADD COLUMN Rol_Directiva ENUM('Presidenta', 'Secretaria', 'Tesorero') NULL AFTER Rol;