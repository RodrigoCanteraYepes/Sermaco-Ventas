# -*- coding: utf-8 -*-

def migrate(cr, version):
    """
    Migración para limpiar datos incorrectos en campos boolean
    antes de la actualización del módulo
    """
    
    # Limpiar campo collapsed_chapters_in_lines en sale_order
    cr.execute("""
        UPDATE sale_order 
        SET collapsed_chapters_in_lines = FALSE 
        WHERE collapsed_chapters_in_lines::text = '[]' 
           OR collapsed_chapters_in_lines IS NULL
    """)
    
    # Limpiar campo is_collapsed en sale_order_chapter
    cr.execute("""
        UPDATE sale_order_chapter 
        SET is_collapsed = FALSE 
        WHERE is_collapsed::text = '[]' 
           OR is_collapsed IS NULL
    """)
    
    # Limpiar campo page_break_before en sale_order_chapter
    cr.execute("""
        UPDATE sale_order_chapter 
        SET page_break_before = TRUE 
        WHERE page_break_before::text = '[]' 
           OR page_break_before IS NULL
    """)
    
    print("Migración completada: campos boolean limpiados")