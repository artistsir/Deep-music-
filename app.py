from flask import Flask, request, jsonify, render_template
import requests
import re
from urllib.parse import urlparse, urlunparse

app = Flask(__name__)

class InstagramDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        })
    
    def remove_query_from_url(self, url):
        """Remove query parameters from URL"""
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
    
    def get_reel_video(self, url):
        """Extract video URL from Instagram page"""
        try:
            clean_url = self.remove_query_from_url(url)
            response = self.session.get(clean_url, timeout=30)
            
            if response.status_code != 200:
                return None
            
            html_content = response.text
            
            # Multiple patterns to find video URL
            video_patterns = [
                r'"video_url":"([^"]+)"',
                r'video_versions.*?url.*?"([^"]+)"',
                r'contentUrl":"([^"]+)"',
                r'<video[^>]*src="([^"]+)"',
            ]
            
            for pattern in video_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    video_url = match.replace('\\u0026', '&').replace('\\u002F', '/')
                    if video_url.startswith('http') and ('.mp4' in video_url or 'video' in video_url):
                        return video_url
            
            return None
            
        except Exception as e:
            print(f"Error extracting video: {e}")
            return None
    
    def get_reel_info(self, url):
        """Get reel information including video URL"""
        try:
            print(f"[PROCESSING]: {url}")
            clean_url = self.remove_query_from_url(url)
            
            # Get video URL
            download_link = self.get_reel_video(clean_url)
            
            if not download_link:
                return {'error': 'Could not extract video from Instagram'}
            
            # Get Open Graph info
            og_info = self.get_open_graph_info(clean_url)
            
            return {
                'success': True,
                'platform': 'instagram',
                'title': og_info.get('title', 'Instagram Reel'),
                'author': og_info.get('author', ''),
                'description': og_info.get('description', ''),
                'thumbnail': og_info.get('image', ''),
                'media_urls': [download_link],
                'post_url': clean_url
            }
            
        except Exception as e:
            return {'error': f'Instagram processing error: {str(e)}'}
    
    def get_open_graph_info(self, url):
        """Extract Open Graph info from page"""
        try:
            response = self.session.get(url, timeout=30)
            html = response.text
            
            og_info = {}
            
            # Extract title
            title_match = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]*)"', html)
            if title_match:
                og_info['title'] = title_match.group(1)
            
            # Extract description
            desc_match = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]*)"', html)
            if desc_match:
                og_info['description'] = desc_match.group(1)
            
            # Extract image
            image_match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]*)"', html)
            if image_match:
                og_info['image'] = image_match.group(1)
            
            return og_info
            
        except Exception as e:
            print(f"Open Graph error: {e}")
            return {}

downloader = InstagramDownloader()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/download', methods=['POST', 'GET'])
def download_media():
    if request.method == 'GET':
        url = request.args.get('url')
    else:
        data = request.get_json()
        url = data.get('url') if data else None
    
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400
    
    if 'instagram.com' in url:
        result = downloader.get_reel_info(url)
    else:
        result = {'error': 'Only Instagram supported in this version'}
    
    return jsonify(result)

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'active',
        'service': 'Instagram Reel Downloader',
        'version': '4.0',
        'method': 'Auto Download - 100% WORKING'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
