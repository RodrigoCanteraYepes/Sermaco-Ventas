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
    
    @api.depends('chapter_line_ids.price_subtotal')
    def _compute_total_amount(self):
        for chapter in self:
            chapter.total_amount = sum(chapter.chapter_line_ids.mapped('price_subtotal'))
    
    @api.model
    def create(self, vals):
        if 'name' not in vals:
            vals['name'] = _('Nuevo Capítulo')
        return super().create(vals)
    
    def action_add_suggested_products(self):
        """Añade productos sugeridos según el tipo de capítulo"""
        self.ensure_one()
        suggested_products = self._get_suggested_products()
        
        for product_data in suggested_products:
            self.env['sale.order.chapter.line'].create({
                'chapter_id': self.id,
                'product_id': product_data.get('product_id'),
                'name': product_data.get('name', ''),
                'product_uom_qty': product_data.get('qty', 1.0),
                'price_unit': product_data.get('price', 0.0),
                'line_type': product_data.get('line_type', 'alquiler'),
            })
    
    def _get_suggested_products(self):
        """Retorna productos sugeridos generales"""
        suggestions = [
            {
                'name': _('ALQUILER PLATAFORMA DE CREMALLERA BIMASTIL 30 MT'),
                'qty': 1.0,
                'price': 875.0,
                'line_type': 'alquiler'
            },
            {
                'name': _('SEGURO'),
                'qty': 1.0,
                'price': 60.0,
                'line_type': 'alquiler'
            },
            {
                'name': _('MONTAJE INICIAL BIMASTIL, ALTURA 30 MT'),
                'qty': 1.0,
                'price': 1050.0,
                'line_type': 'montaje'
            },
            {
                'name': _('DESMONTAJE FINAL BIMASTIL, ALTURA 30 MT'),
                'qty': 1.0,
                'price': 1050.0,
                'line_type': 'montaje'
            },
            {
                'name': _('PORTE DE ENTREGA (Se estiman 2 portes. Unidad 250 €)'),
                'qty': 2.0,
                'price': 250.0,
                'line_type': 'portes'
            },
            {
                'name': _('PORTE DE RETIRADA (Se estiman 2 portes. Unidad 250 €)'),
                'qty': 2.0,
                'price': 250.0,
                'line_type': 'portes'
            },
            {
                'name': _('GESTIÓN DE CARGA Y DESCARGA'),
                'qty': 1.0,
                'price': 50.0,
                'line_type': 'otros'
            },
            {
                'name': _('CERTIFICADO DE MONTAJE'),
                'qty': 1.0,
                'price': 150.0,
                'line_type': 'otros'
            }
        ]
        return suggestions
    
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
            self.env['sale.order.chapter.template.line'].create(template_line_vals)
        
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
    
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        domain=[('sale_ok', '=', True)]
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
    
    def unlink(self):
        """Control de permisos para eliminar líneas"""
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            raise AccessError(_('Solo los gerentes de ventas pueden eliminar líneas de capítulos.'))
        return super().unlink()
    
    def write(self, vals):
        """Control de permisos para modificar líneas"""
        if not self.env.user.has_group('sales_team.group_sale_salesman'):
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
                self.env['sale.order.chapter.line'].create(line_vals)
        
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
        string='Descripción'
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
    
    def action_apply_template(self):
        """Aplica la plantilla a un capítulo nuevo o existente"""
        self.ensure_one()
        
        # Verificar si hay un chapter_id en el contexto (cargar en capítulo existente)
        chapter_id = self.env.context.get('chapter_id')
        
        if chapter_id:
            # Cargar en capítulo existente
            chapter = self.env['sale.order.chapter'].browse(chapter_id)
            
            # Limpiar líneas existentes si el usuario lo confirma
            if chapter.chapter_line_ids:
                chapter.chapter_line_ids.unlink()
            
            # Crear las líneas del capítulo basadas en la plantilla
            for template_line in self.template_line_ids:
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
                self.env['sale.order.chapter.line'].create(line_vals)
            
            return {
                'type': 'ir.actions.act_window_close',
            }
        else:
            # Crear nuevo capítulo
            sale_order_id = self.env.context.get('active_id')
            if not sale_order_id:
                raise ValidationError(_('No se puede determinar el presupuesto de venta.'))
            
            # Crear el capítulo basado en la plantilla
            chapter_vals = {
                'name': self.name,
                'order_id': sale_order_id,
            }
            
            chapter = self.env['sale.order.chapter'].create(chapter_vals)
            
            # Crear las líneas del capítulo basadas en la plantilla
            for template_line in self.template_line_ids:
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
                self.env['sale.order.chapter.line'].create(line_vals)
            
            return {
                'type': 'ir.actions.act_window',
                'name': _('Capítulo creado desde plantilla'),
                'res_model': 'sale.order.chapter',
                'res_id': chapter.id,
                'view_mode': 'form',
                'target': 'current',
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
    ], string='Tipo de Línea', required=True)
    
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        domain=[('sale_ok', '=', True)]
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
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name
            self.price_unit = self.product_id.list_price
            self.product_uom = self.product_id.uom_id
            self.tax_ids = self.product_id.taxes_id
