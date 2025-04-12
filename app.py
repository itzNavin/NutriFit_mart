import os
import json
import qrcode
from flask import Flask, render_template, request, redirect, url_for, jsonify
import cv2

app = Flask(__name__)

# Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
QR_CODES_DIR = os.path.join(STATIC_DIR, 'qr_codes')
UPLOADS_DIR = os.path.join(STATIC_DIR, 'uploads')
CATALOG_FILE = os.path.join(BASE_DIR, 'catalog.json')

os.makedirs(QR_CODES_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

def load_catalog():
    if os.path.exists(CATALOG_FILE):
        try:
            with open(CATALOG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Warning: catalog.json is empty or contains invalid JSON. Starting with empty catalog.")
            return []
    return []

def save_catalog(catalog):
    with open(CATALOG_FILE, 'w') as f:
        json.dump(catalog, f, indent=2)

def generate_qr_code(catalog):
    qr = qrcode.make(json.dumps(catalog))
    qr_path = os.path.join(QR_CODES_DIR, 'catalog_qr.png')
    qr.save(qr_path)
    return url_for('static', filename=f'qr_codes/catalog_qr.png')

def decode_barcode(image_path):
    if not os.path.exists(image_path):
        return None
    img = cv2.imread(image_path)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if not hasattr(cv2, 'barcode'):
        return None
    detector = cv2.barcode.BarcodeDetector()
    ok, data, _, _ = detector.detectAndDecode(gray)
    return data if ok else None

@app.route('/')
def index():
    catalog = load_catalog()
    qr_code_path = generate_qr_code(catalog)
    return render_template('index.html', qr_code_path=qr_code_path)

@app.route('/products')
def products():
    catalog = load_catalog()
    return render_template('products_list.html', catalog=catalog)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        # Combine quantity value and unit
        quantity = f"{request.form['quantity_value']} {request.form['quantity_unit']}"
        
        item = {
            'name': request.form['name'],
            'nutritional_values': request.form['nutritional_values'],
            'price': float(request.form['price']),
            'quantity': quantity,
            'category': request.form['category'],
            'tags': request.form['tags'].split(',') if request.form['tags'] else [],
            'image': request.files['image'].filename if 'image' in request.files else None
        }
        
        catalog = load_catalog()
        catalog.append(item)
        save_catalog(catalog)
        return redirect(url_for('products'))
    return render_template('add_items.html')

@app.route('/delete/<int:index>', methods=['POST'])
def delete(index):
    catalog = load_catalog()
    if 0 <= index < len(catalog):
        catalog.pop(index)
        save_catalog(catalog)
    return redirect(url_for('products'))

# In your scan route
@app.route('/scan', methods=['GET', 'POST'])
def scan():
    if request.method == 'POST':
        # Handle both live scanning and image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename.endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(UPLOADS_DIR, file.filename)
                file.save(file_path)
                barcode_data = decode_barcode(file_path)
                if barcode_data:
                    catalog = load_catalog()
                    catalog.append({
                        'name': barcode_data,
                        'nutritional_values': 'Unknown',
                        'price': 0,
                        'quantity': 1
                    })
                    save_catalog(catalog)
                    return jsonify({'message': 'Item added successfully!'}), 200
                return jsonify({'error': 'No barcode detected in the image'}), 400
        else:
            barcode_data = request.form.get('barcode_data')
            if barcode_data:
                catalog = load_catalog()
                catalog.append({
                    'name': barcode_data,
                    'nutritional_values': 'Unknown',
                    'price': 0,
                    'quantity': 1
                })
                save_catalog(catalog)
                return jsonify({'message': 'Item added successfully!'}), 200
        return jsonify({'error': 'No barcode data received'}), 400
    return render_template('scan.html')

if __name__ == '__main__':
    app.run(debug=True)