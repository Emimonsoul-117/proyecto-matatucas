# Matatucas LMS - Errores Comunes y Soluciones

## Errores Frecuentes

### 1. MySQL no arranca (XAMPP)
**Síntoma**: "MySQL shutdown unexpectedly" en XAMPP
**Causa**: Archivos `ib_logfile` corruptos por apagado brusco
**Solución**:
1. Renombrar `C:\xampp\mysql\data` → `data_old`
2. Crear nueva carpeta `data`
3. Copiar contenido de `C:\xampp\mysql\backup` → nueva `data`
4. Copiar `matatucas_db/` e `ibdata1` de `data_old` → nueva `data`
5. Reiniciar MySQL

### 2. BuildError: Could not build url for endpoint
**Causa**: Referencia a endpoint eliminado o renombrado en template/código
**Solución**: Buscar con grep el endpoint viejo en templates y rutas, reemplazar

### 3. App se cuelga al iniciar (sin output)
**Causa**: Funciones `_ensure_*` en `__init__.py` ejecutando ALTER TABLE cuando MySQL está bloqueado
**Diagnóstico**: Comentar temporalmente las funciones `_ensure_*` para aislar
**Solución**: Reiniciar MySQL, verificar conexión con script simple

### 4. HTTPS requerido por Microsoft SSO
**Causa**: Azure AD rechaza redirect URIs con `http://` (excepto localhost)
**Solución**: `ssl_context='adhoc'` en `app.run()` + `pip install pyOpenSSL`

### 5. Procesos Python zombis bloqueando puerto
**Solución**: `taskkill /F /IM python.exe /T` antes de reiniciar

### 6. pip dependency resolver warnings
**Síntoma**: "ERROR: pip's dependency resolver does not currently take into account..."
**Realidad**: Es solo un warning, no un error real. Si dice "Successfully installed", todo está bien.

## Debugging Tips
- Activar debug: `app.run(debug=True)` (NUNCA en producción)
- Ver logs MySQL: `C:\xampp\mysql\data\mysql_error.log`
- Verificar puerto 3306: `netstat -ano | findstr :3306`
- Probar conexión DB directa: `python -c "import mysql.connector; conn = mysql.connector.connect(user='root', password='', host='localhost', database='Matatucas_db'); print('OK'); conn.close()"`
