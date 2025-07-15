# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError


class SaleOrderChapter(models.Model):
    _name = 'sale.order.chapter'
    _description = 'Capítulos del Presupuesto de Venta'
    _order = 'sequence, id'

    name = fields.Char(
        string='Nombre del Capítulo',
        required=True
    )
    
    description = fields.Text(
        string='Descripción'
    )
    
    # Campo chapter_type eliminado - ahora se usa line_type en cada línea
    
    order_id = fields.Many2one(
        'sale.order',
        string='Presupuesto de Venta',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    chapter_line_ids = fields.One2many(
        'sale.order.chapter.line',
        'chapter_id',
        string='Líneas del Capítulo'
    )
    
    total_amount = fields.Monetary(
        string='Total del Capítulo',
        compute='_compute_total_amount',
        store=True,
        currency_field='currency_id'
    )
    
    manual_total = fields.Monetary(
        string='Precio Total Manual',
        currency_field='currency_id',
        help='Precio total manual del capítulo. Si se establece, se usará en lugar del total calculado.'
    )
    
    use_manual_total = fields.Boolean(
        string='Usar Precio Manual',
        default=False,
        help='Si está marcado, se usará el precio manual en lugar del total calculado'
    )
    
    currency_id = fields.Many2one(
        related='order_id.currency_id',
        store=True,
        readonly=True
    )
    
    is_collapsed = fields.Boolean(
        string='Capítulo Minimizado',
        default=False,
        help='Controla si el capítulo está minimizado en la vista (no afecta al PDF)'
    )
    
    page_break_before = fields.Boolean(
        string='Salto de Página Antes',
        default=True,
        help='Fuerza un salto de página antes de este capítulo en el PDF'
    )
    
    chapter_type = fields.Selection([
        ('alquiler', 'Alquiler'),
        ('montaje', 'Montaje'),
        ('portes', 'Portes'),
        ('otros', 'Otros Conceptos'),
        ('mixto', 'Mixto')
    ], string='Tipo de Capítulo', default='otros')
    
    @api.depends('chapter_line_ids.price_subtotal', 'manual_total', 'use_manual_total')
    def _compute_total_amount(self):
        for chapter in self:
            if chapter.use_manual_total and chapter.manual_total:
                chapter.total_amount = chapter.manual_total
            else:
                chapter.total_amount = sum(chapter.chapter_line_ids.mapped('price_subtotal'))
    

    
    @api.model
    def create(self, vals):
        if 'name' not in vals:
            vals['name'] = _('Nuevo Capítulo')
        return super().create(vals)
    

    
    def action_save_as_template(self):
        """Guarda el capítulo actual como plantilla"""
        self.ensure_one()
        
        if not self.chapter_line_ids:
            raise ValidationError(_('No se puede crear una plantilla de un capítulo vacío.'))
        
        # Crear la plantilla
        template_vals = {
            'name': f"{self.name} - Plantilla",
            'description': f"Plantilla creada desde el capítulo: {self.name}",
        }
        
        template = self.env['sale.order.chapter.template'].create(template_vals)
        
        # Crear las líneas de la plantilla
        for line in self.chapter_line_ids:
            template_line_vals = {
                'template_id': template.id,
                'sequence': line.sequence,
                'line_type': line.line_type,
                'product_id': line.product_id.id if line.product_id else False,
                'name': line.name,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id if line.product_uom else False,
                'price_unit': line.price_unit,                'tax_ids': [(6, 0, line.tax_ids.ids)],
            }
            self.env['sale.order.chapter.template.line'].with_context(creating_from_template=True).create(template_line_vals)
        
        # Forzar commit de la transacción
        self.env.cr.commit()
        
        # Mostrar mensaje de éxito
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Plantilla Creada'),
                'message': _('La plantilla "%s" se ha guardado correctamente y está disponible en el menú Plantillas de Capítulos.') % template.name,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_load_from_template(self):
        """Abre un wizard para cargar desde plantilla"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cargar desde Plantilla'),
            'res_model': 'sale.order.chapter.template',
            'view_mode': 'list,form',
            'target': 'new',
            'context': {
                'chapter_id': self.id,
            }
        }
    
    def unlink(self):
        """Control de permisos para eliminar capítulos"""
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            raise AccessError(_('Solo los gerentes de ventas pueden eliminar capítulos.'))
        return super().unlink()
    
    def write(self, vals):
        """Control de permisos para modificar capítulos"""
        if not self.env.user.has_group('sales_team.group_sale_salesman'):
            raise AccessError(_('No tienes permisos para modificar capítulos.'))
        return super().write(vals)
    
    def action_toggle_collapse(self):
        """Alterna el estado de minimizado del capítulo"""
        self.ensure_one()
        self.is_collapsed = not self.is_collapsed
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    



class SaleOrderChapterLine(models.Model):
    _name = 'sale.order.chapter.line'
    _description = 'Líneas de Capítulos del Presupuesto'
    _order = 'chapter_id, sequence, id'

    chapter_id = fields.Many2one(
        'sale.order.chapter',
        string='Capítulo',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    line_type = fields.Selection([
        ('alquiler', 'Alquiler'),
        ('montaje', 'Montaje'),
        ('portes', 'Portes'),
        ('otros', 'Otros Conceptos')
    ], string='Tipo de Línea', required=True, default='alquiler')
    
    is_fixed = fields.Boolean(
        string='Línea Fija',
        default=False,
        help='Indica si es una línea de sección que aparece en negrita sin otros campos'
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        domain=[('sale_ok', '=', True)],
        ondelete='set null'
    )
    
    name = fields.Char(
        string='Descripción',
        help='Descripción de la línea'
    )
    
    product_uom_qty = fields.Float(
        string='Cantidad',
        digits='Product Unit of Measure',
        default=1.0,
        required=True
    )
    
    product_uom = fields.Many2one(
        'uom.uom',
        string='Unidad de Medida'
    )
    
    price_unit = fields.Float(
        string='Precio Unitario',
        digits='Product Price',
        default=0.0
    )
    
    tax_ids = fields.Many2many(
        'account.tax',
        string='Impuestos',
        domain=[('type_tax_use', '=', 'sale')]
    )
    
    # Campos específicos para alquiler
    rental_period_type = fields.Selection([
        ('day', 'Día'),
        ('week', 'Semana'),
        ('month', 'Mes')
    ], string='Tipo de Período', default='day')
    
    rental_periods = fields.Float(
        string='Períodos de Alquiler',
        default=1.0,
        help='Número de días, semanas o meses según el tipo de período'
    )
    
    price_per_period = fields.Float(
        string='Precio por Período',
        digits='Product Price',
        default=0.0,
        help='Precio por día, semana o mes según el tipo de período'
    )
    
    price_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_amount',
        store=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        related='chapter_id.currency_id',
        store=True,
        readonly=True
    )
    
    @api.depends('product_uom_qty', 'price_unit', 'rental_periods', 'price_per_period', 'line_type')
    def _compute_amount(self):
        for line in self:
            if line.line_type == 'alquiler' and line.price_per_period > 0:
                # Para alquiler, usar precio por período * períodos * cantidad
                line.price_subtotal = line.product_uom_qty * line.rental_periods * line.price_per_period
            else:
                # Para otros tipos, usar cálculo tradicional
                line.price_subtotal = line.product_uom_qty * line.price_unit
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name
            self.product_uom = self.product_id.uom_id
            self.tax_ids = self.product_id.taxes_id
            
            if self.line_type == 'alquiler':
                # Para alquiler, configurar precio por período
                self.price_per_period = self.product_id.list_price
                self.price_unit = 0.0  # Limpiar precio unitario
            else:
                # Para otros tipos, usar precio unitario tradicional
                self.price_unit = self.product_id.list_price
                self.price_per_period = 0.0  # Limpiar precio por período
    
    @api.onchange('line_type')
    def _onchange_line_type(self):
        """Ajusta los campos de precio según el tipo de línea"""
        if self.line_type == 'alquiler':
            # Para alquiler, mover precio unitario a precio por período
            if self.price_unit > 0 and self.price_per_period == 0:
                self.price_per_period = self.price_unit
                self.price_unit = 0.0
        else:
            # Para otros tipos, mover precio por período a precio unitario
            if self.price_per_period > 0 and self.price_unit == 0:
                self.price_unit = self.price_per_period
                self.price_per_period = 0.0
    
    def action_transfer_to_order_lines(self):
        """Transfiere la línea del capítulo a las líneas del pedido"""
        self.ensure_one()
        sale_order = self.chapter_id.order_id
        
        # Preparar descripción y precio según el tipo de línea
        name = self.name
        price_unit = self.price_unit
        
        if self.line_type == 'alquiler' and self.price_per_period > 0:
            # Para alquiler, incluir información de períodos en la descripción
            period_text = {
                'day': 'día(s)',
                'week': 'semana(s)', 
                'month': 'mes(es)'
            }.get(self.rental_period_type, 'período(s)')
            
            name += f" - {self.rental_periods} {period_text} a {self.price_per_period}€ por {self.rental_period_type == 'day' and 'día' or self.rental_period_type == 'week' and 'semana' or 'mes'}"
            price_unit = self.rental_periods * self.price_per_period
        
        # Crear línea en sale.order.line
        if self.is_fixed:
            # Para líneas fijas (secciones), crear como sección
            sale_line_vals = {
                'order_id': sale_order.id,
                'display_type': 'line_section',
                'name': name,
                'product_uom_qty': 0.0,
                'price_unit': 0.0,
                'line_type': self.line_type,
                'source_chapter_id': self.chapter_id.id,
                'is_fixed': self.is_fixed,
            }
        else:
            # Para líneas normales
            sale_line_vals = {
                'order_id': sale_order.id,
                'product_id': self.product_id.id if self.product_id else False,
                'name': name,
                'product_uom_qty': self.product_uom_qty,
                'product_uom': self.product_uom.id if self.product_uom else False,
                'price_unit': price_unit,
                'tax_id': [(6, 0, self.tax_ids.ids)],
                'line_type': self.line_type,
                'source_chapter_id': self.chapter_id.id,
                'is_fixed': self.is_fixed,
            }
        
        self.env['sale.order.line'].create(sale_line_vals)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Éxito'),
                'message': _('Línea transferida a las líneas del pedido'),
                'type': 'success',
            }
        }
    
    @api.model
    def create(self, vals):
        """Control de permisos para crear líneas según tipo"""
        # Verificar si se está intentando crear una línea de alquiler o montaje
        line_type = vals.get('line_type')
        
        # Permitir creación durante la aplicación de plantillas o creación automática de capítulos
        if self.env.context.get('creating_from_template') or self.env.context.get('creating_default_sections'):
            return super().create(vals)
        
        # Evitar creación manual de líneas de alquiler y montaje
        if line_type in ('alquiler', 'montaje'):
            raise AccessError(_('No se pueden añadir nuevas líneas a las secciones de alquiler y montaje.'))
        
        return super().create(vals)
    
    def unlink(self):
        """Control de permisos para eliminar líneas según tipo y si es fija"""
        for line in self:
            # Las líneas fijas de alquiler y montaje no se pueden eliminar
            if line.is_fixed and line.line_type in ('alquiler', 'montaje'):
                raise AccessError(_('No se pueden eliminar las líneas de sección de alquiler y montaje.'))
            
            # Las líneas de datos de alquiler y montaje no se pueden eliminar
            if not line.is_fixed and line.line_type in ('alquiler', 'montaje'):
                raise AccessError(_('No se pueden eliminar las líneas de alquiler y montaje.'))
            
            # Para otras líneas, solo gerentes pueden eliminar
            if not self.env.user.has_group('sales_team.group_sale_manager'):
                raise AccessError(_('Solo los gerentes de ventas pueden eliminar líneas de capítulos.'))
        
        return super().unlink()
    
    def write(self, vals):
        """Control de permisos para modificar líneas según tipo y si es fija"""
        for line in self:
            # Las líneas fijas de alquiler y montaje no se pueden modificar (excepto en creación)
            if line.is_fixed and line.line_type in ('alquiler', 'montaje'):
                raise AccessError(_('No se pueden modificar las líneas de sección de alquiler y montaje.'))
            
            # Para líneas de datos de alquiler y montaje, solo se puede modificar el precio
            if not line.is_fixed and line.line_type in ('alquiler', 'montaje'):
                # Verificar qué campos se están intentando modificar
                forbidden_fields = set(vals.keys()) - {'price_unit'}
                if forbidden_fields:
                    raise AccessError(_('En las líneas de alquiler y montaje solo se puede modificar el precio unitario.'))
            
            # Para otras líneas, verificar permisos normales
            elif not self.env.user.has_group('sales_team.group_sale_salesman'):
                raise AccessError(_('No tienes permisos para modificar líneas de capítulos.'))
        
        return super().write(vals)


class ChapterTemplateWizard(models.TransientModel):
    _name = 'chapter.template.wizard'
    _description = 'Wizard para Aplicar Múltiples Plantillas'
    
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Presupuesto de Venta',
        required=True
    )
    
    template_ids = fields.Many2many(
        'sale.order.chapter.template',
        string='Plantillas a Aplicar',
        required=True
    )
    
    def action_apply_templates(self):
        """Aplica todas las plantillas seleccionadas"""
        self.ensure_one()
        
        created_chapters = []
        
        for template in self.template_ids:
            # Crear el capítulo basado en la plantilla
            chapter_vals = {
                'name': template.name,
                'order_id': self.sale_order_id.id,
                'is_collapsed': False,  # Empezar expandido
                'page_break_before': True,  # Salto de página por defecto
            }
            
            chapter = self.env['sale.order.chapter'].create(chapter_vals)
            created_chapters.append(chapter.id)
            
            # Crear las líneas del capítulo basadas en la plantilla
            for template_line in template.template_line_ids:
                line_vals = {
                    'chapter_id': chapter.id,
                    'sequence': template_line.sequence,
                    'line_type': template_line.line_type,
                    'product_id': template_line.product_id.id if template_line.product_id else False,
                    'name': template_line.name,
                    'product_uom_qty': template_line.product_uom_qty,
                    'product_uom': template_line.product_uom.id if template_line.product_uom else False,
                    'price_unit': template_line.price_unit,
                    'tax_ids': [(6, 0, template_line.tax_ids.ids)],
                }
                self.env['sale.order.chapter.line'].with_context(creating_from_template=True).create(line_vals)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Presupuesto de Venta'),
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    



class SaleOrderChapterTemplate(models.Model):
    _name = 'sale.order.chapter.template'
    _description = 'Plantillas de Capítulos'
    _order = 'name'
    
    name = fields.Char(
        string='Nombre de la Plantilla',
        required=True
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción detallada de la plantilla'
    )
    
    # Campo chapter_type eliminado - ahora se usa line_type en cada línea
    
    template_line_ids = fields.One2many(
        'sale.order.chapter.template.line',
        'template_id',
        string='Líneas de la Plantilla'
    )
    

    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Creado por',
        default=lambda self: self.env.user,
        readonly=True
    )
    
    @api.model
    def create(self, vals):
        """Crear plantilla con secciones fijas iniciales"""
        template = super().create(vals)
        template._create_default_sections()
        return template
    
    def _create_default_sections(self):
        """Crea las 4 secciones fijas por defecto"""
        self.ensure_one()
        
        # Crear líneas fijas para cada sección siempre
        sections = [
            {'line_type': 'alquiler', 'sequence': 100, 'name': 'Alquiler'},
            {'line_type': 'montaje', 'sequence': 200, 'name': 'Montaje'},
            {'line_type': 'portes', 'sequence': 300, 'name': 'Portes'},
            {'line_type': 'otros', 'sequence': 400, 'name': 'Otros Conceptos'},
        ]
        
        for section in sections:
            self.env['sale.order.chapter.template.line'].with_context(creating_default_sections=True).create({
                'template_id': self.id,
                'line_type': section['line_type'],
                'sequence': section['sequence'],
                'name': section['name'],
                'product_uom_qty': 1.0,
                'price_unit': 0.0,
                'is_fixed': True,
            })
    
    def action_apply_template(self):
        """Aplica la plantilla creando un capítulo con todas las líneas o cargando directamente en líneas del pedido"""
        self.ensure_one()
        
        # Obtener el ID del presupuesto desde el contexto
        sale_order_id = self.env.context.get('default_sale_order_id') or self.env.context.get('active_id')
        if not sale_order_id:
            raise ValidationError(_('No se puede determinar el presupuesto de venta.'))
        
        sale_order = self.env['sale.order'].browse(sale_order_id)
        
        # Verificar si debe cargar directamente en líneas del pedido
        load_to_order_lines = self.env.context.get('load_to_order_lines', False)
        
        if load_to_order_lines:
            return self._load_template_to_order_lines(sale_order)
        else:
            return self._load_template_to_chapter(sale_order)
    
    def _load_template_to_order_lines(self, sale_order):
        """Carga la plantilla directamente como líneas del pedido"""
        lines_created = 0
        
        # Copiar la descripción de la plantilla al campo order_description del presupuesto
        if self.description:
            # Si ya hay una descripción, agregar la nueva separada por líneas
            if sale_order.order_description:
                sale_order.order_description += "\n\n" + self.description
            else:
                sale_order.order_description = self.description
        
        # Crear una línea de título principal con el nombre de la plantilla en grande
        main_title_vals = {
            'order_id': sale_order.id,
            'display_type': 'line_section',
            'name': f"🔹 {self.name.upper()}",  # Nombre de la plantilla en mayúsculas con icono
            'product_uom_qty': 0.0,
            'price_unit': 0.0,
            'line_type': 'otros',  # Usar 'otros' para identificar títulos principales
            'is_fixed': True,
        }
        self.env['sale.order.line'].with_context(creating_from_template=True).create(main_title_vals)
        lines_created += 1
        
        # Crear líneas directamente en sale.order.line (incluyendo las secciones como separadores)
        for template_line in self.template_line_ids:
            # Para líneas fijas (secciones), crear como líneas de sección
            if template_line.is_fixed:
                line_vals = {
                    'order_id': sale_order.id,
                    'display_type': 'line_section',  # Crear como sección
                    'name': f"   ▪ {template_line.name}",  # Indentado con viñeta
                    'product_uom_qty': 0.0,  # Sin cantidad para secciones
                    'price_unit': 0.0,  # Sin precio para secciones
                    'line_type': template_line.line_type,  # Mantener el line_type original para subsecciones
                    'is_fixed': template_line.is_fixed,
                }
            else:
                # Construir el nombre incluyendo el nombre de la plantilla
                if template_line.product_id:
                    line_name = f"      • {template_line.product_id.display_name}"
                else:
                    line_name = f"      • {template_line.name}" if template_line.name else f"      • {template_line.line_type.title()}"
                
                line_vals = {
                    'order_id': sale_order.id,
                    'product_id': template_line.product_id.id if template_line.product_id else False,
                    'name': line_name,
                    'product_uom_qty': template_line.product_uom_qty,
                    'product_uom': template_line.product_uom.id if template_line.product_uom else False,
                    'price_unit': template_line.price_unit,
                    'line_type': template_line.line_type,
                    'is_fixed': template_line.is_fixed,
                    'tax_id': [(6, 0, template_line.tax_ids.ids)],
                }
            self.env['sale.order.line'].with_context(creating_from_template=True).create(line_vals)
            lines_created += 1
        
        # Mostrar mensaje de éxito y cerrar la ventana
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Plantilla Cargada'),
                'message': _('La plantilla "%s" se ha cargado correctamente con %d líneas en el pedido.') % (self.name, lines_created),
                'type': 'success',
                'next': {
                    'type': 'ir.actions.act_window_close',
                }
            }
        }
    
    def _load_template_to_chapter(self, sale_order):
        """Carga la plantilla como un nuevo capítulo"""
        # Crear un capítulo con el nombre de la plantilla
        chapter_vals = {
            'name': self.name,
            'description': self.description or '',
            'order_id': sale_order.id,
            'chapter_type': 'mixto',
        }
        
        chapter = self.env['sale.order.chapter'].create(chapter_vals)
        
        # Obtener tipos de línea únicos que no son fijas en la plantilla
        line_types_in_template = set()
        for template_line in self.template_line_ids:
            if not template_line.is_fixed:
                line_types_in_template.add(template_line.line_type)
        
        section_sequence = 10
        
        # Crear secciones para cada tipo de línea que existe en la plantilla
        if 'alquiler' in line_types_in_template:
            # Crear línea de sección fija "Alquiler" en azul
            self.env['sale.order.chapter.line'].with_context(creating_from_template=True).create({
                'chapter_id': chapter.id,
                'sequence': section_sequence,
                'line_type': 'alquiler',
                'is_fixed': True,
                'name': 'Alquiler',
                'product_uom_qty': 1.0,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'price_unit': 0.0,
            })
            section_sequence += 10
            
            # Crear línea de datos con el nombre de la plantilla
            self.env['sale.order.chapter.line'].with_context(creating_from_template=True).create({
                'chapter_id': chapter.id,
                'sequence': section_sequence,
                'line_type': 'alquiler',
                'is_fixed': False,
                'name': f'🔹 ALQUILER {self.name.upper()}',
                'product_uom_qty': 1.0,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'price_unit': 0.0,
            })
            section_sequence += 10
        
        if 'montaje' in line_types_in_template:
            # Crear línea de sección fija "Montaje" en azul
            self.env['sale.order.chapter.line'].with_context(creating_from_template=True).create({
                'chapter_id': chapter.id,
                'sequence': section_sequence,
                'line_type': 'montaje',
                'is_fixed': True,
                'name': 'Montaje',
                'product_uom_qty': 1.0,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'price_unit': 0.0,
            })
            section_sequence += 10
            
            # Crear línea de montaje con el nombre de la plantilla
            self.env['sale.order.chapter.line'].with_context(creating_from_template=True).create({
                'chapter_id': chapter.id,
                'sequence': section_sequence,
                'line_type': 'montaje',
                'is_fixed': False,
                'name': f'🔹 MONTAJE {self.name.upper()}',
                'product_uom_qty': 1.0,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'price_unit': 120.0,
            })
            section_sequence += 10
            
            # Crear línea de desmontaje con el nombre de la plantilla
            self.env['sale.order.chapter.line'].with_context(creating_from_template=True).create({
                'chapter_id': chapter.id,
                'sequence': section_sequence,
                'line_type': 'montaje',
                'is_fixed': False,
                'name': f'🔹 DESMONTAJE {self.name.upper()}',
                'product_uom_qty': 1.0,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'price_unit': 120.0,
            })
            section_sequence += 10
        
        if 'otros' in line_types_in_template:
            # Crear línea de sección fija "Otros Conceptos" en azul
            self.env['sale.order.chapter.line'].with_context(creating_from_template=True).create({
                'chapter_id': chapter.id,
                'sequence': section_sequence,
                'line_type': 'otros',
                'is_fixed': True,
                'name': 'Otros Conceptos',
                'product_uom_qty': 1.0,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'price_unit': 0.0,
            })
            section_sequence += 10
        
        # Crear todas las líneas de la plantilla en el capítulo (solo las que no son fijas)
        for template_line in self.template_line_ids:
            if not template_line.is_fixed:
                line_vals = {
                    'chapter_id': chapter.id,
                    'sequence': section_sequence,
                    'line_type': template_line.line_type,
                    'is_fixed': template_line.is_fixed,
                    'product_id': template_line.product_id.id if template_line.product_id else False,
                    'name': template_line.product_id.display_name if template_line.product_id else template_line.line_type.title(),
                    'product_uom_qty': template_line.product_uom_qty,
                    'product_uom': template_line.product_uom.id if template_line.product_uom else False,
                    'price_unit': template_line.price_unit,
                    'tax_ids': [(6, 0, template_line.tax_ids.ids)],
                }
                self.env['sale.order.chapter.line'].with_context(creating_from_template=True).create(line_vals)
                section_sequence += 10
        
        # Mostrar mensaje de éxito y cerrar la ventana
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Plantilla Cargada'),
                'message': _('La plantilla "%s" se ha cargado correctamente como un nuevo capítulo.') % self.name,
                'type': 'success',
                'next': {
                    'type': 'ir.actions.act_window_close',
                }
            }
        }
    
    def action_reload_template_view(self):
        """Actualiza y recarga la vista de la plantilla"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def unlink(self):
        """Control de permisos para eliminar plantillas"""
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            raise AccessError(_('Solo los gerentes de ventas pueden eliminar plantillas.'))
        return super().unlink()


class SaleOrderChapterTemplateLine(models.Model):
    _name = 'sale.order.chapter.template.line'
    _description = 'Líneas de Plantillas de Capítulos'
    _order = 'template_id, sequence, id'
    
    template_id = fields.Many2one(
        'sale.order.chapter.template',
        string='Plantilla',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    line_type = fields.Selection([
        ('alquiler', 'Alquiler'),
        ('montaje', 'Montaje'),
        ('portes', 'Portes'),
        ('otros', 'Otros Conceptos')
    ], string='Tipo de Sección', required=True, default='otros')
    
    is_fixed = fields.Boolean(
        string='Línea Fija',
        default=False,
        help='Si está marcado, esta línea aparecerá automáticamente en todas las plantillas nuevas'
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        domain=[('sale_ok', '=', True)],
        ondelete='set null'
    )
    
    name = fields.Text(
        string='Descripción',
        required=True
    )
    
    product_uom_qty = fields.Float(
        string='Cantidad',
        digits='Product Unit of Measure',
        default=1.0,
        required=True
    )
    
    product_uom = fields.Many2one(
        'uom.uom',
        string='Unidad de Medida'
    )
    
    price_unit = fields.Float(
        string='Precio Unitario',
        digits='Product Price',
        default=0.0
    )
    
    tax_ids = fields.Many2many(
        'account.tax',
        string='Impuestos',
        domain=[('type_tax_use', '=', 'sale')]
    )
    
    @api.model
    def create(self, vals):
        """Asegurar que el line_type se establece correctamente y la secuencia se ordena por tipo"""
        # Si se está creando desde una sección específica, establecer el line_type correcto
        if self.env.context.get('default_line_type'):
            vals['line_type'] = self.env.context.get('default_line_type')
        
        # Si no es una línea fija, calcular la secuencia para que aparezca después de la línea fija de su tipo
        if not vals.get('is_fixed', False) and vals.get('template_id') and vals.get('line_type'):
            template_id = vals['template_id']
            line_type = vals['line_type']
            
            # Buscar la secuencia base para este tipo de línea
            base_sequences = {
                'alquiler': 100,
                'montaje': 200,
                'portes': 300,
                'otros': 400,
            }
            
            # Encontrar la última secuencia para este tipo de línea
            existing_lines = self.search([
                ('template_id', '=', template_id),
                ('line_type', '=', line_type)
            ], order='sequence desc', limit=1)
            
            if existing_lines:
                vals['sequence'] = existing_lines.sequence + 1
            else:
                vals['sequence'] = base_sequences.get(line_type, 400) + 1
        
        return super().create(vals)
    
    @api.onchange('line_type')
    def _onchange_line_type(self):
        """Filtrar productos basado en el tipo de sección"""
        domain = [('sale_ok', '=', True)]
        
        if self.line_type == 'alquiler':
            domain.extend([
                '|', '|', '|',
                ('name', 'ilike', 'alquiler'),
                ('name', 'ilike', 'alqui'),
                ('categ_id.name', 'ilike', 'alquiler'),
                ('default_code', 'ilike', 'ALQ')
            ])
        elif self.line_type == 'montaje':
            domain.extend([
                '|', '|', '|', '|',
                ('name', 'ilike', 'montaje'),
                ('name', 'ilike', 'instalacion'),
                ('name', 'ilike', 'instalación'),
                ('categ_id.name', 'ilike', 'montaje'),
                ('default_code', 'ilike', 'MON')
            ])
        elif self.line_type == 'portes':
            domain.extend([
                '|', '|', '|', '|', '|',
                ('name', 'ilike', 'porte'),
                ('name', 'ilike', 'transporte'),
                ('name', 'ilike', 'envio'),
                ('name', 'ilike', 'envío'),
                ('categ_id.name', 'ilike', 'transporte'),
                ('default_code', 'ilike', 'POR')
            ])
        
        return {'domain': {'product_id': domain}}
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            # Actualizar nombre, precio, unidad y impuestos
            self.name = self.product_id.display_name
            self.price_unit = self.product_id.list_price
            self.product_uom = self.product_id.uom_id
            self.tax_ids = self.product_id.taxes_id
