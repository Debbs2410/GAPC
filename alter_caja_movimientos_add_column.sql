-- Script para agregar columnas faltantes a Caja_Movimientos
ALTER TABLE Caja_Movimientos
ADD COLUMN Registrado_por INT,
ADD COLUMN Observaciones VARCHAR(255);
