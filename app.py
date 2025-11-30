from flask import Flask, request, jsonify, render_template
import requests
import re
import json
from urllib.parse import urlparse, urlunparse, quote

app = Flask(__name__)

class InstagramDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
        })
    
    def remove_query_from_url(self, url):
        """Remove query parameters from URL"""
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
    
    def get_reel_video_direct(self, url):
        """Method 1: Direct HTML parsing"""
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
                r'src="(https://[^"]*\.mp4[^"]*)"',
            ]
            
            for pattern in video_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    video_url = match.replace('\\u0026', '&').replace('\\u002F', '/')
                    if video_url.startswith('http') and ('.mp4' in video_url or 'video' in video_url):
                        print(f"Found video URL: {video_url}")
                        return video_url
            
            return None
            
        except Exception as e:
            print(f"Direct method error: {e}")
            return None
    
    def get_reel_video_api(self, url):
        """Method 2: Use external APIs"""
        try:
            # Try snapinsta.app API
            encoded_url = quote(url)
            api_url = "https://snapinsta.app/api/ajaxSearch"
            
            payload = f"q={encoded_url}&t=media&lang=en"
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://snapinsta.app",
                "Referer": "https://snapinsta.app/",
            }
            
            response = self.session.post(api_url, data=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    # Extract download link from HTML response
                    html = data['data']
                    download_match = re.search(r'href="(https://[^"]*\.mp4[^"]*)"', html)
                    if download_match:
                        video_url = download_match.group(1)
                        print(f"SnapInsta video URL: {video_url}")
                        return video_url
            
            return None
            
        except Exception as e:
            print(f"API method error: {e}")
            return None
    
    def get_reel_video_savefrom(self, url):
        """Method 3: Use savefrom.net"""
        try:
            api_url = "https://api.savefrom.net/api/convert"
            payload = {
                "url": url
            }
            
            headers = {
                "Content-Type": "application/json",
            }
            
            response = self.session.post(api_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"SaveFrom response: {data}")
                
                if data.get('url'):
                    video_url = data['url']
                    if video_url.startswith('http'):
                        print(f"SaveFrom video URL: {video_url}")
                        return video_url
                
                if data.get('links') and isinstance(data['links'], list):
                    for link in data['links']:
                        if link.get('url') and link['url'].startswith('http'):
                            print(f"SaveFrom video URL: {link['url']}")
                            return link['url']
            
            return None
            
        except Exception as e:
            print(f"SaveFrom error: {e}")
            return None
    
    def get_reel_video_instadownloader(self, url):
        """Method 4: Use instadownloader.co"""
        try:
            api_url = "https://www.instadownloader.co/fetch"
            payload = {
                "url": url
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://www.instadownloader.co",
                "Referer": "https://www.instadownloader.co/",
            }
            
            response = self.session.post(api_url, data=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('medias') and isinstance(data['medias'], list):
                    for media in data['medias']:
                        if media.get('url') and media['url'].startswith('http'):
                            print(f"InstaDownloader video URL: {media['url']}")
                            return media['url']
            
            return None
            
        except Exception as e:
            print(f"InstaDownloader error: {e}")
            return None
    
    def get_reel_info(self, url):
        """Get reel information using multiple methods"""
        try:
            print(f"[PROCESSING]: {url}")
            clean_url = self.remove_query_from_url(url)
            
            # Try multiple methods
            methods = [
                self.get_reel_video_direct,
                self.get_reel_video_api,
                self.get_reel_video_savefrom,
                self.get_reel_video_instadownloader
            ]
            
            download_link = None
            used_method = "Unknown"
            
            for i, method in enumerate(methods):
                print(f"Trying method {i+1}...")
                download_link = method(clean_url)
                if download_link:
                    used_method = f"Method {i+1}"
                    break
            
            if not download_link:
                return {'error': 'All download methods failed. Instagram may have blocked access.'}
            
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
                'post_url': clean_url,
                'method': used_method
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
        'version': '5.0',
        'supported_methods': ['Direct HTML', 'SnapInsta API', 'SaveFrom', 'InstaDownloader']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
