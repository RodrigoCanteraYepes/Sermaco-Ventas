# -*- coding: utf-8 -*-
{
    'name': 'Sale Order Chapters',
    'version': '18.0.1.0.12',
    'category': 'Sales',
    'summary': 'Añade capítulos personalizados a los presupuestos de venta',
    'description': """
        Módulo que extiende la funcionalidad de los presupuestos de venta (sale.order)
        añadiendo una nueva pestaña "Capítulos del Presupuesto" que permite estructurar
        los productos en categorías predefinidas:
        - Alquiler
        - Montaje
        - Portes
        - Otros Conceptos
    """,
    'author': 'Tu Empresa',
    'website': 'https://www.tuempresa.com',
    'depends': ['base', 'sale', 'sale_management', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sale_order_chapter_data.xml',
        'views/sale_order_view.xml',
        'views/chapter_template_section_wizard_view.xml',
        'reports/sale_order_report.xml',
        'reports/sale_order_report_modern.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
