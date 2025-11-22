# 💰 Módulo de Ahorros - Instrucciones de Instalación y Uso

## 📋 Instalación de la Base de Datos

### Paso 1: Crear la tabla de Ahorros

Ejecuta el siguiente script SQL en tu base de datos MySQL:

```sql
-- Puedes encontrar el script completo en: crear_tabla_ahorros.sql
```

O ejecuta directamente desde la terminal de PowerShell:

```powershell
# Asegúrate de estar en el directorio del proyecto
mysql -u tu_usuario -p tu_base_de_datos < crear_tabla_ahorros.sql
```

## 🎯 Características del Módulo de Ahorros

### 1. 💵 Registrar Ahorro
- Selecciona una reunión específica
- Solo aparecen los miembros que **asistieron** (Presente o Tardanza)
- Registra el monto que cada miembro desea ahorrar
- Agrega observaciones opcionales
- Ver resumen: total, promedio, cantidad de ahorradores

### 2. 📋 Ver Ahorros
- Lista completa de todos los ahorros registrados
- Filtros por: Grupo, Ciclo, Estado (Activo/Devuelto)
- Estadísticas: Total activos, devueltos, general
- Detalles de cada ahorro con miembro, grupo, fecha, monto

### 3. 📊 Reportes
- **Por Miembro**: Cuánto ha ahorrado cada miembro (activo, devuelto, total)
- **Por Grupo**: Resumen de ahorros por grupo
- **Por Ciclo**: Ahorros en cada ciclo, pendientes de devolver y ya devueltos

### 4. 💸 Devolución de Ahorros
- **Devolución Individual**: Marca los ahorros de un miembro como devueltos
- **Devolución Masiva**: Devuelve todos los ahorros de un ciclo completo
- Se ejecuta al finalizar el ciclo
- Registra la fecha de devolución automáticamente

## 🔄 Flujo de Trabajo Recomendado

### Durante el Ciclo:

1. **Programar Reunión** → Asistencia y Multas > Reuniones
2. **Registrar Asistencia** → Asistencia y Multas > Asistencia
3. **Registrar Ahorros** → Ahorros > Registrar Ahorro
   - Solo los miembros que asistieron pueden ahorrar
   - Registra el monto que cada uno aporta

4. **Repetir** para cada reunión del ciclo

### Al Finalizar el Ciclo:

1. **Revisar Reportes** → Ahorros > Reportes
   - Verifica cuánto tiene ahorrado cada miembro
   
2. **Devolver Ahorros** → Ahorros > Devolución de Ahorros
   - Selecciona el ciclo finalizado
   - Devuelve individualmente o masivamente
   - Confirma que se entregó el dinero físicamente

## 💡 Ventajas del Sistema

✅ **Control Total**: Sabe exactamente cuánto ha ahorrado cada miembro
✅ **Transparencia**: Los miembros pueden ver su progreso
✅ **Seguridad**: Registro de quién registra y cuándo
✅ **Historial**: Mantiene registro de ciclos anteriores
✅ **Reportes**: Estadísticas detalladas por miembro, grupo y ciclo
✅ **Flexibilidad**: Permite ahorros opcionales (monto puede ser $0)
✅ **Auditoría**: Fecha de registro y devolución

## 📊 Estados de los Ahorros

- **Activo**: El ahorro está pendiente de devolver
- **Devuelto**: El ahorro ya fue entregado al miembro

## 🔐 Seguridad

- Los ahorros solo pueden registrarse para miembros que asistieron
- No se pueden duplicar ahorros en la misma reunión
- Cada acción registra quién la realizó y cuándo
- Los ahorros devueltos no se pueden modificar

## 📝 Notas Importantes

1. **Asistencia Primero**: Debes registrar la asistencia antes de poder registrar ahorros
2. **Montos Flexibles**: Cada miembro puede ahorrar montos diferentes
3. **Opcional**: Si un miembro asiste pero no ahorra, simplemente deja el monto en $0
4. **Devolución Cuidadosa**: Asegúrate de entregar el dinero físicamente antes de marcar como "Devuelto"
5. **Ciclo Completo**: Es mejor devolver todos los ahorros al finalizar el ciclo completo

## 🎓 Ejemplo de Uso

### Reunión Semana 1:
- María asiste → Ahorra $5.00
- Juan asiste → Ahorra $3.00
- Pedro asiste → Ahorra $0.00 (no ahorra esta semana)

### Reunión Semana 2:
- María asiste → Ahorra $5.00
- Juan no asiste → No puede ahorrar
- Pedro asiste → Ahorra $2.00

### Al finalizar el ciclo:
- María tiene: $10.00 (2 ahorros)
- Juan tiene: $3.00 (1 ahorro)
- Pedro tiene: $2.00 (1 ahorro)

**Total a devolver**: $15.00

## 🆘 Soporte

Si tienes algún problema o pregunta:
1. Verifica que la tabla `Ahorros` esté creada correctamente
2. Asegúrate de tener permisos de administrador
3. Revisa que las relaciones con otras tablas (Miembros, Grupos, Ciclos, Reuniones) existan

---

**¡El módulo de ahorros está listo para usar! 🎉**
