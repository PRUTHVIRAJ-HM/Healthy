import os
import logging
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import json
from text_extractor import extract_text_from_image, extract_text_from_pdf
from web_scraper import get_food_information
from rag_engine import analyze_prescription, check_food_safety

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Configure upload folder
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Get food product from form
        food_product = request.form.get('food_product', '')
        if not food_product:
            flash('Please enter a food product name', 'danger')
            return redirect(url_for('index'))
        
        # Check if prescription file was uploaded
        if 'prescription' not in request.files:
            flash('No prescription file uploaded', 'danger')
            return redirect(url_for('index'))
        
        file = request.files['prescription']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(url_for('index'))
        
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload PDF or image files.', 'danger')
            return redirect(url_for('index'))
        
        # Save the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text from prescription
        prescription_text = ""
        if filename.lower().endswith('.pdf'):
            prescription_text = extract_text_from_pdf(filepath)
        else:  # Image files
            prescription_text = extract_text_from_image(filepath)
        
        # Check if extraction was successful
        if not prescription_text:
            flash('Could not extract text from the prescription. Please try a clearer image or PDF.', 'warning')
            return redirect(url_for('index'))
        
        # Get food information through web scraping
        food_info = get_food_information(food_product)
        
        # Analyze prescription for dietary restrictions
        restrictions = analyze_prescription(prescription_text)
        
        # Check if food is safe based on restrictions
        result = check_food_safety(food_product, food_info, restrictions)
        
        # Cleanup the uploaded file
        os.remove(filepath)
        
        # Return the result page
        return render_template('result.html', 
                              food_product=food_product,
                              is_safe=result['is_safe'],
                              recommendation=result['recommendation'],
                              explanation=result['explanation'],
                              benefits=result['benefits'],
                              health_risks=result['health_risks'],
                              restrictions=restrictions,
                              nutrients=result['nutrients'],
                              result=result)
    
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        flash(f'An error occurred during analysis: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.errorhandler(413)
def request_entity_too_large(error):
    flash('File too large. Maximum file size is 16MB.', 'danger')
    return redirect(url_for('index')), 413

@app.errorhandler(500)
def internal_server_error(error):
    flash('An internal server error occurred. Please try again later.', 'danger')
    return redirect(url_for('index')), 500

@app.errorhandler(404)
def page_not_found(error):
    return render_template('index.html', error="Page not found"), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
