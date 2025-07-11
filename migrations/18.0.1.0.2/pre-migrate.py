# -*- coding: utf-8 -*-

def migrate(cr, version):
    """
    Migración para permitir borrar productos sin afectar líneas existentes
    Actualiza las restricciones de clave foránea para usar ondelete='set null'
    """
    
    # Actualizar restricción en sale.order.line.product_id
    cr.execute("""
        ALTER TABLE sale_order_line 
        DROP CONSTRAINT IF EXISTS sale_order_line_product_id_fkey;
    """)
    
    cr.execute("""
        ALTER TABLE sale_order_line 
        ADD CONSTRAINT sale_order_line_product_id_fkey 
        FOREIGN KEY (product_id) REFERENCES product_product(id) 
        ON DELETE SET NULL;
    """)
    
    # Actualizar restricción en sale_order_chapter_line.product_id
    cr.execute("""
        ALTER TABLE sale_order_chapter_line 
        DROP CONSTRAINT IF EXISTS sale_order_chapter_line_product_id_fkey;
    """)
    
    cr.execute("""
        ALTER TABLE sale_order_chapter_line 
        ADD CONSTRAINT sale_order_chapter_line_product_id_fkey 
        FOREIGN KEY (product_id) REFERENCES product_product(id) 
        ON DELETE SET NULL;
    """)
    
    # Actualizar restricción en sale_order_chapter_template_line.product_id
    cr.execute("""
        ALTER TABLE sale_order_chapter_template_line 
        DROP CONSTRAINT IF EXISTS sale_order_chapter_template_line_product_id_fkey;
    """)
    
    cr.execute("""
        ALTER TABLE sale_order_chapter_template_line 
        ADD CONSTRAINT sale_order_chapter_template_line_product_id_fkey 
        FOREIGN KEY (product_id) REFERENCES product_product(id) 
        ON DELETE SET NULL;
    """)