# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrderChapter(models.Model):
    _name = 'sale.order.chapter'
    _description = 'Capítulos del Presupuesto de Venta'
    _order = 'sequence, id'

    name = fields.Char(
        string='Nombre del Capítulo',
        required=True
    )
    chapter_type = fields.Selection([
        ('alquiler', 'Alquiler'),
        ('montaje', 'Montaje'),
        ('portes', 'Portes'),
        ('otros', 'Otros Conceptos')
    ], string='Tipo de Capítulo', required=True, default='alquiler')
    
    sale_order_id = fields.Many2one(
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
        related='sale_order_id.currency_id',
        store=True,
        readonly=True
    )
    
    @api.depends('chapter_line_ids.price_subtotal')
    def _compute_total_amount(self):
        for chapter in self:
            chapter.total_amount = sum(chapter.chapter_line_ids.mapped('price_subtotal'))
    
    @api.model
    def create(self, vals):
        if 'name' not in vals and 'chapter_type' in vals:
            chapter_names = {
                'alquiler': _('Alquiler'),
                'montaje': _('Montaje'),
                'portes': _('Portes'),
                'otros': _('Otros Conceptos')
            }
            vals['name'] = chapter_names.get(vals['chapter_type'], _('Nuevo Capítulo'))
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
            })
    
    def _get_suggested_products(self):
        """Retorna productos sugeridos según el tipo de capítulo"""
        suggestions = {
            'alquiler': [
                {
                    'name': _('ALQUILER PLATAFORMA DE CREMALLERA BIMASTIL 30 MT'),
                    'qty': 1.0,
                    'price': 0.0
                }
            ],
            'montaje': [
                {
                    'name': _('MONTAJE INICIAL BIMASTIL'),
                    'qty': 1.0,
                    'price': 0.0
                }
            ],
            'portes': [
                {
                    'name': _('TRANSPORTE Y PORTES'),
                    'qty': 1.0,
                    'price': 0.0
                }
            ],
            'otros': [
                {
                    'name': _('OTROS CONCEPTOS'),
                    'qty': 1.0,
                    'price': 0.0
                }
            ]
        }
        return suggestions.get(self.chapter_type, [])


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
    
    @api.depends('product_uom_qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            line.price_subtotal = line.product_uom_qty * line.price_unit
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name
            self.price_unit = self.product_id.list_price
            self.product_uom = self.product_id.uom_id
    
    def action_transfer_to_order_lines(self):
        """Transfiere la línea del capítulo a las líneas del pedido"""
        self.ensure_one()
        sale_order = self.chapter_id.sale_order_id
        
        # Crear línea en sale.order.line
        sale_line_vals = {
            'order_id': sale_order.id,
            'product_id': self.product_id.id if self.product_id else False,
            'name': self.name,
            'product_uom_qty': self.product_uom_qty,
            'product_uom': self.product_uom.id if self.product_uom else False,
            'price_unit': self.price_unit,
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
