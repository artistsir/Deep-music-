from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import uuid
import time
import threading
import logging
from utils.downloader import download_reel_with_cookies

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1000 per day", "200 per hour"],
    storage_uri="memory://",
)

# Configuration
DOWNLOAD_FOLDER = 'downloads'
COOKIES_FOLDER = 'cookies'
MAX_FILE_AGE = 1800  # 30 minutes

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)
if not os.path.exists(COOKIES_FOLDER):
    os.makedirs(COOKIES_FOLDER)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify({
        "status": "active", 
        "message": "Reels Downloader with Cookie Support",
        "timestamp": time.time()
    })

@app.route('/api/download', methods=['POST'])
@limiter.limit("30 per minute")
def download_reel_endpoint():
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                "success": False,
                "error": "URL is required in JSON format"
            }), 400
        
        reel_url = data['url'].strip()
        
        if not reel_url:
            return jsonify({
                "success": False,
                "error": "URL cannot be empty"
            }), 400
        
        # Validate URL
        if not (reel_url.startswith('http://') or reel_url.startswith('https://')):
            return jsonify({
                "success": False,
                "error": "Invalid URL format"
            }), 400
        
        if not any(domain in reel_url for domain in ['instagram.com', 'facebook.com', 'fb.watch']):
            return jsonify({
                "success": False,
                "error": "Unsupported platform. Supported: Instagram, Facebook"
            }), 400
        
        logger.info(f"Download request for: {reel_url}")
        
        # Use cookies for download
        result = download_reel_with_cookies(reel_url, DOWNLOAD_FOLDER, COOKIES_FOLDER)
        
        processing_time = round(time.time() - start_time, 2)
        
        if result['success']:
            response_data = {
                "success": True,
                "message": "Reel downloaded successfully",
                "download_url": f"/api/file/{result['filename']}",
                "filename": result['filename'],
                "file_size": result.get('file_size', 0),
                "title": result.get('title', 'reel'),
                "duration": result.get('duration', 'Unknown'),
                "processing_time": f"{processing_time}s",
                "quality": result.get('quality', 'HD')
            }
            
            if result.get('thumbnail'):
                response_data['thumbnail'] = result['thumbnail']
            
            return jsonify(response_data)
        else:
            return jsonify({
                "success": False,
                "error": result['error'],
                "processing_time": f"{processing_time}s",
                "solution": result.get('solution', 'Try another reel or use cookies')
            }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/file/<filename>')
def serve_file(filename):
    try:
        if '..' in filename or '/' in filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        file_age = time.time() - os.path.getctime(file_path)
        if file_age > MAX_FILE_AGE:
            os.remove(file_path)
            return jsonify({"error": "File expired"}), 410
            
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"File serving error: {str(e)}")
        return jsonify({"error": "Error serving file"}), 500

@app.route('/api/upload-cookies', methods=['POST'])
def upload_cookies():
    """Endpoint to upload cookies file"""
    try:
        if 'cookies_file' not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400
        
        file = request.files['cookies_file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        if file and file.filename.endswith('.txt'):
            filename = f"cookies_{int(time.time())}.txt"
            filepath = os.path.join(COOKIES_FOLDER, filename)
            file.save(filepath)
            
            return jsonify({
                "success": True,
                "message": "Cookies file uploaded successfully",
                "filename": filename
            })
        else:
            return jsonify({"success": False, "error": "Only .txt files are supported"}), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def cleanup_old_files():
    """Clean up old files"""
    try:
        deleted_count = 0
        current_time = time.time()
        
        for folder in [DOWNLOAD_FOLDER, COOKIES_FOLDER]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getctime(file_path)
                    if file_age > MAX_FILE_AGE:
                        os.remove(file_path)
                        deleted_count += 1
        
        return deleted_count
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        return 0

def background_cleanup():
    """Background cleanup thread"""
    while True:
        time.sleep(300)  # 5 minutes
        try:
            deleted = cleanup_old_files()
            if deleted > 0:
                logger.info(f"Cleanup deleted {deleted} files")
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")

# Start background cleanup
cleanup_thread = threading.Thread(target=background_cleanup, daemon=True)
cleanup_thread.start()

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "success": False,
        "error": "Too many requests. Please wait a few minutes."
    }), 429

if __name__ == '__main__':
    logger.info("Starting Reels Downloader with Cookie Support...")
    cleanup_old_files()
    app.run(host='0.0.0.0', port=5000, debug=False)
