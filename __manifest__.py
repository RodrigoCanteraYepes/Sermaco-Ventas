# -*- coding: utf-8 -*-
{
    'name': 'Sale Order Chapters',
    'version': '18.0.1.0.15',
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
        'views/sale_order_view.xml',
        'reports/sale_order_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
