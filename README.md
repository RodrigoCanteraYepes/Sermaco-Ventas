# Sale Order Chapters - Módulo de Capítulos para Presupuestos

## Descripción

Este módulo personalizado para Odoo 18.0.1.0.0 Community Edition extiende la funcionalidad de los presupuestos de venta (`sale.order`) añadiendo una nueva pestaña "Capítulos del Presupuesto" que permite estructurar los productos en categorías predefinidas.

## Versión Corregida

Esta versión incluye todas las correcciones identificadas en la revisión inicial:
- ✅ Nomenclatura de campos unificada
- ✅ Campos faltantes implementados
- ✅ Vistas XML completas y funcionales
- ✅ Manifest corregido
- ✅ Traducciones actualizadas
- ✅ Permisos de seguridad refinados

## Características Principales

### 🎯 Funcionalidades

- **Nueva pestaña "Capítulos del Presupuesto"** en el formulario de `sale.order`
- **Cuatro tipos de capítulos predefinidos:**
  - Alquiler
  - Montaje
  - Portes
  - Otros Conceptos
- **Gestión de líneas por capítulo** con productos, cantidades y precios
- **Productos sugeridos** para cada tipo de capítulo
- **Transferencia automática** de líneas de capítulos a líneas del pedido
- **Plantillas predefinidas** para crear todos los capítulos de una vez
- **Cálculo automático** de totales por capítulo
- **Interfaz intuitiva** con botones de acción específicos
- **Interfaz completa**: Botones de acción, confirmaciones, y navegación intuitiva
- **Cálculos automáticos**: Totales por capítulo y total general
- **Secuenciación**: Orden personalizable de capítulos y líneas

### 🌐 Multilenguaje

- Soporte completo para español e inglés
- Todas las etiquetas y campos están preparados para traducción
- Archivo de traducción incluido (`i18n/es.po`)

## Estructura del Módulo

```
sale_order_chapters/
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── sale_order_chapter.py
│   └── sale_order.py
├── views/
│   └── sale_order_view.xml
├── security/
│   └── ir.model.access.csv
├── i18n/
│   └── es.po
└── README.md
```

## Modelos Implementados

### 1. `sale.order.chapter`
**Descripción:** Modelo principal que representa un capítulo del presupuesto.

**Campos principales:**
- `name`: Nombre del capítulo (Char)
- `chapter_type`: Tipo de capítulo (Selection: Alquiler, Montaje, Portes, Otros)
- `sale_order_id`: Relación con el presupuesto de venta (Many2one)
- `sequence`: Orden de visualización (Integer)
- `chapter_line_ids`: Líneas del capítulo (One2many)
- `total_amount`: Total calculado del capítulo (Monetary)
- `currency_id`: Moneda (Many2one)

**Métodos principales:**
- `action_add_suggested_products()`: Añade productos sugeridos según el tipo
- `_get_suggested_products()`: Retorna productos sugeridos por tipo

### 2. `sale.order.chapter.line`
**Descripción:** Líneas individuales dentro de cada capítulo.

**Campos principales:**
- `chapter_id`: Relación con el capítulo (Many2one)
- `sequence`: Orden de la línea (Integer)
- `product_id`: Producto (Many2one)
- `name`: Descripción (Text)
- `product_uom_qty`: Cantidad (Float)
- `product_uom`: Unidad de medida (Many2one)
- `price_unit`: Precio unitario (Float)
- `price_subtotal`: Subtotal calculado (Monetary)
- `currency_id`: Moneda (Many2one)

**Métodos principales:**
- `action_transfer_to_order_lines()`: Transfiere la línea a las líneas del pedido

### 3. `sale.order` (Herencia)
**Descripción:** Extensión del modelo de presupuesto de venta.

**Campos añadidos:**
- `chapter_ids`: Relación con los capítulos
- `chapters_total`: Total de todos los capítulos (Monetary)

**Métodos añadidos:**
- `action_add_chapter()`: Abre formulario para añadir nuevo capítulo
- `action_transfer_all_chapters_to_lines()`: Transfiere todas las líneas de capítulos
- `action_create_chapter_template()`: Crea plantilla con todos los tipos de capítulos

## Vistas Implementadas

### 1. Vista de Formulario de Capítulo
- Formulario completo para gestionar capítulos
- Notebook con líneas del capítulo editables
- Botón para añadir productos sugeridos

### 2. Vista de Lista de Capítulos
- Lista ordenable con handle de secuencia
- Visualización de totales por capítulo

### 3. Herencia de Vista de Sale Order
- Nueva pestaña "Capítulos del Presupuesto"
- Botones de acción:
  - "Añadir Capítulo"
  - "Crear Plantilla de Capítulos"
  - "Transferir Todo a Líneas del Pedido"
