# import os
# from flask import Flask, render_template, request, redirect, url_for, send_from_directory
# from werkzeug.utils import secure_filename
# import string
# import random

# # --- Configuration ---
# UPLOAD_FOLDER = 'uploads' # The folder where uploaded files will be stored
# # It's a good practice to create this folder in your project directory
# ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# def allowed_file(filename):
#     """Checks if a file has an allowed extension."""
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# def generate_unique_link():
#     """Generates a random, unique 10-character string for a download link."""
#     # We will use this to create unique URLs for each file
#     return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# @app.route('/')
# def index():
#     """The main page for uploading files."""
#     return render_template('index.html')

# @app.route('/upload', methods=['POST'])
# def upload_file():
#     """Handles file uploads from the user."""
#     # Check if the post request has the file part
#     if 'file' not in request.files:
#         return 'No file part in the request', 400

#     file = request.files['file']

#     # If the user does not select a file, the browser submits an empty file
#     if file.filename == '':
#         return 'No selected file', 400

#     if file and allowed_file(file.filename):
#         # Secure the filename to prevent security issues
#         filename = secure_filename(file.filename)
        
#         # Generate a unique ID for the file
#         unique_id = generate_unique_link()
        
#         # Create a unique folder for each file to be shared
#         file_directory = os.path.join(app.config['UPLOAD_FOLDER'], unique_id)
#         os.makedirs(file_directory, exist_ok=True)
        
#         # Save the file inside its unique folder
#         file_path = os.path.join(file_directory, filename)
#         file.save(file_path)

#         # Build the shareable link
#         shareable_link = url_for('download_file', unique_id=unique_id, filename=filename, _external=True)
        
#         return render_template('share_link.html', shareable_link=shareable_link)

#     return 'File type not allowed', 400

# @app.route('/share/<unique_id>/<filename>')
# def download_file(unique_id, filename):
#     """Serves the file for download via a unique link."""
#     file_directory = os.path.join(app.config['UPLOAD_FOLDER'], unique_id)
#     return send_from_directory(file_directory, filename)

# if __name__ == '__main__':
#     # Create the uploads folder if it doesn't exist
#     if not os.path.exists(UPLOAD_FOLDER):
#         os.makedirs(UPLOAD_FOLDER)
#     app.run(debug=True)




## Setup _ Code
"""Testing Code"""
import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import string
import random
from datetime import datetime, timedelta

# --- Configuration ---
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'your_secret_key' # Needed for flash messages
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///files.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Model ---
class SharedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(10), unique=True, nullable=False)
    original_filename = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))
    expiration_time = db.Column(db.DateTime)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

# Ensure the database and table are created
with app.app_context():
    db.create_all()

# --- Utility Functions ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_link():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part in the request')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        unique_id = generate_unique_link()
        
        # Save file to disk
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_id)
        os.makedirs(file_path, exist_ok=True)
        file.save(os.path.join(file_path, original_filename))

        # Handle password and expiration
        password = request.form.get('password')
        password_hash = generate_password_hash(password) if password else None
        
        expires_in = request.form.get('expires_in')
        expiration_time = None
        if expires_in and expires_in.isdigit():
            expiration_time = datetime.utcnow() + timedelta(minutes=int(expires_in))
        
        # Save metadata to database
        new_file = SharedFile(
            unique_id=unique_id,
            original_filename=original_filename,
            filename=original_filename,
            password_hash=password_hash,
            expiration_time=expiration_time
        )
        db.session.add(new_file)
        db.session.commit()

        shareable_link = url_for('share_file', unique_id=unique_id, _external=True)
        return render_template('share_link.html', shareable_link=shareable_link)

    flash('File type not allowed')
    return redirect(url_for('index'))

@app.route('/share/<unique_id>', methods=['GET', 'POST'])
def share_file(unique_id):
    shared_file = SharedFile.query.filter_by(unique_id=unique_id).first_or_404()

    # Check for expiration
    if shared_file.expiration_time and datetime.utcnow() > shared_file.expiration_time:
        flash('This file link has expired.')
        return render_template('expired.html'), 410

    # If password protected, handle the prompt
    if shared_file.password_hash:
        if request.method == 'POST':
            password = request.form.get('password')
            if check_password_hash(shared_file.password_hash, password):
                return redirect(url_for('download_file', unique_id=unique_id))
            else:
                flash('Incorrect password.')
                return render_template('password_prompt.html', unique_id=unique_id)
        else:
            return render_template('password_prompt.html', unique_id=unique_id)
    
    # If no password, redirect directly to download
    return redirect(url_for('download_file', unique_id=unique_id))

@app.route('/download/<unique_id>')
def download_file(unique_id):
    shared_file = SharedFile.query.filter_by(unique_id=unique_id).first_or_404()
    
    # Check for expiration again for security
    if shared_file.expiration_time and datetime.utcnow() > shared_file.expiration_time:
        flash('This file link has expired.')
        return render_template('expired.html'), 410

    file_directory = os.path.join(app.config['UPLOAD_FOLDER'], unique_id)
    return send_from_directory(file_directory, shared_file.original_filename, as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)