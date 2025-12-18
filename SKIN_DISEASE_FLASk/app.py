from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import json
import os
from werkzeug.utils import secure_filename
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import time  # Add this line with your other imports
import numpy as np
import cv2
from PIL import Image
import base64
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'jfif'}


# Disease classes (you'll need to update this based on your dataset)
DISEASE_CLASSES = [
  'Acne', 'Lentigines', 'Leprosy', 'Melasma', 'Other', 'Periorbital_hyperpigmentation', 'Postinflammatory_hyperpigmentation', 'Vitiligo'
]

# Load or initialize user data
def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

def load_products():
    try:
        with open('products.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def load_doctors():
    try:
        with open('doctors.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_jfif_to_jpg(filepath):
    """Convert JFIF files to JPG format for better compatibility"""
    if filepath.lower().endswith('.jfif'):
        img = Image.open(filepath)
        new_path = filepath.rsplit('.', 1)[0] + '.jpg'
        rgb_img = img.convert('RGB')
        rgb_img.save(new_path, 'JPEG')
        os.remove(filepath)  # Remove the original JFIF file
        return new_path
    return filepath

# Load CNN model (you'll need to train this first)
def load_skin_model():
    try:
        model = load_model('models/skin_model.h5')
        return model
    except:
        return None

# Preprocess image for prediction
def preprocess_image(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array /= 255.0
    return img_array

# Routes
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_users()
        
        if username in users and users[username]['password'] == password:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        users = load_users()
        
        if username in users:
            flash('Username already exists', 'error')
        else:
            users[username] = {
                'password': password,
                'email': email
            }
            save_users(users)
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        filepath = None
        
        # Check if camera image was submitted
        if 'camera_image' in request.form and request.form['camera_image']:
            # Handle base64 image from camera
            image_data = request.form['camera_image'].split(',')[1]
            img_bytes = base64.b64decode(image_data)
            img = Image.open(io.BytesIO(img_bytes))
            
            # Save the image
            filename = f"camera_capture_{session['username']}_{int(time.time())}.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            img.convert('RGB').save(filepath, 'JPEG')
            
        # Check if file was uploaded
        elif 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Convert JFIF to JPG if needed
                filepath = convert_jfif_to_jpg(filepath)
            else:
                flash('Invalid file type. Please upload PNG, JPG, JPEG, or JFIF.', 'error')
                return redirect(request.url)
        else:
            flash('Please select an image or capture from camera', 'error')
            return redirect(request.url)
        
        # Load model and make prediction
        model = load_skin_model()
        if model is None:
            flash('Model not available. Please train the model first.', 'error')
            return redirect(request.url)
        
        # Preprocess and predict
        try:
            img_array = preprocess_image(filepath)
            prediction = model.predict(img_array)
            predicted_class_idx = np.argmax(prediction[0])
            confidence = prediction[0][predicted_class_idx]
            
            disease_name = DISEASE_CLASSES[predicted_class_idx]
            
            # Classify as minor or major
            major_diseases = ['Melasma', 'Periorbital_hyperpigmentation']
            is_major = disease_name in major_diseases
            
            return render_template('results.html', 
                                 disease=disease_name,
                                 confidence=float(confidence),
                                 is_major=is_major,
                                 image_url=filepath)
        except Exception as e:
            flash(f'Error processing image: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('predict.html')

@app.route('/results')
def results():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('results.html')

@app.route('/get_recommendations/<disease_type>')
def get_recommendations(disease_type):
    if disease_type == 'minor':
        products = load_products()
        return jsonify(products)
    else:
        doctors = load_doctors()
        return jsonify(doctors)

@app.route('/train_model')
def train_model():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # This would trigger the training process
    # In a real application, you might want to run this in a background process
    try:
        # Import and run training
        from models.model_training import train_skin_model
        accuracy = train_skin_model()
        flash(f'Model training completed with accuracy: {accuracy:.2f}%', 'success')
    except Exception as e:
        flash(f'Training failed: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    app.run(debug=True)