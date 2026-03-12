import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os

DB_CONFIG = {
    'host': 'localhost',
    'database': 'postgres',
    'user': 'postgres',
    'password': '123',
    'port': '5432',
    'client_encoding': 'UTF8',
    'options': '-c client_encoding=UTF8'
}

def connect_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        conn.set_client_encoding('UTF8')
        
        print("Подключение к БД успешно установлено")
        return conn
    except UnicodeDecodeError as e:
        print(f"Ошибка кодировки при подключении: {e}")
        print("Пробуем альтернативный способ подключения...")
        
        alt_config = {
            'host': 'localhost',
            'database': 'furniture_company',
            'user': 'postgres',
            'password': 'your_password', 
            'port': '5432'
        }
        try:
            conn = psycopg2.connect(**alt_config)
            cursor = conn.cursor()
            cursor.execute("SET client_encoding TO 'UTF8';")
            cursor.close()
            print("Подключение с альтернативным способом успешно")
            return conn
        except Exception as e2:
            print(f"Альтернативное подключение тоже не удалось: {e2}")
            return None
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        return None

def check_database_exists(conn):
    """Проверка существования базы данных и таблиц"""
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        if tables:
            print("Существующие таблицы в БД:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("В БД нет таблиц. Сначала выполните database_schema.sql")
        
        cursor.close()
        return True
    except Exception as e:
        print(f"Ошибка при проверке БД: {e}")
        return False

def import_material_types(conn):
    """Импорт типов материалов"""
    try:
        df = pd.read_excel('data/Material_type_import.xlsx', engine='openpyxl')

        df.columns = ['name', 'loss_percent']
        
        cursor = conn.cursor()

        cursor.execute("TRUNCATE material_types RESTART IDENTITY CASCADE;")

        data = [(row['name'], float(row['loss_percent'])) 
                for _, row in df.iterrows()]

        execute_values(cursor, 
            "INSERT INTO material_types (name, loss_percent) VALUES %s",
            data)
        
        conn.commit()
        print(f"✅ Импортировано {len(data)} типов материалов")
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при импорте типов материалов: {e}")
        raise e

def import_product_types(conn):
    try:
        df = pd.read_excel('data/Product_type_import.xlsx', engine='openpyxl')
        df.columns = ['name', 'coefficient']
        
        cursor = conn.cursor()
        
        cursor.execute("TRUNCATE product_types RESTART IDENTITY CASCADE;")
        
        data = [(row['name'], float(row['coefficient'])) 
                for _, row in df.iterrows()]
        
        execute_values(cursor, 
            "INSERT INTO product_types (name, coefficient) VALUES %s",
            data)
        
        conn.commit()
        print(f"Импортировано {len(data)} типов продукции")
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при импорте типов продукции: {e}")
        raise e

def import_workshops(conn):
    try:
        df = pd.read_excel('data/Workshops_import.xlsx', engine='openpyxl')
        df.columns = ['name', 'type', 'employees_count']
        
        cursor = conn.cursor()
        
        cursor.execute("TRUNCATE workshops RESTART IDENTITY CASCADE;")
        
        data = [(row['name'], row['type'], int(row['employees_count'])) 
                for _, row in df.iterrows()]
        
        execute_values(cursor, 
            "INSERT INTO workshops (name, type, employees_count) VALUES %s",
            data)
        
        conn.commit()
        print(f"✅ Импортировано {len(data)} цехов")
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при импорте цехов: {e}")
        raise e

def import_products(conn):
    try:
        df = pd.read_excel('data/Products_import.xlsx', engine='openpyxl')
        df.columns = ['product_type', 'name', 'article', 'min_price', 'main_material']
        
        cursor = conn.cursor()
        
        cursor.execute("TRUNCATE products RESTART IDENTITY CASCADE;")
        
        data = []
        errors = []
        
        for idx, row in df.iterrows():
            try:
                cursor.execute("SELECT id FROM product_types WHERE name = %s", 
                              (row['product_type'],))
                result = cursor.fetchone()
                if not result:
                    errors.append(f"Тип продукции не найден: {row['product_type']}")
                    continue
                product_type_id = result[0]

                cursor.execute("SELECT id FROM material_types WHERE name = %s", 
                              (row['main_material'],))
                result = cursor.fetchone()
                if not result:
                    errors.append(f"Материал не найден: {row['main_material']}")
                    continue
                material_id = result[0]
                
                data.append((
                    str(row['article']),
                    product_type_id,
                    row['name'],
                    float(row['min_price']),
                    material_id
                ))
            except Exception as e:
                errors.append(f"Строка {idx+1}: {e}")
        
        if errors:
            print("Ошибки при обработке:")
            for err in errors:
                print(f"  - {err}")
        
        if data:
            execute_values(cursor, 
                "INSERT INTO products (article, product_type_id, name, min_price, main_material_id) VALUES %s",
                data)
            conn.commit()
            print(f"Импортировано {len(data)} продуктов")
        else:
            print("Нет данных для импорта продуктов")
            
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при импорте продуктов: {e}")
        raise e

def import_product_workshops(conn):
    try:
        df = pd.read_excel('data/Product_workshops_import.xlsx', engine='openpyxl')
        df.columns = ['product_name', 'workshop_name', 'hours']
        
        cursor = conn.cursor()
        
        cursor.execute("TRUNCATE product_workshops RESTART IDENTITY;")
        
        data = []
        errors = []
        
        for idx, row in df.iterrows():
            try:
                cursor.execute("SELECT id FROM products WHERE name = %s", 
                              (row['product_name'],))
                result = cursor.fetchone()
                if not result:
                    errors.append(f"Продукт не найден: {row['product_name']}")
                    continue
                product_id = result[0]
                
                cursor.execute("SELECT id FROM workshops WHERE name = %s", 
                              (row['workshop_name'],))
                result = cursor.fetchone()
                if not result:
                    errors.append(f"Цех не найден: {row['workshop_name']}")
                    continue
                workshop_id = result[0]
                
                data.append((
                    product_id,
                    workshop_id,
                    float(row['hours'])
                ))
            except Exception as e:
                errors.append(f"Строка {idx+1}: {e}")
        
        if errors:
            print("Ошибки при обработке связей:")
            for err in errors:
                print(f"  - {err}")
        
        if data:
            execute_values(cursor, 
                "INSERT INTO product_workshops (product_id, workshop_id, hours) VALUES %s",
                data)
            conn.commit()
            print(f"Импортировано {len(data)} связей продуктов с цехами")
        else:
            print("Нет данных для импорта связей")
            
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при импорте связей: {e}")
        raise e

def create_tables_if_not_exist(conn):
    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS material_types (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                loss_percent NUMERIC(10, 4) NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS product_types (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                coefficient NUMERIC(10, 2) NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS workshops (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL UNIQUE,
                type VARCHAR(100) NOT NULL,
                employees_count INTEGER NOT NULL CHECK (employees_count > 0)
            );
            
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                article VARCHAR(50) NOT NULL UNIQUE,
                product_type_id INTEGER NOT NULL REFERENCES product_types(id) ON DELETE RESTRICT,
                name VARCHAR(200) NOT NULL,
                min_price NUMERIC(10, 2) NOT NULL CHECK (min_price >= 0),
                main_material_id INTEGER NOT NULL REFERENCES material_types(id) ON DELETE RESTRICT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS product_workshops (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                workshop_id INTEGER NOT NULL REFERENCES workshops(id) ON DELETE CASCADE,
                hours NUMERIC(10, 1) NOT NULL CHECK (hours >= 0),
                UNIQUE(product_id, workshop_id)
            );
        """)
        conn.commit()
        print("✅ Таблицы проверены/созданы")
        cursor.close()
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        raise e

def main():
    print("=" * 50)
    print("Начало импорта данных...")
    print("=" * 50)

    if not os.path.exists('data'):
        print("Папка 'data' не найдена!")
        print("Создайте папку 'data' и поместите в нее Excel файлы")
        return

    required_files = [
        'Material_type_import.xlsx',
        'Product_type_import.xlsx',
        'Products_import.xlsx',
        'Product_workshops_import.xlsx',
        'Workshops_import.xlsx'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(f'data/{file}'):
            missing_files.append(file)
    
    if missing_files:
        print("Отсутствуют файлы:")
        for file in missing_files:
            print(f"  - data/{file}")
        return
    
    conn = connect_db()
    if not conn:
        print("Не удалось подключиться к БД. Проверьте:")
        print("  1. Запущен ли PostgreSQL")
        print("  2. Правильность пароля в DB_CONFIG")
        print("  3. Существует ли база данных 'furniture_company'")
        return
    
    try:
        create_tables_if_not_exist(conn)
        
        check_database_exists(conn)

        print("\n" + "=" * 50)
        print("Импорт типов материалов...")
        import_material_types(conn)
        
        print("\n" + "=" * 50)
        print("Импорт типов продукции...")
        import_product_types(conn)
        
        print("\n" + "=" * 50)
        print("Импорт цехов...")
        import_workshops(conn)
        
        print("\n" + "=" * 50)
        print("Импорт продуктов...")
        import_products(conn)
        
        print("\n" + "=" * 50)
        print("Импорт связей продуктов с цехами...")
        import_product_workshops(conn)
        
        print("\n" + "=" * 50)
        print("✅ Импорт данных успешно завершен!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nОшибка при импорте: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
            print("Соединение с БД закрыто")

if __name__ == "__main__":
    main()