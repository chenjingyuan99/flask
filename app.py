from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
import os
import pandas as pd
import json
from werkzeug.utils import secure_filename

# Cloud 
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
load_dotenv()
AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
AZURE_STORAGE_CONTAINER = os.getenv('AZURE_STORAGE_CONTAINER', 'testflask')
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER)
# For photo saving

app = Flask(__name__)
app.secret_key = 'supersecretkey_cloud_storage_2025'

# Configuration
UPLOAD_FOLDER = 'uploads'
PHOTO_FOLDER = os.path.join(UPLOAD_FOLDER, 'photos')
ALLOWED_EXTENSIONS = {'csv'}
ALLOWED_PHOTO_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PHOTO_FOLDER'] = PHOTO_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create directories if they don't exist
for folder in [UPLOAD_FOLDER, PHOTO_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Global variable to store people data
people_data = {}

def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def load_csv_data(csv_path):
    """Load CSV data and return as dictionary"""
    try:
        df = pd.read_csv(csv_path)
        # Convert DataFrame to dictionary with Name as key
        data = {}
        for _, row in df.iterrows():
            name = str(row.get('Name', '')).strip()
            if name and name != 'nan':
                data[name] = {
                    'State': str(row.get('State', '')),
                    'Salary': str(row.get('Salary', '')),
                    'Grade': str(row.get('Grade', '')),
                    'Room': str(row.get('Room', '')),
                    'Telnum': str(row.get('Telnum', '')),
                    'Picture': str(row.get('Picture', '')),
                    'Keywords': str(row.get('Keywords', ''))
                }
        return data
    except Exception as e:
        flash(f'Error loading CSV: {str(e)}')
        return {}

@app.route('/')
def index():
    return render_template('index.html', people_data=people_data)

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    global people_data
    
    if 'csv_file' not in request.files:
        flash('No CSV file selected')
        return redirect(url_for('index'))
    
    file = request.files['csv_file']
    if file.filename == '':
        flash('No CSV file selected')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename, ALLOWED_EXTENSIONS):
        filename = secure_filename(file.filename)
        csv_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(csv_path)
        
        # Load CSV data
        people_data = load_csv_data(csv_path)
        flash(f'CSV uploaded successfully! Loaded {len(people_data)} records.')
    else:
        flash('Invalid file type. Please upload a CSV file.')
    
    return redirect(url_for('index'))

@app.route('/upload_photos', methods=['POST'])
def upload_photos():
    if 'photo_files' not in request.files:
        flash('No photos selected')
        return redirect(url_for('index'))
    
    files = request.files.getlist('photo_files')
    uploaded_count = 0
    
    for file in files:
        if file.filename == '':
            continue
            
        if file and allowed_file(file.filename, ALLOWED_PHOTO_EXTENSIONS):
            filename = secure_filename(file.filename)
            
            # Check if photo already exists
            photo_path = os.path.join(app.config['PHOTO_FOLDER'], filename)
            if os.path.exists(photo_path):
                flash(f'Photo {filename} already exists. Skipped.')
                continue
            
            file.save(photo_path)
            uploaded_count += 1
        else:
            flash(f'Invalid photo type: {file.filename}')
    
    flash(f'Uploaded {uploaded_count} photos successfully!')
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
def search():
    search_type = request.form.get('search_type')
    results = []
    
    if search_type == 'name':
        name = request.form.get('search_name', '').strip()
        if name in people_data:
            results = [{'name': name, 'data': people_data[name]}]
    
    elif search_type == 'state':
        state = request.form.get('search_state', '').strip().upper()
        for name, data in people_data.items():
            if data['State'].upper() == state:
                results.append({'name': name, 'data': data})
    
    elif search_type == 'salary':
        min_salary = request.form.get('min_salary', '')
        max_salary = request.form.get('max_salary', '')
        
        for name, data in people_data.items():
            salary_str = data['Salary']
            if salary_str and salary_str != 'nan' and salary_str != '':
                try:
                    salary = float(salary_str)
                    include = True
                    
                    if min_salary and float(min_salary) > salary:
                        include = False
                    if max_salary and float(max_salary) < salary:
                        include = False
                    
                    if include:
                        results.append({'name': name, 'data': data})
                except ValueError:
                    continue
    
    return render_template('index.html', people_data=people_data, search_results=results)

@app.route('/get_person/<name>')
def get_person(name):
    if name in people_data:
        return jsonify({'success': True, 'data': people_data[name]})
    return jsonify({'success': False, 'message': 'Person not found'})

@app.route('/update_person', methods=['POST'])
def update_person():
    global people_data
    
    name = request.form.get('name')
    if name not in people_data:
        flash('Person not found')
        return redirect(url_for('index'))
    
    # Update all fields except name and picture
    people_data[name]['State'] = request.form.get('state', '')
    people_data[name]['Salary'] = request.form.get('salary', '')
    people_data[name]['Grade'] = request.form.get('grade', '')
    people_data[name]['Room'] = request.form.get('room', '')
    people_data[name]['Telnum'] = request.form.get('telnum', '')
    people_data[name]['Keywords'] = request.form.get('keywords', '')
    
    flash(f'Updated information for {name}')
    return redirect(url_for('index'))

@app.route('/add_photo/<name>', methods=['POST'])
def add_photo(name):
    if name not in people_data:
        flash('Person not found')
        return redirect(url_for('index'))
    
    if 'photo_file' not in request.files:
        flash('No photo selected')
        return redirect(url_for('index'))
    
    file = request.files['photo_file']
    if file.filename == '' or not allowed_file(file.filename, ALLOWED_PHOTO_EXTENSIONS):
        flash('Invalid photo file')
        return redirect(url_for('index'))
    
    filename = secure_filename(file.filename)
    photo_path = os.path.join(app.config['PHOTO_FOLDER'], filename)
    file.save(photo_path)
    
    people_data[name]['Picture'] = filename
    flash(f'Photo added for {name}')
    return redirect(url_for('index'))

@app.route('/remove_person/<name>', methods=['POST'])
def remove_person(name):
    global people_data
    
    if name in people_data:
        # Remove photo file if it exists
        picture = people_data[name].get('Picture', '')
        if picture:
            photo_path = os.path.join(app.config['PHOTO_FOLDER'], picture)
            if os.path.exists(photo_path):
                os.remove(photo_path)
        
        del people_data[name]
        flash(f'Removed {name} from database')
    else:
        flash('Person not found')
    
    return redirect(url_for('index'))

@app.route('/photo/<filename>')
def serve_photo(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['PHOTO_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
