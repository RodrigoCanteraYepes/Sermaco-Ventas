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
    
    is_fixed = fields.Boolean(
        string='Línea Fija',
        default=False,
        help='Indica si esta línea es fija y no se puede modificar'
    )
    
    is_section_collapsed = fields.Boolean(
        string='Sección Colapsada',
        default=False,
        help='Indica si esta sección está colapsada'
    )
    
    section_key = fields.Char(
        string='Clave de Sección',
        compute='_compute_section_key',
        help='Clave única para identificar la sección'
    )
    
    collapse_icon = fields.Char(
        string='Icono de Colapso',
        compute='_compute_collapse_icon',
        help='Icono que indica el estado de colapso de la sección'
    )
    
    is_line_visible = fields.Boolean(
        string='Línea Visible',
        compute='_compute_line_visibility',
        help='Determina si la línea debe ser visible según el estado de colapso de su sección'
    )
    
    # Redefinir product_id para permitir borrar productos
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        ondelete='set null',
        help='Producto asociado a la línea. Se puede borrar sin afectar la línea.'
    )
    
    @api.depends('line_type', 'name', 'display_type')
    def _compute_section_key(self):
        """Calcula una clave única para identificar la sección"""
        for line in self:
            if line.display_type == 'line_section' and line.is_fixed:
                line.section_key = f"{line.line_type}_{line.name}"
            else:
                line.section_key = False
    
    @api.depends('is_section_collapsed', 'display_type', 'is_fixed')
    def _compute_collapse_icon(self):
        """Calcula el icono de colapso según el estado de la sección"""
        for line in self:
            if line.display_type == 'line_section' and line.is_fixed:
                line.collapse_icon = '▶' if line.is_section_collapsed else '▼'
            else:
                line.collapse_icon = False
    
    @api.depends('line_type', 'display_type', 'is_fixed', 'order_id.collapsed_sections')
    def _compute_line_visibility(self):
        """Calcula si la línea debe ser visible según el estado de colapso de su sección"""
        import json
        
        for line in self:
            # Las secciones fijas siempre son visibles
            if line.display_type == 'line_section' and line.is_fixed:
                line.is_line_visible = True
            # Las líneas de productos dependen del estado de su sección padre
            elif not line.is_fixed and line.line_type:
                collapsed_sections = json.loads(line.order_id.collapsed_sections or '{}')
                section_key = f"{line.line_type}_{line.line_type.title()}"
                line.is_line_visible = section_key not in collapsed_sections
            else:
                line.is_line_visible = True
    
    def action_toggle_section_collapse(self):
        """Alterna el estado de colapso de una sección"""
        self.ensure_one()
        if not (self.display_type == 'line_section' and self.is_fixed):
            return
        
        import json
        
        # Obtener el estado actual de secciones colapsadas
        collapsed_sections = json.loads(self.order_id.collapsed_sections or '{}')
        
        # Alternar el estado de esta sección
        section_key = self.section_key
        if section_key in collapsed_sections:
            del collapsed_sections[section_key]
            collapsed = False
        else:
            collapsed_sections[section_key] = True
            collapsed = True
        
        # Guardar el nuevo estado
        self.order_id.collapsed_sections = json.dumps(collapsed_sections)
        
        # Actualizar el campo is_section_collapsed para todas las líneas de esta sección
        section_lines = self.order_id.order_line.filtered(
            lambda l: l.line_type == self.line_type
        )
        
        for line in section_lines:
            line.is_section_collapsed = collapsed
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def action_toggle_chapter_collapse(self):
        """Alterna el estado de colapso de un capítulo completo"""
        self.ensure_one()
        if not (self.display_type == 'line_section' and self.line_type == 'otros'):
            return
        
        import json
        
        # Obtener el estado actual de secciones colapsadas
        collapsed_sections = json.loads(self.order_id.collapsed_sections or '{}')
        
        # Crear clave única para el capítulo
        chapter_key = f"chapter_{self.source_chapter_id.id if self.source_chapter_id else self.name}"
        
        # Alternar el estado del capítulo
        if chapter_key in collapsed_sections:
            del collapsed_sections[chapter_key]
            collapsed = False
        else:
            collapsed_sections[chapter_key] = True
            collapsed = True
        
        # Guardar el nuevo estado
        self.order_id.collapsed_sections = json.dumps(collapsed_sections)
        
        # Actualizar todas las líneas del mismo capítulo
        chapter_lines = self.order_id.order_line.filtered(
            lambda l: l.source_chapter_id == self.source_chapter_id
        )
        
        for line in chapter_lines:
            line.is_section_collapsed = collapsed
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def write(self, vals):
        """Control de permisos para modificar líneas fijas"""
        for line in self:
            # Solo las secciones de alquiler y montaje son fijas e inmovibles
            if line.is_fixed and line.line_type in ('alquiler', 'montaje') and not self.env.context.get('creating_from_template'):
                # Permitir cambios en el estado de colapso
                allowed_fields = {'is_section_collapsed'}
                if not allowed_fields.intersection(set(vals.keys())):
                    from odoo.exceptions import AccessError
                    raise AccessError(_('Las secciones de alquiler y montaje no se pueden modificar, mover ni cambiar. Solo se pueden editar desde las plantillas de capítulos.'))
        return super().write(vals)
    
    def unlink(self):
        """Control de permisos para eliminar líneas fijas"""
        for line in self:
            # Solo las secciones de alquiler y montaje no se pueden eliminar
            if line.is_fixed and line.line_type in ('alquiler', 'montaje'):
                from odoo.exceptions import AccessError
                raise AccessError(_('Las secciones de alquiler y montaje no se pueden eliminar. Solo se pueden editar desde las plantillas de capítulos.'))
        return super().unlink()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    chapter_ids = fields.One2many(
        'sale.order.chapter',
        'order_id',
        string='Capítulos del Presupuesto'
    )
    
    order_description = fields.Text(
        string='Descripción del Presupuesto',
        help='Descripción adicional para el presupuesto'
    )
    
    chapters_total = fields.Monetary(
        string='Total de Capítulos',
        compute='_compute_chapters_total',
        store=True,
        currency_field='currency_id'
    )
    
    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note')
    ], string='Display Type', help='Campo auxiliar para compatibilidad de vista')
    
    is_fixed = fields.Boolean(
        string='Línea Fija',
        help='Campo auxiliar para compatibilidad de vista'
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
    
    collapsed_sections = fields.Text(
        string='Secciones Colapsadas',
        default='{}',
        help='JSON que almacena qué secciones están colapsadas por tipo'
    )
    
    is_section_collapsed = fields.Boolean(
        string='Sección Colapsada (Auxiliar)',
        default=False,
        help='Campo auxiliar para la vista - no se usa directamente'
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
                if line.is_fixed:
                    # Para líneas fijas (secciones), crear como sección
                    # Solo las secciones de alquiler y montaje permanecen fijas
                    is_fixed_section = line.line_type in ('alquiler', 'montaje')
                    sale_line_vals = {
                        'order_id': self.id,
                        'display_type': 'line_section',
                        'name': name,
                        'product_uom_qty': 0.0,
                        'price_unit': 0.0,
                        'line_type': line.line_type,
                        'source_chapter_id': chapter.id,
                        'is_fixed': is_fixed_section,
                    }
                else:
                    # Para líneas normales - todas son editables independientemente del tipo
                    sale_line_vals = {
                        'order_id': self.id,
                        'product_id': line.product_id.id if line.product_id else False,
                        'name': name,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id if line.product_uom else False,
                        'price_unit': price_unit,
                        'line_type': line.line_type,
                        'source_chapter_id': chapter.id,
                        'is_fixed': False,  # Todos los productos son editables
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
    

    
    def action_toggle_all_sections_collapse(self):
        """Alterna el estado de colapso de todas las secciones"""
        self.ensure_one()
        
        import json
        
        # Obtener el estado actual
        collapsed_sections = json.loads(self.collapsed_sections or '{}')
        
        # Determinar si colapsar o expandir todo
        section_lines = self.order_line.filtered(
            lambda l: l.display_type == 'line_section' and l.is_fixed
        )
        
        # Si hay alguna sección expandida, colapsar todas; si no, expandir todas
        has_expanded = any(line.section_key not in collapsed_sections for line in section_lines)
        
        if has_expanded:
            # Colapsar todas las secciones
            for line in section_lines:
                if line.section_key:
                    collapsed_sections[line.section_key] = True
        else:
            # Expandir todas las secciones
            collapsed_sections = {}
        
        # Guardar el nuevo estado
        self.collapsed_sections = json.dumps(collapsed_sections)
        
        # Actualizar todas las líneas
        for line in self.order_line:
            if line.display_type == 'line_section' and line.is_fixed:
                line.is_section_collapsed = line.section_key in collapsed_sections
            elif not line.is_fixed and line.line_type:
                # Buscar si la sección padre está colapsada
                section_key = f"{line.line_type}_{line.line_type.title()}"
                line.is_section_collapsed = section_key in collapsed_sections
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def action_load_template(self):
        """Abrir selector de plantillas para cargar en el presupuesto"""
        # Detectar si se llama desde líneas del pedido basándose en el contexto
        load_to_order_lines = self.env.context.get('load_to_order_lines', False)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cargar Plantilla'),
            'res_model': 'sale.order.chapter.template',
            'view_mode': 'list',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'search_default_active': 1,
                'load_to_order_lines': load_to_order_lines,
            },
            'domain': [('active', '=', True)]
        }
    
    def action_load_template_to_order_lines(self):
        """Abrir selector de plantillas para cargar directamente en líneas del pedido"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cargar Plantilla en Líneas del Pedido'),
            'res_model': 'sale.order.chapter.template',
            'view_mode': 'list',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'search_default_active': 1,
                'load_to_order_lines': True,
            },
            'domain': [('active', '=', True)]
        }