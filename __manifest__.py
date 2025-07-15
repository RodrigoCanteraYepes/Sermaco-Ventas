# -*- coding: utf-8 -*-
{
    'name': 'Sale Order Chapters',
    'version': '18.0.1.0.62',
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
    'depends': ['sale', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/sale_order_chapter_data.xml',
        'views/sale_order_view.xml',
        'reports/sale_order_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'SermacoV1/static/src/css/sale_order_collapse.css',
            'SermacoV1/static/src/js/sale_order_collapse.js',
            'SermacoV1/static/src/xml/sale_order_collapse_templates.xml',
        ],
    },

    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
