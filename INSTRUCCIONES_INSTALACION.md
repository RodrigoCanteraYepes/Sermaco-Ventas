# Instrucciones de Instalación - Sale Order Chapters

## Correcciones Realizadas

✅ **Assets declarados** en `__manifest__.py` para cargar CSS/JS
✅ **Referencias de módulo corregidas** en `sale_order_view.xml`
✅ **CSS simplificado** en `sale_order_report_modern.xml` para compatibilidad PDF

## Pasos para Instalar en AWS

### 1. Copiar el módulo al servidor
```bash
# Desde tu máquina local, copiar toda la carpeta SermacoV1 al servidor
scp -r SermacoV1/ usuario@IP_SERVIDOR:/opt/odoo18/custom_addons/sale_order_chapters/
```

### 2. Establecer permisos correctos
```bash
# En el servidor AWS
sudo chown -R odoo:odoo /opt/odoo18/custom_addons/sale_order_chapters/
sudo chmod -R 755 /opt/odoo18/custom_addons/sale_order_chapters/
```

### 3. Reiniciar Odoo
```bash
# Reiniciar el servicio de Odoo
sudo systemctl restart odoo
```

### 4. Actualizar el módulo en Odoo
1. Ir a **Aplicaciones** en Odoo
2. Buscar "Sale Order Chapters"
3. Hacer clic en **Actualizar**
4. Verificar que no hay errores en los logs

### 5. Verificar funcionamiento
1. Crear una nueva orden de venta
2. Agregar capítulos y líneas
3. Generar reporte PDF (tanto normal como moderno)
4. Verificar que los estilos se aplican correctamente

## Solución de Problemas

### Si los PDF no cargan estilos:
- Verificar logs de Odoo: `sudo tail -f /var/log/odoo/odoo.log`
- Comprobar versión de wkhtmltopdf: `wkhtmltopdf --version`
- Verificar permisos de archivos estáticos

### Si hay errores de módulo:
- Verificar que todas las dependencias están instaladas
- Comprobar sintaxis de archivos XML
- Revisar que el nombre del módulo coincide en todos los archivos

## Información Técnica

- **Nombre del módulo**: `sale_order_chapters`
- **Dependencias**: `base`, `sale`, `sale_management`, `mail`
- **Archivos estáticos**: CSS y JS en `/static/src/`
- **Reportes**: Dos versiones (normal y moderna) en `/reports/`