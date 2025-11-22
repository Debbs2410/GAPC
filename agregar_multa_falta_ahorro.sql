-- Agregar tipo de multa para falta de ahorro mínimo

INSERT INTO Configuracion_Multas (Tipo_multa, Monto_default, Descripcion)
VALUES ('Falta_Ahorro', 1.00, 'Multa por no cumplir el monto mínimo de ahorro requerido')
ON DUPLICATE KEY UPDATE Tipo_multa = Tipo_multa;
