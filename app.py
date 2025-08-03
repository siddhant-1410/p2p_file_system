import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import string
import random

# --- Configuration ---
UPLOAD_FOLDER = 'uploads' # The folder where uploaded files will be stored
# It's a good practice to create this folder in your project directory
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    """Checks if a file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_link():
    """Generates a random, unique 10-character string for a download link."""
    # We will use this to create unique URLs for each file
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

@app.route('/')
def index():
    """The main page for uploading files."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file uploads from the user."""
    # Check if the post request has the file part
    if 'file' not in request.files:
        return 'No file part in the request', 400

    file = request.files['file']

    # If the user does not select a file, the browser submits an empty file
    if file.filename == '':
        return 'No selected file', 400

    if file and allowed_file(file.filename):
        # Secure the filename to prevent security issues
        filename = secure_filename(file.filename)
        
        # Generate a unique ID for the file
        unique_id = generate_unique_link()
        
        # Create a unique folder for each file to be shared
        file_directory = os.path.join(app.config['UPLOAD_FOLDER'], unique_id)
        os.makedirs(file_directory, exist_ok=True)
        
        # Save the file inside its unique folder
        file_path = os.path.join(file_directory, filename)
        file.save(file_path)

        # Build the shareable link
        shareable_link = url_for('download_file', unique_id=unique_id, filename=filename, _external=True)
        
        return render_template('share_link.html', shareable_link=shareable_link)

    return 'File type not allowed', 400

@app.route('/share/<unique_id>/<filename>')
def download_file(unique_id, filename):
    """Serves the file for download via a unique link."""
    file_directory = os.path.join(app.config['UPLOAD_FOLDER'], unique_id)
    return send_from_directory(file_directory, filename)

if __name__ == '__main__':
    # Create the uploads folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)