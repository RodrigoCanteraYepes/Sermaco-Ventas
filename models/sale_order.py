# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    chapter_ids = fields.One2many(
        'sale.order.chapter',
        'sale_order_id',
        string='Capítulos del Presupuesto'
    )
    
    chapters_total = fields.Monetary(
        string='Total de Capítulos',
        compute='_compute_chapters_total',
        store=True,
        currency_field='currency_id'
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
                'default_sale_order_id': self.id,
                'default_sequence': len(self.chapter_ids) * 10 + 10,
            }
        }
    
    def action_transfer_all_chapters_to_lines(self):
        """Transfiere todas las líneas de capítulos a las líneas del pedido"""
        self.ensure_one()
        transferred_lines = 0
        
        for chapter in self.chapter_ids:
            for line in chapter.chapter_line_ids:
                # Crear línea en sale.order.line
                sale_line_vals = {
                    'order_id': self.id,
                    'product_id': line.product_id.id if line.product_id else False,
                    'name': f"[{chapter.name}] {line.name}",
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id if line.product_uom else False,
                    'price_unit': line.price_unit,
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
    
    def action_create_chapter_template(self):
        """Crea capítulos con plantillas predefinidas"""
        self.ensure_one()
        
        chapter_types = ['alquiler', 'montaje', 'portes', 'otros']
        
        for i, chapter_type in enumerate(chapter_types):
            # Verificar si ya existe un capítulo de este tipo
            existing_chapter = self.chapter_ids.filtered(lambda c: c.chapter_type == chapter_type)
            if not existing_chapter:
                chapter = self.env['sale.order.chapter'].create({
                    'sale_order_id': self.id,
                    'chapter_type': chapter_type,
                    'sequence': (i + 1) * 10
                })
                # Añadir productos sugeridos
                chapter.action_add_suggested_products()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Éxito'),
                'message': _('Plantilla de capítulos creada exitosamente'),
                'type': 'success',
            }
        }