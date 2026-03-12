from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

from models import (
    Product, ProductType, MaterialType, Workshop, ProductWorkshop,
    get_db_connection, DB_CONFIG
)
from utils import calculate_raw_material

app = Flask(__name__)
app.secret_key = 'demo-exam-2025-secret-key'

@app.context_processor
def utility_processor():
    def calculate_total_time(product_id):
        """Функция для расчета общего времени изготовления"""
        return Workshop.calculate_total_time(product_id)
    
    def get_product_workshops_count(product_id):
        try:
            workshops = Workshop.get_by_product(product_id)
            return len(workshops)
        except:
            return 0
    
    return dict(
        calculate_total_time=calculate_total_time,
        get_product_workshops_count=get_product_workshops_count
    )

@app.route('/')
def index():
    try:
        products = Product.get_all()
        return render_template('index.html', products=products)
    except Exception as e:
        flash(f'Ошибка при загрузке данных: {str(e)}', 'error')
        return render_template('index.html', products=[])

@app.route('/workshops')
def workshops_list():
    try:
        workshops = Workshop.get_all_workshops()
        return render_template('workshops_list.html', workshops=workshops)
    except Exception as e:
        flash(f'Ошибка при загрузке цехов: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/product/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        try:
            article = request.form['article']
            product_type_id = int(request.form['product_type_id'])
            name = request.form['name']
            min_price = float(request.form['min_price'])
            main_material_id = int(request.form['main_material_id'])
            
            if min_price < 0:
                flash('Стоимость не может быть отрицательной!', 'error')
                return redirect(url_for('add_product'))
            
            product_id = Product.create(
                article, product_type_id, name, min_price, main_material_id
            )
            
            flash('Продукция успешно добавлена!', 'success')
            return redirect(url_for('index'))
            
        except ValueError as e:
            flash(f'Ошибка в формате данных: {str(e)}', 'error')
        except Exception as e:
            flash(f'Ошибка при добавлении продукции: {str(e)}', 'error')
            
        return redirect(url_for('add_product'))
    
    try:
        product_types = ProductType.get_all()
        materials = MaterialType.get_all()
        return render_template('product_form.html', 
                             product_types=product_types, 
                             materials=materials,
                             product=None)
    except Exception as e:
        flash(f'Ошибка при загрузке данных: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/product/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    """Редактирование продукции"""
    if request.method == 'POST':
        try:
            article = request.form['article']
            product_type_id = int(request.form['product_type_id'])
            name = request.form['name']
            min_price = float(request.form['min_price'])
            main_material_id = int(request.form['main_material_id'])
            
            if min_price < 0:
                flash('Стоимость не может быть отрицательной!', 'error')
                return redirect(url_for('edit_product', product_id=product_id))
            
            Product.update(product_id, article, product_type_id, 
                          name, min_price, main_material_id)
            
            flash('Продукция успешно обновлена!', 'success')
            return redirect(url_for('index'))
            
        except ValueError as e:
            flash(f'Ошибка в формате данных: {str(e)}', 'error')
        except Exception as e:
            flash(f'Ошибка при обновлении продукции: {str(e)}', 'error')
            
        return redirect(url_for('edit_product', product_id=product_id))
    
    try:
        product = Product.get_by_id(product_id)
        if not product:
            flash('Продукция не найдена!', 'error')
            return redirect(url_for('index'))
        
        product_types = ProductType.get_all()
        materials = MaterialType.get_all()
        
        return render_template('product_form.html',
                             product=product,
                             product_types=product_types,
                             materials=materials)
    except Exception as e:
        flash(f'Ошибка при загрузке данных: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/product/<int:product_id>/workshops')
def view_workshops(product_id):
    try:
        product = Product.get_by_id(product_id)
        if not product:
            flash('Продукция не найдена!', 'error')
            return redirect(url_for('index'))
        
        workshops = Workshop.get_by_product(product_id)
        total_time = Workshop.calculate_total_time(product_id)
        
        return render_template('workshops.html',
                             product=product,
                             workshops=workshops,
                             total_time=total_time)
    except Exception as e:
        flash(f'Ошибка при загрузке данных: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/product/<int:product_id>/workshops/manage')
def manage_product_workshops(product_id):
    try:
        product = Product.get_by_id(product_id)
        if not product:
            flash('Продукция не найдена!', 'error')
            return redirect(url_for('index'))
        
        workshops = Workshop.get_by_product(product_id)
        
        available_workshops = Workshop.get_not_assigned_to_product(product_id)
        
        total_time = Workshop.calculate_total_time(product_id)
        
        return render_template('product_workshops.html',
                             product=product,
                             workshops=workshops,
                             available_workshops=available_workshops,
                             total_time=total_time)
    except Exception as e:
        flash(f'Ошибка при загрузке данных: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/product/<int:product_id>/workshops/add', methods=['POST'])
def add_product_workshop(product_id):
    try:
        workshop_id = int(request.form['workshop_id'])
        hours = float(request.form['hours'])
        
        if hours <= 0:
            flash('Время изготовления должно быть положительным числом!', 'error')
            return redirect(url_for('manage_product_workshops', product_id=product_id))
        
        ProductWorkshop.add(product_id, workshop_id, hours)
        flash('Цех успешно добавлен к продукции!', 'success')
        
    except ValueError as e:
        flash(f'Ошибка в формате данных: {str(e)}', 'error')
    except Exception as e:
        flash(f'Ошибка при добавлении цеха: {str(e)}', 'error')
    
    return redirect(url_for('manage_product_workshops', product_id=product_id))

@app.route('/product/<int:product_id>/workshops/<int:workshop_id>/remove', methods=['POST'])
def remove_product_workshop(product_id, workshop_id):
    try:
        ProductWorkshop.remove(product_id, workshop_id)
        flash('Цех успешно удален из технологического процесса!', 'success')
    except Exception as e:
        flash(f'Ошибка при удалении цеха: {str(e)}', 'error')
    
    return redirect(url_for('manage_product_workshops', product_id=product_id))

@app.route('/product/<int:product_id>/workshops/<int:workshop_id>/update', methods=['POST'])
def update_workshop_hours(product_id, workshop_id):
    try:
        hours = float(request.form['hours'])
        
        if hours <= 0:
            flash('Время изготовления должно быть положительным числом!', 'error')
            return redirect(url_for('manage_product_workshops', product_id=product_id))
        
        ProductWorkshop.update_hours(product_id, workshop_id, hours)
        flash('Время изготовления успешно обновлено!', 'success')
        
    except ValueError as e:
        flash(f'Ошибка в формате данных: {str(e)}', 'error')
    except Exception as e:
        flash(f'Ошибка при обновлении времени: {str(e)}', 'error')
    
    return redirect(url_for('manage_product_workshops', product_id=product_id))

@app.route('/api/product/<int:product_id>/total-time')
def api_total_time(product_id):
    try:
        total_time = Workshop.calculate_total_time(product_id)
        return jsonify({'total_time': total_time, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 400

@app.route('/api/calculate-material', methods=['POST'])
def calculate_material():
    try:
        data = request.get_json()
        
        product_type_id = int(data.get('product_type_id'))
        material_type_id = int(data.get('material_type_id'))
        product_quantity = int(data.get('product_quantity'))
        param1 = float(data.get('param1'))
        param2 = float(data.get('param2'))
        
        result = calculate_raw_material(
            product_type_id, material_type_id, 
            product_quantity, param1, param2
        )
        
        return jsonify({'result': result, 'success': result != -1})
        
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 400

@app.route('/calculator')
def calculator():
    try:
        product_types = ProductType.get_all()
        material_types = MaterialType.get_all()
        return render_template('calculator.html',
                             product_types=product_types,
                             material_types=material_types)
    except Exception as e:
        flash(f'Ошибка при загрузке данных: {str(e)}', 'error')
        return redirect(url_for('index'))

#@app.errorhandler(404)
#def not_found_error(error):
    flash('Запрашиваемая страница не найдена', 'error')
    return redirect(url_for('index'))

#@app.errorhandler(500)
#def internal_error(error):
    flash('Внутренняя ошибка сервера', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)