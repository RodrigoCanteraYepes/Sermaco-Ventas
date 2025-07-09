# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    line_type = fields.Selection([
        ('alquiler', 'Alquiler'),
        ('montaje', 'Montaje'),
        ('portes', 'Portes'),
        ('otros', 'Otros Conceptos'),
    ], string='Tipo de Línea', default='otros')
    
    source_chapter_id = fields.Many2one(
        'sale.order.chapter',
        string='Capítulo de Origen',
        help='Capítulo desde el cual se transfirió esta línea'
    )
    
    chapter_name = fields.Char(
        string='Nombre del Capítulo',
        related='source_chapter_id.name',
        readonly=True
    )


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    chapter_ids = fields.One2many(
        'sale.order.chapter',
        'order_id',
        string='Capítulos del Presupuesto'
    )
    
    chapters_total = fields.Monetary(
        string='Total de Capítulos',
        compute='_compute_chapters_total',
        store=True,
        currency_field='currency_id'
    )
    
    new_chapter_name = fields.Char(
        string='Nombre del Nuevo Capítulo',
        help='Campo temporal para crear capítulos inline'
    )
    
    collapsed_chapters_in_lines = fields.Boolean(
        string='Capítulos Colapsados en Líneas',
        default=False,
        help='Indica si los capítulos están colapsados en las líneas del pedido'
    )
    
    @api.depends('chapter_ids.total_amount')
    def _compute_chapters_total(self):
        for order in self:
            order.chapters_total = sum(order.chapter_ids.mapped('total_amount'))
    
    def action_add_chapter(self):
        """Acción para añadir un nuevo capítulo"""
        self.ensure_one()
        return {
            'name': _('Añadir Capítulo'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.chapter',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_sequence': len(self.chapter_ids) * 10 + 10,
            }
        }
    
    def action_create_chapter_inline(self):
        """Crea un capítulo directamente desde el campo inline"""
        self.ensure_one()
        if not self.new_chapter_name:
            return
        
        # Crear el capítulo
        chapter = self.env['sale.order.chapter'].create({
            'order_id': self.id,
            'name': self.new_chapter_name,
            'sequence': (len(self.chapter_ids) + 1) * 10
        })
        
        # Limpiar el campo temporal
        self.new_chapter_name = False
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Éxito'),
                'message': _('Capítulo "%s" creado exitosamente') % chapter.name,
                'type': 'success',
            }
        }
    
    def action_transfer_all_chapters_to_lines(self):
        """Transfiere todas las líneas de capítulos a las líneas del pedido"""
        self.ensure_one()
        transferred_lines = 0
        
        for chapter in self.chapter_ids:
            for line in chapter.chapter_line_ids:
                # Preparar precio según el tipo de línea
                price_unit = line.price_unit
                name = line.name
                
                if line.line_type == 'alquiler' and line.price_per_period > 0:
                    price_unit = line.price_per_period * line.rental_periods
                    period_text = {
                        'day': 'día(s)',
                        'week': 'semana(s)',
                        'month': 'mes(es)'
                    }.get(line.rental_period_type, 'período(s)')
                    name = f"{line.name} - {line.rental_periods} {period_text} x {line.price_per_period}€"
                
                # Crear línea en sale.order.line
                sale_line_vals = {
                    'order_id': self.id,
                    'product_id': line.product_id.id if line.product_id else False,
                    'name': f"[{chapter.name}] {name}",
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id if line.product_uom else False,
                    'price_unit': price_unit,
                    'line_type': line.line_type,
                    'source_chapter_id': chapter.id,
                }
                
                self.env['sale.order.line'].create(sale_line_vals)
                transferred_lines += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Éxito'),
                'message': _('Se han transferido %d líneas a las líneas del pedido') % transferred_lines,
                'type': 'success',
            }
        }
    

    
    def action_load_template(self):
        """Abrir selector de plantillas para cargar en el presupuesto"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cargar Plantilla'),
            'res_model': 'sale.order.chapter.template',
            'view_mode': 'list',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'search_default_active': 1,
            },
            'domain': [('active', '=', True)]
        }