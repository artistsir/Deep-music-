from flask import Flask, request, jsonify, render_template
import requests
import os

app = Flask(__name__)

class SocialMediaDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # RapidAPI Key - YOU NEED TO GET THIS FROM RAPIDAPI.COM
        self.rapidapi_key = os.environ.get('RAPIDAPI_KEY', 'YOUR_RAPIDAPI_KEY_HERE')
    
    def download_instagram(self, url):
        """Instagram download using RapidAPI - PROPER WORKING"""
        try:
            # Extract Reel ID from URL
            if '/reel/' in url:
                reel_id = url.split('/reel/')[1].split('/')[0].split('?')[0]
            elif '/p/' in url:
                reel_id = url.split('/p/')[1].split('/')[0].split('?')[0]
            else:
                return {'error': 'Invalid Instagram URL format'}
            
            # RapidAPI endpoint
            api_url = "https://instagram-social-api.p.rapidapi.com/v1/post_info"
            params = {
                "code_or_id_or_url": reel_id
            }
            headers = {
                "x-rapidapi-key": self.rapidapi_key,
                "x-rapidapi-host": "instagram-social-api.p.rapidapi.com"
            }
            
            response = self.session.get(api_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('data') and data['data'].get('video_versions'):
                    video_url = data['data']['video_versions'][0]['url']
                    return {
                        'success': True,
                        'platform': 'instagram',
                        'media_urls': [video_url],
                        'title': data['data'].get('caption', {}).get('text', 'Instagram Reel'),
                        'post_url': url
                    }
                elif data.get('data') and data['data'].get('image_versions2'):
                    image_url = data['data']['image_versions2']['candidates'][0]['url']
                    return {
                        'success': True,
                        'platform': 'instagram',
                        'media_urls': [image_url],
                        'title': data['data'].get('caption', {}).get('text', 'Instagram Post'),
                        'post_url': url
                    }
                else:
                    return {'error': 'No media found in this post'}
            else:
                return {'error': f'API Error: {response.status_code}'}
                
        except Exception as e:
            return {'error': f'Instagram error: {str(e)}'}
    
    def download_tiktok(self, url):
        """TikTok download"""
        try:
            api_url = "https://tikwm.com/api/"
            payload = {"url": url}
            
            response = self.session.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and data['data'].get('play'):
                    video_url = data['data']['play']
                    if not video_url.startswith('http'):
                        video_url = 'https:' + video_url
                    
                    return {
                        'success': True,
                        'platform': 'tiktok',
                        'media_urls': [video_url],
                        'title': data['data'].get('title', 'TikTok Video'),
                        'post_url': url
                    }
            
            return {'error': 'TikTok download failed'}
            
        except Exception as e:
            return {'error': f'TikTok error: {str(e)}'}
    
    def download_media(self, url):
        if 'instagram.com' in url:
            return self.download_instagram(url)
        elif 'tiktok.com' in url:
            return self.download_tiktok(url)
        else:
            return {'error': 'Unsupported platform. Use Instagram or TikTok.'}

downloader = SocialMediaDownloader()

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
    
    result = downloader.download_media(url)
    return jsonify(result)

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'active',
        'service': 'Social Media Downloader',
        'version': '5.0',
        'supported_platforms': ['Instagram', 'TikTok'],
        'note': 'Instagram uses RapidAPI - requires API key'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
