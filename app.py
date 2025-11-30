from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import uuid
import time
import threading
import logging
from utils.downloader import download_reel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["500 per day", "100 per hour"],
    storage_uri="memory://",
)

# Configuration
DOWNLOAD_FOLDER = 'downloads'
MAX_FILE_AGE = 1800  # 30 minutes
CLEANUP_INTERVAL = 300  # 5 minutes

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify({
        "status": "active", 
        "message": "Reels Downloader API is running",
        "timestamp": time.time()
    })

@app.route('/api/download', methods=['POST'])
@limiter.limit("20 per minute")
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
        
        # Validate URL format
        if not (reel_url.startswith('http://') or reel_url.startswith('https://')):
            return jsonify({
                "success": False,
                "error": "Invalid URL format. Must start with http:// or https://"
            }), 400
        
        # Check if it's a supported platform
        supported_domains = [
            'instagram.com', 'www.instagram.com',
            'facebook.com', 'www.facebook.com',
            'fb.watch', 'www.fb.watch'
        ]
        
        if not any(domain in reel_url for domain in supported_domains):
            return jsonify({
                "success": False,
                "error": "Unsupported platform. Supported: Instagram, Facebook"
            }), 400
        
        logger.info(f"Download request for: {reel_url}")
        
        # Download the reel
        result = download_reel(reel_url, DOWNLOAD_FOLDER)
        
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
                "processing_time": f"{processing_time}s"
            }
            
            if result.get('thumbnail'):
                response_data['thumbnail'] = result['thumbnail']
            
            return jsonify(response_data)
        else:
            return jsonify({
                "success": False,
                "error": result['error'],
                "processing_time": f"{processing_time}s"
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
        # Security checks
        if '..' in filename or '/' in filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found or expired"}), 404
        
        # Check file age
        file_age = time.time() - os.path.getctime(file_path)
        if file_age > MAX_FILE_AGE:
            os.remove(file_path)
            return jsonify({"error": "File expired"}), 410
            
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"File serving error: {str(e)}")
        return jsonify({"error": "Error serving file"}), 500

def cleanup_old_files():
    """Clean up old files"""
    try:
        deleted_count = 0
        current_time = time.time()
        
        for filename in os.listdir(DOWNLOAD_FOLDER):
            file_path = os.path.join(DOWNLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getctime(file_path)
                if file_age > MAX_FILE_AGE:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"Deleted old file: {filename}")
        
        return deleted_count
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        return 0

def background_cleanup():
    """Background cleanup thread"""
    while True:
        time.sleep(CLEANUP_INTERVAL)
        try:
            deleted = cleanup_old_files()
            if deleted > 0:
                logger.info(f"Background cleanup deleted {deleted} files")
        except Exception as e:
            logger.error(f"Background cleanup error: {str(e)}")

# Start background cleanup thread
cleanup_thread = threading.Thread(target=background_cleanup, daemon=True)
cleanup_thread.start()

# Error handlers
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "success": False,
        "error": "Rate limit exceeded. Please try again in a few minutes."
    }), 429

if __name__ == '__main__':
    logger.info("Starting Reels Downloader API...")
    cleanup_old_files()
    app.run(host='0.0.0.0', port=5000, debug=False)
