from dataclasses import dataclass
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': 'localhost',
    'database': 'postgres',
    'user': 'postgres',
    'password': '123',
    'port': '5432',
    'client_encoding': 'UTF8'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@dataclass
class Product:
    id: Optional[int]
    article: str
    product_type_id: int
    product_type_name: Optional[str]
    name: str
    min_price: float
    main_material_id: int
    main_material_name: Optional[str]
    
    @staticmethod
    def get_all():
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                p.id, p.article, p.name, p.min_price,
                pt.id as product_type_id, pt.name as product_type_name,
                mt.id as main_material_id, mt.name as main_material_name
            FROM products p
            JOIN product_types pt ON p.product_type_id = pt.id
            JOIN material_types mt ON p.main_material_id = mt.id
            ORDER BY p.name
        """
        
        cur.execute(query)
        products = cur.fetchall()
        cur.close()
        conn.close()
        
        return products
    
    @staticmethod
    def get_by_id(product_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                p.id, p.article, p.name, p.min_price,
                pt.id as product_type_id, pt.name as product_type_name,
                mt.id as main_material_id, mt.name as main_material_name
            FROM products p
            JOIN product_types pt ON p.product_type_id = pt.id
            JOIN material_types mt ON p.main_material_id = mt.id
            WHERE p.id = %s
        """
        
        cur.execute(query, (product_id,))
        product = cur.fetchone()
        cur.close()
        conn.close()
        
        return product
    
    @staticmethod
    def create(article, product_type_id, name, min_price, main_material_id):

        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
            INSERT INTO products (article, product_type_id, name, min_price, main_material_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        
        cur.execute(query, (article, product_type_id, name, min_price, main_material_id))
        product_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return product_id
    
    @staticmethod
    def update(product_id, article, product_type_id, name, min_price, main_material_id):
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
            UPDATE products 
            SET article = %s, product_type_id = %s, name = %s, 
                min_price = %s, main_material_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        cur.execute(query, (article, product_type_id, name, min_price, 
                           main_material_id, product_id))
        conn.commit()
        cur.close()
        conn.close()
        
        return True

@dataclass
class ProductType:
    @staticmethod
    def get_all():
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT id, name, coefficient FROM product_types ORDER BY name")
        types = cur.fetchall()
        cur.close()
        conn.close()
        
        return types

@dataclass
class MaterialType:
    @staticmethod
    def get_all():
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT id, name, loss_percent FROM material_types ORDER BY name")
        materials = cur.fetchall()
        cur.close()
        conn.close()
        
        return materials

@dataclass
class Workshop:
    id: Optional[int]
    name: str
    type: str
    employees_count: int
    
    @staticmethod
    def get_all():
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id, name, type, employees_count 
            FROM workshops 
            ORDER BY name
        """)
        workshops = cur.fetchall()
        cur.close()
        conn.close()
        
        return workshops
    
    @staticmethod
    def get_all_workshops():
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT id, name, type, employees_count
            FROM workshops
            ORDER BY name
        """
        
        cur.execute(query)
        workshops = cur.fetchall()
        cur.close()
        conn.close()
        
        return workshops
    
    @staticmethod
    def get_by_product(product_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                w.id, w.name, w.type, w.employees_count,
                pw.hours, pw.id as product_workshop_id
            FROM workshops w
            JOIN product_workshops pw ON w.id = pw.workshop_id
            WHERE pw.product_id = %s
            ORDER BY w.name
        """
        
        cur.execute(query, (product_id,))
        workshops = cur.fetchall()
        cur.close()
        conn.close()
        
        return workshops
    
    @staticmethod
    def get_not_assigned_to_product(product_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT id, name, type, employees_count
            FROM workshops
            WHERE id NOT IN (
                SELECT workshop_id 
                FROM product_workshops 
                WHERE product_id = %s
            )
            ORDER BY name
        """
        
        cur.execute(query, (product_id,))
        workshops = cur.fetchall()
        cur.close()
        conn.close()
        
        return workshops
    
    @staticmethod
    def calculate_total_time(product_id):
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
            SELECT COALESCE(SUM(hours), 0) as total_hours
            FROM product_workshops
            WHERE product_id = %s
        """
        
        cur.execute(query, (product_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        return int(round(result[0])) if result and result[0] else 0


class ProductWorkshop:
    
    @staticmethod
    def add(product_id, workshop_id, hours):
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            query = """
                INSERT INTO product_workshops (product_id, workshop_id, hours)
                VALUES (%s, %s, %s)
                ON CONFLICT (product_id, workshop_id) 
                DO UPDATE SET hours = EXCLUDED.hours
            """
            cur.execute(query, (product_id, workshop_id, float(hours)))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def remove(product_id, workshop_id):
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            query = """
                DELETE FROM product_workshops 
                WHERE product_id = %s AND workshop_id = %s
            """
            cur.execute(query, (product_id, workshop_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def update_hours(product_id, workshop_id, hours):
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            query = """
                UPDATE product_workshops 
                SET hours = %s
                WHERE product_id = %s AND workshop_id = %s
            """
            cur.execute(query, (float(hours), product_id, workshop_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_by_product(product_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT pw.*, w.name as workshop_name, w.type as workshop_type
            FROM product_workshops pw
            JOIN workshops w ON pw.workshop_id = w.id
            WHERE pw.product_id = %s
            ORDER BY w.name
        """
        
        cur.execute(query, (product_id,))
        items = cur.fetchall()
        cur.close()
        conn.close()
        
        return items