- Resumen de totales

## Instalación

### Requisitos Previos
- Odoo 18.0.1.0.0 Community Edition
- Módulos base: `sale`, `sale_management`

### Pasos de Instalación

1. **Copiar el módulo:**
   ```bash
   cp -r sale_order_chapters /path/to/odoo/addons/
   ```

2. **Actualizar lista de aplicaciones:**
   ```bash
   ./odoo-bin -u all -d tu_base_de_datos
   ```
   - O desde la interfaz: Aplicaciones > "Actualizar lista de aplicaciones"

3. **Instalar el módulo:**
   - Buscar "Sale Order Chapters"
   - Hacer clic en "Instalar"

4. **Verificar instalación:**
   - Ir a Ventas > Presupuestos
   - Crear o editar un presupuesto
   - Verificar que aparece la pestaña "Capítulos del Presupuesto"
   - Verificar que las traducciones se carguen correctamente

## Guía de Uso

### Gestión Básica
1. **Crear o editar un pedido de venta**
2. **Navegar a la pestaña "Capítulos del Presupuesto"**
3. **Usar "Añadir Capítulo" para crear capítulos individuales**
4. **Usar "Crear Plantilla de Capítulos" para generar los 4 tipos predefinidos**

### Gestión de Líneas
1. **Hacer doble clic en un capítulo para editarlo**
2. **Añadir líneas manualmente o usar "Añadir Productos Sugeridos"**
3. **Configurar cantidades, precios y descripciones**
4. **Usar "Transferir" para mover líneas individuales al pedido principal**

### Transferencia Masiva
1. **Usar "Transferir Todo a Líneas del Pedido" para mover todas las líneas**
2. **Confirmar la acción en el diálogo de confirmación**
3. **Las líneas se añadirán al pedido principal manteniendo la organización**

### Productos Sugeridos por Capítulo

**Alquiler:**
- ALQUILER PLATAFORMA DE CREMALLERA BIMASTIL 30 MT

**Montaje:**
- MONTAJE INICIAL BIMASTIL

**Portes:**
- TRANSPORTE Y PORTES

**Otros Conceptos:**
- OTROS CONCEPTOS

## Personalización

### Añadir Nuevos Tipos de Capítulos

En `models/sale_order_chapter.py`, modificar la selección `chapter_type`:

```python
chapter_type = fields.Selection([
    ('alquiler', 'Alquiler'),
    ('montaje', 'Montaje'),
    ('portes', 'Portes'),
    ('otros', 'Otros Conceptos'),
    ('nuevo_tipo', 'Nuevo Tipo'),  # Añadir aquí
], string='Tipo de Capítulo', required=True, default='alquiler')
```

### Modificar Productos Sugeridos

En el método `_get_suggested_products()`, añadir o modificar las sugerencias:

```python
suggestions = {
    'alquiler': [
        {
            'name': _('NUEVO PRODUCTO DE ALQUILER'),
            'qty': 1.0,
            'price': 100.0
        }
    ],
    # ... resto de tipos
}
```

## Seguridad

El módulo incluye permisos para:
- **Vendedores** (`sales_team.group_sale_salesman`): Lectura, escritura, creación y eliminación
- **Gerentes de Ventas** (`sales_team.group_sale_manager`): Permisos completos

## Funcionalidades Técnicas

### Métodos Principales
- `action_add_chapter()`: Abre formulario para nuevo capítulo
- `action_create_chapter_template()`: Crea los 4 tipos de capítulos predefinidos
- `action_transfer_all_chapters_to_lines()`: Transfiere todas las líneas al pedido
- `action_add_suggested_products()`: Añade productos sugeridos por tipo
- `_get_suggested_products()`: Lógica de productos sugeridos (personalizable)

### Validaciones y Cálculos
- Cálculo automático de subtotales por línea
- Cálculo automático de totales por capítulo
- Cálculo del total general de capítulos
- Validación de campos obligatorios
- Onchange automático al seleccionar productos

## Compatibilidad

- ✅ Odoo 18.0.1.0.0 Community Edition
- ✅ Módulos requeridos: `sale`, `sale_management`
- ✅ Compatible con instalaciones estándar
- ✅ No requiere módulos de terceros

## Estado del Módulo

**Estado**: ✅ **FUNCIONAL Y CORREGIDO**
- Todos los errores identificados han sido corregidos
- Interfaz completa implementada
- Traducciones actualizadas
- Listo para producción

## Soporte y Contribuciones

Para reportar errores o solicitar nuevas funcionalidades, por favor contacta al equipo de desarrollo.

## Licencia

Este módulo está licenciado bajo LGPL-3.

---

**Versión:** 18.0.1.0.0  
**Autor:** Tu Empresa  
**Fecha:** 2024