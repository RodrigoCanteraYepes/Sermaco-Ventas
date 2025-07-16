# -*- coding: utf-8 -*-

def migrate(cr, version):
    """
    Migración para manejar la transición del campo line_type a display_type
    en las tablas de líneas de capítulos y plantillas
    """
    
    # Verificar si existe la columna line_type en sale_order_chapter_line
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='sale_order_chapter_line' 
        AND column_name='line_type'
    """)
    
    if cr.fetchone():
        # Migrar datos de line_type a display_type en sale_order_chapter_line
        cr.execute("""
            UPDATE sale_order_chapter_line 
            SET display_type = CASE 
                WHEN line_type = 'otros' THEN 'line_section'
                WHEN line_type = 'producto' THEN 'product'
                ELSE 'product'
            END
            WHERE line_type IS NOT NULL
        """)
        
        # Actualizar is_fixed basado en line_type
        cr.execute("""
            UPDATE sale_order_chapter_line 
            SET is_fixed = CASE 
                WHEN line_type = 'otros' THEN TRUE
                ELSE FALSE
            END
            WHERE line_type IS NOT NULL
        """)
    
    # Verificar si existe la columna line_type en sale_order_chapter_template_line
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='sale_order_chapter_template_line' 
        AND column_name='line_type'
    """)
    
    if cr.fetchone():
        # Migrar datos de line_type a display_type en sale_order_chapter_template_line
        cr.execute("""
            UPDATE sale_order_chapter_template_line 
            SET display_type = CASE 
                WHEN line_type = 'otros' THEN 'line_section'
                WHEN line_type = 'producto' THEN 'product'
                ELSE 'product'
            END
            WHERE line_type IS NOT NULL
        """)
        
        # Actualizar is_fixed basado en line_type
        cr.execute("""
            UPDATE sale_order_chapter_template_line 
            SET is_fixed = CASE 
                WHEN line_type = 'otros' THEN TRUE
                ELSE FALSE
            END
            WHERE line_type IS NOT NULL
        """)
    
    print("Migración completada: transición de line_type a display_type")