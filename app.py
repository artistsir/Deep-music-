from flask import Flask, request, jsonify, render_template
import requests
import re
import json
import os
from urllib.parse import urlparse

app = Flask(__name__)

class InstagramDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_media_links(self, html_content):
        """Extract media links from Instagram page HTML"""
        media_links = []
        
        # Patterns for different media types
        patterns = [
            r'"display_url":"(https://[^"]+)"',  # Images
            r'"video_url":"(https://[^"]+)"',    # Videos
            r'"src":"(https://[^"]+)"'           # Alternative pattern
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                # Clean up the URL
                clean_url = match.replace('\\u0026', '&')
                if clean_url not in media_links:
                    media_links.append(clean_url)
        
        return media_links
    
    def download_media(self, url):
        """Download media from Instagram URL"""
        try:
            # Validate Instagram URL
            if not self.is_valid_instagram_url(url):
                return {'error': 'Invalid Instagram URL'}
            
            # Fetch the Instagram page
            response = self.session.get(url)
            if response.status_code != 200:
                return {'error': 'Failed to fetch Instagram page'}
            
            # Extract media links
            media_links = self.extract_media_links(response.text)
            
            if not media_links:
                return {'error': 'No media found in the post'}
            
            # Prepare response
            result = {
                'success': True,
                'media_count': len(media_links),
                'media_urls': media_links,
                'post_url': url
            }
            
            return result
            
        except Exception as e:
            return {'error': f'An error occurred: {str(e)}'}
    
    def is_valid_instagram_url(self, url):
        """Validate if the URL is a valid Instagram post URL"""
        parsed = urlparse(url)
        if parsed.netloc not in ['www.instagram.com', 'instagram.com']:
            return False
        
        # Check if it's a post URL (contains /p/ or /reel/)
        path = parsed.path
        return '/p/' in path or '/reel/' in path

# Initialize downloader
downloader = InstagramDownloader()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def download():
    """API endpoint for downloading Instagram media"""
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    url = data['url']
    result = downloader.download_media(url)
    
    return jsonify(result)

@app.route('/api/status')
def status():
    """API status endpoint"""
    return jsonify({
        'status': 'active',
        'service': 'Instagram Downloader API',
        'version': '1.0'
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
