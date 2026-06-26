import os
import time
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from recognition_system import recognize_part, preload_dataset

app = Flask(__name__)
CORS(app)


# Configure upload folder
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Warm up the cache at startup
print("Warming up the spare parts ORB descriptor cache...")
preload_dataset()

@app.route('/')
def index():
    """Renders the main dashboard page."""
    return render_template('index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serves static assets from the root assets folder."""
    return send_from_directory(os.path.join(app.root_path, 'assets'), filename)

@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint for spare part recognition.
    Expects an 'image' file in POST form-data.
    Returns details of the recognized part and matching statistics as JSON.
    """
    if 'image' not in request.files:
        return jsonify({
            "error": "No image file provided in the request"
        }), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({
            "error": "Empty filename"
        }), 400

    # Save file with a fixed filename (or unique) to query
    # We use a fixed name with overwrite to avoid filling up disk space
    filename = "query.jpg"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(filepath)
    except Exception as e:
        return jsonify({
            "error": f"Failed to save uploaded image: {str(e)}"
        }), 500

    # Run the recognition pipeline
    start_time = time.time()
    try:
        result = recognize_part(filepath)
    except Exception as e:
        return jsonify({
            "error": f"Recognition pipeline error: {str(e)}"
        }), 500
    
    processing_time = round((time.time() - start_time) * 1000, 2) # in milliseconds

    # Add extra metadata for the client
    response_data = {
        "success": True,
        "part": result.get("part", "Unknown"),
        "matches": result.get("matches", 0),
        "confidence": result.get("confidence", 0.0),
        "details": result.get("details"),
        "imageUrl": f"/static/uploads/{filename}?t={int(time.time())}", # Query parameter to bypass browser cache
        "processingTimeMs": processing_time
    }

    return jsonify(response_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port
    )
