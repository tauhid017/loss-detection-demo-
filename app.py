from flask import Flask, render_template, request, jsonify, send_file, make_response
from werkzeug.utils import secure_filename
from PIL import Image
import os
import tempfile
import uuid
from datetime import datetime
from image_captioner import ImageCaptioner
from description_generator import DescriptionGenerator
import json
import base64
import cv2
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from textwrap import wrap  # ✅ for text wrapping

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-make-it-random'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Initialize models (cached)
captioner = None
desc_generator = None

# Ensure upload and history directories exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('data', exist_ok=True)

HISTORY_FILE = 'data/detection_history.json'

# Initialize history file if it doesn't exist
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'w') as f:
        json.dump([], f)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_models():
    """Initialize models only when needed"""
    global captioner, desc_generator
    if captioner is None or desc_generator is None:
        captioner = ImageCaptioner()
        desc_generator = DescriptionGenerator()
    return captioner, desc_generator

def load_history():
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)

def add_to_history(entry):
    history = load_history()
    history.append(entry)
    save_history(history)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/history')
def history():
    history_data = load_history()
    history_data.reverse()  # Show most recent first
    return render_template('history.html', history=history_data)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        damage_type = request.form.get('damage_type', 'Unknown Damage')
        custom_damage = request.form.get('custom_damage', '')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            file_id = str(uuid.uuid4())
            filename = secure_filename(file.filename)
            temp_path = os.path.join('uploads', f"{file_id}_{filename}")
            file.save(temp_path)
            
            # Validate image
            try:
                with Image.open(temp_path) as img:
                    img.verify()
            except Exception:
                os.remove(temp_path)
                return jsonify({'error': 'Invalid image file'}), 400
            
            # Load models
            captioner, desc_generator = get_models()
            
            # Process image
            image_caption = captioner.generate_caption(temp_path)
            
            # Use custom damage type if provided
            final_damage_type = custom_damage if custom_damage else damage_type
            
            # Generate description
            loss_description = desc_generator.enhance_description(image_caption, final_damage_type)
            
            # Store original image data in base64 format
            image = cv2.imread(temp_path)
            _, buffer = cv2.imencode('.jpg', image)
            image_data = base64.b64encode(buffer).decode('utf-8')
            
            # Create result data
            result_data = {
                'success': True,
                'image_caption': image_caption,
                'damage_type': final_damage_type,
                'loss_description': loss_description,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'filename': filename,
                'image_data': image_data
            }
            
            # Add to history
            history_entry = {
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'damage_type': final_damage_type,
                'image_caption': image_caption,
                'loss_description': loss_description,
                'image_data': image_data
            }
            add_to_history(history_entry)
            
            # Clean up temporary file
            os.remove(temp_path)
            
            return jsonify(result_data)
        
        else:
            return jsonify({'error': 'Invalid file type. Please upload PNG, JPG, or JPEG.'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    """Download description as PDF file"""
    try:
        data = request.get_json()
        description = data.get('description', '')
        damage_type = data.get('damage_type', 'loss_description')
        image_data = data.get('image_data', '')
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Header
        p.setFillColorRGB(0/255, 119/255, 182/255)
        p.rect(0, height-100, width, 100, fill=1)
        p.setFillColorRGB(1, 1, 1)
        p.setFont("Helvetica-Bold", 20)
        p.drawString(50, height-60, "Insurance Loss Description Report")
        p.setFont("Helvetica", 12)
        p.drawString(50, height-80, "Generated by ClaimInsight AI System")

        # Damage Info
        y = height - 130
        p.setFillColorRGB(0/255, 119/255, 182/255)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Damage Assessment Details")
        p.setFillColorRGB(0, 0, 0)
        y -= 20
        p.setFont("Helvetica", 12)
        p.drawString(50, y, f"Damage Type: {damage_type}")
        y -= 20
        p.drawString(50, y, f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Loss Description
        y -= 40
        p.setFillColorRGB(0/255, 119/255, 182/255)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Professional Loss Description")
        y -= 20
        p.setFillColorRGB(0, 0, 0)

        # ✅ Wrapped text fix
        wrapped_lines = []
        max_width = 90  # characters per line
        for paragraph in description.split('\n'):
            for wrapped_line in wrap(paragraph, width=max_width):
                wrapped_lines.append(wrapped_line)

        for line in wrapped_lines:
            if line.strip():
                if y < 100:
                    p.showPage()
                    y = height - 50
                p.setFont("Helvetica", 10)
                p.drawString(50, y, line.strip())
                y -= 15

        # Damage Image
        if image_data and y > 200:
            try:
                y -= 30
                p.setFillColorRGB(0/255, 119/255, 182/255)
                p.setFont("Helvetica-Bold", 14)
                p.drawString(50, y, "Damage Image")
                y -= 20
                img_data = base64.b64decode(image_data)
                img = Image.open(BytesIO(img_data))

                max_width = 300
                max_height = 200
                img_width, img_height = img.size
                aspect = img_width / img_height
                if aspect > max_width/max_height:
                    img_width = max_width
                    img_height = img_width / aspect
                else:
                    img_height = max_height
                    img_width = img_height * aspect

                p.drawImage(ImageReader(img), 50, y-img_height, width=img_width, height=img_height)
            except Exception as e:
                print(f"Error adding image to PDF: {str(e)}")

        # Footer
        p.setFont("Helvetica", 8)
        p.drawString(50, 30, "Confidential - For Insurance Claim Purposes")
        p.drawString(400, 30, f"Generated on: {datetime.now().strftime('%d %b %Y')}")

        p.save()
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.mimetype = 'application/pdf'
        response.headers['Content-Disposition'] = f"attachment; filename=loss_description_{damage_type.replace(' ', '_')}.pdf"

        return response
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
