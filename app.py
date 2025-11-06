from flask import Flask, render_template, request, jsonify, make_response
from werkzeug.utils import secure_filename
from PIL import Image
import os
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
from textwrap import wrap

# ------------------ App Setup ------------------
app = Flask(__name__)
app.secret_key = 'your-secret-key-here-make-it-random'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure folders exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('data', exist_ok=True)

HISTORY_FILE = 'data/detection_history.json'

if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'w') as f:
        json.dump([], f)

# Model caching
captioner = None
desc_generator = None

# ------------------ Helper Functions ------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_models():
    """Lazy-load models"""
    global captioner, desc_generator
    if captioner is None or desc_generator is None:
        captioner = ImageCaptioner()
        desc_generator = DescriptionGenerator()
    return captioner, desc_generator

def load_history():
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)

def add_to_history(entry):
    history = load_history()
    history.append(entry)
    save_history(history)

# ------------------ Routes ------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/history')
def history():
    history_data = load_history()
    history_data.reverse()
    return render_template('history.html', history=history_data)

@app.route('/ping')
def ping():
    """Health check route"""
    return jsonify({"status": "ok", "message": "Flask backend running successfully"}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and image processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        damage_type = request.form.get('damage_type', 'Unknown Damage')
        custom_damage = request.form.get('custom_damage', '')

        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload PNG, JPG, or JPEG.'}), 400
        
        # Save temporary file
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

        # Process using models
        captioner, desc_generator = get_models()
        image_caption = captioner.generate_caption(temp_path)
        final_damage_type = custom_damage if custom_damage else damage_type
        loss_description = desc_generator.enhance_description(image_caption, final_damage_type)

        # Convert to Base64
        image = cv2.imread(temp_path)
        _, buffer = cv2.imencode('.jpg', image)
        image_data = base64.b64encode(buffer).decode('utf-8')

        # Save to history
        entry = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'damage_type': final_damage_type,
            'image_caption': image_caption,
            'loss_description': loss_description,
            'image_data': image_data
        }
        add_to_history(entry)

        # Clean up
        os.remove(temp_path)

        result_data = {
            'success': True,
            'image_caption': image_caption,
            'damage_type': final_damage_type,
            'loss_description': loss_description,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'filename': filename,
            'image_data': image_data
        }

        return jsonify(result_data), 200

    except Exception as e:
        # Log and return proper JSON error
        print(f"❌ Upload Error: {str(e)}")
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    """Download generated report as PDF"""
    try:
        data = request.get_json(force=True)
        description = data.get('description', '')
        damage_type = data.get('damage_type', 'Unknown')
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

        wrapped_lines = []
        for paragraph in description.split('\n'):
            wrapped_lines.extend(wrap(paragraph, width=90))

        for line in wrapped_lines:
            if y < 100:
                p.showPage()
                y = height - 50
            p.setFont("Helvetica", 10)
            p.drawString(50, y, line.strip())
            y -= 15

        # Add Image
        if image_data and y > 200:
            try:
                y -= 30
                p.setFillColorRGB(0/255, 119/255, 182/255)
                p.setFont("Helvetica-Bold", 14)
                p.drawString(50, y, "Damage Image")
                y -= 20
                img_data = base64.b64decode(image_data)
                img = Image.open(BytesIO(img_data))

                max_width, max_height = 300, 200
                img_width, img_height = img.size
                aspect = img_width / img_height
                if aspect > max_width / max_height:
                    img_width = max_width
                    img_height = img_width / aspect
                else:
                    img_height = max_height
                    img_width = img_height * aspect

                p.drawImage(ImageReader(img), 50, y - img_height, width=img_width, height=img_height)
            except Exception as e:
                print(f"Error adding image to PDF: {e}")

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
        print(f"❌ PDF Generation Error: {str(e)}")
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500

# ------------------ Error Handlers ------------------
@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

@app.errorhandler(Exception)
def handle_all_exceptions(e):
    """Catch all unexpected errors as JSON"""
    print(f"⚠️ Unhandled Exception: {str(e)}")
    return jsonify({'error': str(e), 'type': e.__class__.__name__}), 500

# ------------------ Run Server ------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
