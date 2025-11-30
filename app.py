from flask import Flask, request, jsonify, render_template
import http.client
import json
import requests
from urllib.parse import quote

app = Flask(__name__)

class InstagramDownloader:
    def __init__(self):
        # YOUR WORKING RAPIDAPI KEY
        self.rapidapi_key = "c39530dad2msh8aa5bb904864303p188dbbjsn30e79193a8fc"
    
    def get_shortcode(self, url):
        """Extract shortcode from Instagram URL"""
        if '/reel/' in url:
            return url.split('/reel/')[1].split('/')[0].split('?')[0]
        elif '/p/' in url:
            return url.split('/p/')[1].split('/')[0].split('?')[0]
        else:
            parts = url.split('/')
            for part in parts:
                if len(part) == 11 and not '?' in part:
                    return part
            return None

    def check_api_balance(self):
        """Check RapidAPI balance"""
        try:
            conn = http.client.HTTPSConnection("instagram-premium-api-2023.p.rapidapi.com")
            conn.request("GET", "/sys/balance", headers={
                'x-rapidapi-key': self.rapidapi_key,
                'x-rapidapi-host': "instagram-premium-api-2023.p.rapidapi.com"
            })
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            result = json.loads(data)
            print(f"API Balance: {result}")
            return result
        except Exception as e:
            print(f"Balance check error: {e}")
            return None

    def download_instagram_method1(self, url):
        """Method 1: Instagram Premium API"""
        try:
            shortcode = self.get_shortcode(url)
            if not shortcode:
                return None
                
            conn = http.client.HTTPSConnection("instagram-premium-api-2023.p.rapidapi.com")
            conn.request("GET", f"/media?shortcode={shortcode}", headers={
                'x-rapidapi-key': self.rapidapi_key,
                'x-rapidapi-host': "instagram-premium-api-2023.p.rapidapi.com"
            })
            
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            result = json.loads(data)
            print("Method 1 Response:", result)
            
            if result.get('items') and len(result['items']) > 0:
                item = result['items'][0]
                if item.get('video_versions'):
                    video_url = item['video_versions'][0]['url']
                    return {
                        'success': True,
                        'media_urls': [video_url],
                        'title': item.get('caption', {}).get('text', 'Instagram Reel'),
                        'author': item.get('user', {}).get('username', ''),
                        'method': 'Premium API'
                    }
            return None
            
        except Exception as e:
            print(f"Method 1 error: {e}")
            return None

    def download_instagram_method2(self, url):
        """Method 2: Instagram Downloader API"""
        try:
            encoded_url = quote(url)
            conn = http.client.HTTPSConnection("instagram-downloader-download-instagram-videos-stories1.p.rapidapi.com")
            conn.request("GET", f"/?url={encoded_url}", headers={
                'x-rapidapi-key': self.rapidapi_key,
                'x-rapidapi-host': "instagram-downloader-download-instagram-videos-stories1.p.rapidapi.com"
            })
            
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            result = json.loads(data)
            print("Method 2 Response:", result)
            
            if result.get('media'):
                return {
                    'success': True,
                    'media_urls': [result['media']],
                    'title': result.get('title', 'Instagram Reel'),
                    'author': result.get('author', ''),
                    'method': 'Downloader API'
                }
            return None
            
        except Exception as e:
            print(f"Method 2 error: {e}")
            return None

    def download_instagram_method3(self, url):
        """Method 3: Fast Reliable Scraper API"""
        try:
            shortcode = self.get_shortcode(url)
            if not shortcode:
                return None
                
            conn = http.client.HTTPSConnection("instagram-api-fast-reliable-data-scraper.p.rapidapi.com")
            conn.request("GET", f"/clip_info_by_shortcode?shortcode={shortcode}", headers={
                'x-rapidapi-key': self.rapidapi_key,
                'x-rapidapi-host': "instagram-api-fast-reliable-data-scraper.p.rapidapi.com"
            })
            
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            result = json.loads(data)
            print("Method 3 Response:", result)
            
            if result.get('video_url'):
                return {
                    'success': True,
                    'media_urls': [result['video_url']],
                    'title': result.get('title', 'Instagram Reel'),
                    'author': result.get('owner', {}).get('username', ''),
                    'method': 'Fast Scraper API'
                }
            return None
            
        except Exception as e:
            print(f"Method 3 error: {e}")
            return None

    def download_instagram_method4(self, url):
        """Method 4: Alternative Downloader API"""
        try:
            encoded_url = quote(url)
            conn = http.client.HTTPSConnection("instagram-downloader-download-instagram-videos-stories.p.rapidapi.com")
            conn.request("GET", f"/index?url={encoded_url}", headers={
                'x-rapidapi-key': self.rapidapi_key,
                'x-rapidapi-host': "instagram-downloader-download-instagram-videos-stories.p.rapidapi.com"
            })
            
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            result = json.loads(data)
            print("Method 4 Response:", result)
            
            if result.get('media'):
                return {
                    'success': True,
                    'media_urls': [result['media']],
                    'title': result.get('title', 'Instagram Reel'),
                    'author': result.get('author', ''),
                    'method': 'Alternative API'
                }
            return None
            
        except Exception as e:
            print(f"Method 4 error: {e}")
            return None

    def download_instagram(self, url):
        """Main download function - tries all methods"""
        try:
            print(f"[PROCESSING]: {url}")
            
            # First check API balance
            balance = self.check_api_balance()
            print(f"API Balance Status: {balance}")
            
            # Try all methods
            methods = [
                self.download_instagram_method1,
                self.download_instagram_method2, 
                self.download_instagram_method3,
                self.download_instagram_method4
            ]
            
            for i, method in enumerate(methods):
                print(f"Trying Method {i+1}...")
                result = method(url)
                if result and result.get('success'):
                    result['platform'] = 'instagram'
                    result['post_url'] = url
                    result['all_methods'] = len(methods)
                    result['used_method'] = i + 1
                    return result
            
            return {'error': 'All RapidAPI methods failed. Please try another URL.'}
            
        except Exception as e:
            return {'error': f'Download error: {str(e)}'}

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
        result = downloader.download_instagram(url)
    else:
        result = {'error': 'Only Instagram supported'}
    
    return jsonify(result)

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'active',
        'service': 'Instagram Reel Downloader',
        'version': '7.0',
        'rapidapi_methods': 4,
        'features': ['Auto Balance Check', 'Multiple APIs', 'Auto Retry']
    })

@app.route('/api/balance')
def check_balance():
    """Check RapidAPI balance"""
    balance = downloader.check_api_balance()
    return jsonify({'rapidapi_balance': balance})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
