# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ChapterTemplateSectionWizard(models.TransientModel):
    _name = 'chapter.template.section.wizard'
    _description = 'Wizard para Añadir Secciones a Plantillas'
    
    template_id = fields.Many2one(
        'sale.order.chapter.template',
        string='Plantilla',
        required=True
    )
    
    section_name = fields.Char(
        string='Nombre de la Sección',
        required=True,
        help='Nombre personalizado para esta sección'
    )
    
    product_category_id = fields.Many2one(
        'product.category',
        string='Categoría de Productos',
        required=True,
        help='Categoría de productos que se mostrarán en esta sección'
    )
    
    product_ids = fields.Many2many(
        'product.product',
        string='Productos',
        domain="[('sale_ok', '=', True), ('categ_id', 'child_of', product_category_id)]",
        help='Selecciona los productos que quieres añadir a esta sección'
    )
    
    @api.onchange('product_category_id')
    def _onchange_product_category_id(self):
        """Limpiar productos seleccionados cuando cambie la categoría"""
        if self.product_category_id:
            self.product_ids = [(5, 0, 0)]  # Limpiar productos seleccionados
            return {
                'domain': {
                    'product_ids': [('sale_ok', '=', True), ('categ_id', 'child_of', self.product_category_id.id)]
                }
            }
    
    def action_add_section(self):
        """Añadir la sección con los productos seleccionados a la plantilla"""
        self.ensure_one()
        
        if not self.product_ids:
            raise ValidationError(_("Debes seleccionar al menos un producto para la sección."))
        
        # Obtener la siguiente secuencia disponible
        last_line = self.env['sale.order.chapter.template.line'].search([
            ('template_id', '=', self.template_id.id)
        ], order='sequence desc', limit=1)
        
        next_sequence = (last_line.sequence + 100) if last_line else 1000
        
        # Crear línea de sección (título)
        section_line = self.env['sale.order.chapter.template.line'].create({
            'template_id': self.template_id.id,
            'name': self.section_name,
            'sequence': next_sequence,
            'display_type': 'line_section',
            'is_fixed': True,  # Las secciones son líneas fijas
            'product_uom_qty': 0.0,
            'price_unit': 0.0,
        })
        
        # Crear líneas de productos
        for product in self.product_ids:
            next_sequence += 1
            self.env['sale.order.chapter.template.line'].create({
                'template_id': self.template_id.id,
                'product_id': product.id,
                'name': product.display_name,
                'sequence': next_sequence,
                'display_type': 'product',
                'is_fixed': False,
                'product_uom_qty': 1.0,
                'price_unit': product.list_price,
                'product_uom': product.uom_id.id,
                'tax_ids': [(6, 0, product.taxes_id.ids)],
            })
        
        # Mostrar mensaje de éxito
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sección Añadida'),
                'message': _('La sección "%s" se ha añadido correctamente con %d productos.') % (self.section_name, len(self.product_ids)),
                'type': 'success',
                'next': {
                    'type': 'ir.actions.act_window_close',
                }
            }
        }