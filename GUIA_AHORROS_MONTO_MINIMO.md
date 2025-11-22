# 💰 Sistema de Ahorros con Monto Mínimo - Guía de Instalación

## 🚀 Instalación Rápida

### Paso 1: Ejecutar Script de Instalación

En la terminal PowerShell (con el entorno virtual activado):

```powershell
cd C:\Users\MINEDUCYT\Downloads\PROYECTO\GAPC
.\.venv\Scripts\Activate.ps1
python instalar_config_ahorros.py
```

Esto creará:
- ✅ Tabla `Configuracion_Ahorros`
- ✅ Configuración por defecto (monto mínimo: $2.00)
- ✅ Tipo de multa "Falta_Ahorro"

### Paso 2: Reiniciar Streamlit

```powershell
streamlit run app.py
```

---

## 📋 Características Implementadas

### 1. **Monto Mínimo Configurable**
- Establece cuánto debe ahorrar cada miembro por reunión
- Configuración global para todo el sistema
- Ajustable en: **Ahorros > Configuración**

### 2. **Validación Automática**
Al registrar ahorros, el sistema:
- ✅ Muestra el monto mínimo requerido
- ⚠️ Advierte si no se cumple el mínimo
- ❌ Indica quiénes recibirán multa
- 📊 Resumen con cantidad de personas a multar

### 3. **Multas Automáticas**
Si un miembro asiste pero:
- **No ahorra nada ($0)** → Multa
- **Ahorra menos del mínimo** → Multa
- **Ahorra el mínimo o más** → Sin multa

La multa se aplica al hacer clic en **"⚠️ Aplicar Multas"**

### 4. **Flexibilidad**
Puedes:
- Desactivar las multas (solo advertencia)
- Cambiar el monto de la multa
- Ajustar el monto mínimo en cualquier momento

---

## 🔄 Flujo de Trabajo

### Durante una Reunión:

1. **Registrar Asistencia** (Asistencia y Multas)
   - Solo presentes pueden ahorrar

2. **Registrar Ahorros** (Ahorros > Registrar Ahorro)
   - Seleccionar reunión
   - El sistema muestra: "Monto mínimo: $2.00"
   - Ingresar monto para cada miembro
   - Si no cumple → Aparece advertencia ⚠️

3. **Guardar Ahorros**
   - Click en "💾 Guardar Ahorros"

4. **Aplicar Multas** (Opcional pero recomendado)
   - Si hay personas que no cumplieron el mínimo
   - Click en "⚠️ Aplicar Multas"
   - El sistema genera multas automáticas

---

## ⚙️ Configuración

### Ajustar Monto Mínimo:

1. Ve a: **Ahorros > Configuración**
2. Configura:
   - **Monto Mínimo**: Ej: $2.00, $3.00, $5.00
   - **Aplicar Multa**: Activar/Desactivar
   - **Monto de Multa**: Ej: $1.00, $2.00
3. Click en "💾 Guardar Configuración"

### Ejemplos de Configuración:

**Configuración Estricta:**
- Monto mínimo: $5.00
- Aplicar multa: ✅ Sí
- Monto multa: $2.00

**Configuración Flexible:**
- Monto mínimo: $2.00
- Aplicar multa: ❌ No (solo advertencia)

**Sin Monto Mínimo:**
- Monto mínimo: $0.00
- Aplica multa: ❌ No

---

## 📊 Reportes

El sistema muestra:
- Total ahorrado por miembro
- Quiénes cumplen/no cumplen el mínimo
- Multas aplicadas por no ahorrar
- Estadísticas por grupo y ciclo

---

## 🎯 Casos de Uso

### Caso 1: Miembro Cumple
- Monto mínimo: $2.00
- Juan ahorra: $3.00
- ✅ **Sin multa**

### Caso 2: Miembro No Cumple
- Monto mínimo: $2.00
- María ahorra: $1.00
- ⚠️ **Multa de $1.00**

### Caso 3: Miembro No Ahorra
- Monto mínimo: $2.00
- Pedro ahorra: $0.00
- ❌ **Multa de $1.00**

### Caso 4: Miembro Justifica (Opcional)
- Puedes agregar observación: "Emergencia familiar"
- Y no aplicar la multa manualmente

---

## 💡 Recomendaciones

1. **Define el monto desde el inicio del ciclo**
2. **Comunica claramente a los miembros** el monto mínimo requerido
3. **Aplica multas consistentemente** para mantener el ahorro activo
4. **Revisa reportes** para ver quiénes cumplen regularmente
5. **Ajusta el monto** según la capacidad del grupo

---

## 🆘 Solución de Problemas

### "No aparece la pestaña Configuración"
→ Ejecuta `python instalar_config_ahorros.py`

### "Error al guardar ahorros"
→ Verifica que la tabla `Configuracion_Ahorros` exista

### "No se aplican las multas"
→ Verifica que "Aplica_multa" esté en 1 (activado)

### "Quiero cambiar el monto después"
→ Ve a Ahorros > Configuración y ajusta cuando quieras

---

## 📝 Notas Importantes

- ⚠️ **Las multas son opcionales**: Puedes registrar ahorros sin aplicar multas
- 💾 **Guarda primero, multa después**: Son dos pasos separados
- 🔄 **No se duplican multas**: Si ya existe una multa para esa reunión, no se crea otra
- 📊 **Todo queda registrado**: Quién aplicó la multa, cuándo y por qué

---

¡El sistema está listo para promover el ahorro constante en tu organización! 💪💰
