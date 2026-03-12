# utils.py
import psycopg2
from models import DB_CONFIG

def calculate_raw_material(product_type_id, material_type_id, product_quantity, 
                          param1, param2):
    if product_quantity <= 0 or param1 <= 0 or param2 <= 0:
        return -1
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("SELECT coefficient FROM product_types WHERE id = %s", 
                   (product_type_id,))
        result = cur.fetchone()
        if not result:
            cur.close()
            conn.close()
            return -1
        product_coef = float(result[0])
        
        cur.execute("SELECT loss_percent FROM material_types WHERE id = %s", 
                   (material_type_id,))
        result = cur.fetchone()
        if not result:
            cur.close()
            conn.close()
            return -1
        material_loss = float(result[0])
        
        cur.close()
        conn.close()
        
        material_per_unit = param1 * param2 * product_coef
        
        total_material = material_per_unit * product_quantity * (1 + material_loss)

        return int(total_material) + (1 if total_material - int(total_material) > 0 else 0)
        
    except Exception as e:
        print(f"Ошибка при расчете сырья: {e}")
        return -1