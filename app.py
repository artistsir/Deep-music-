from flask import Flask, request, jsonify, render_template
import requests
import re
import os
import json

app = Flask(__name__)

class SocialMediaDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def download_youtube(self, url):
        """YouTube download using working APIs"""
        try:
            # Use savetube.io API
            api_url = "https://api.savetube.io/api/v1/download"
            payload = {
                "url": url
            }
            
            response = self.session.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('url'):
                    return {
                        'success': True,
                        'platform': 'youtube',
                        'formats': [{
                            'quality': 'HD',
                            'url': data['url'],
                            'format': 'mp4',
                            'size': 'Unknown'
                        }],
                        'video_url': url
                    }
            
            # Fallback to y2mate
            return self.download_youtube_y2mate(url)
            
        except Exception as e:
            return {'error': f'YouTube error: {str(e)}'}
    
    def download_youtube_y2mate(self, url):
        """YouTube download using y2mate"""
        try:
            api_url = "https://api.y2mate.guru/api/convert"
            payload = {
                "url": url
            }
            
            response = self.session.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('url'):
                    return {
                        'success': True,
                        'platform': 'youtube',
                        'formats': [{
                            'quality': data.get('quality', 'HD'),
                            'url': data['url'],
                            'format': 'mp4',
                            'size': data.get('size', 'Unknown')
                        }],
                        'video_url': url
                    }
            
            return {'error': 'YouTube download service is temporarily unavailable'}
            
        except Exception as e:
            return {'error': f'YouTube fallback error: {str(e)}'}
    
    def download_tiktok(self, url):
        """TikTok download - most reliable"""
        try:
            # Method 1: tikwm API
            api_url = "https://www.tikwm.com/api/"
            payload = {
                "url": url,
                "hd": 1
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = self.session.post(api_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    video_data = data['data']
                    video_url = video_data.get('play')
                    
                    if video_url:
                        if not video_url.startswith('http'):
                            video_url = 'https:' + video_url
                            
                        return {
                            'success': True,
                            'platform': 'tiktok',
                            'media_urls': [video_url],
                            'title': video_data.get('title', 'TikTok Video'),
                            'author': video_data.get('author', {}).get('nickname', 'Unknown'),
                            'post_url': url
                        }
            
            # Method 2: ssstik API
            return self.download_tiktok_ssstik(url)
            
        except Exception as e:
            return {'error': f'TikTok error: {str(e)}'}
    
    def download_tiktok_ssstik(self, url):
        """TikTok download using ssstik.io"""
        try:
            api_url = "https://ssstik.io/abc?url=dl"
            payload = {
                "id": url,
                "locale": "en",
                "tt": ""  # This might need a token
            }
            
            response = self.session.post(api_url, data=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('links'):
                    return {
                        'success': True,
                        'platform': 'tiktok', 
                        'media_urls': [data['links']],
                        'post_url': url
                    }
            
            return {'error': 'TikTok download failed. Try another video.'}
            
        except Exception as e:
            return {'error': f'TikTok fallback error: {str(e)}'}
    
    def download_facebook(self, url):
        """Facebook download"""
        try:
            api_url = "https://getmyfb.com/process"
            payload = {
                "id": url,
                "locale": "en"
            }
            
            response = self.session.post(api_url, data=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('url'):
                    return {
                        'success': True,
                        'platform': 'facebook',
                        'media_urls': [data['url']],
                        'post_url': url
                    }
            
            return {'error': 'Facebook download not available'}
            
        except Exception as e:
            return {'error': f'Facebook error: {str(e)}'}
    
    def download_media(self, url):
        """Main download function - Instagram removed"""
        if 'tiktok.com' in url:
            return self.download_tiktok(url)
        elif 'youtube.com' in url or 'youtu.be' in url:
            return self.download_youtube(url)
        elif 'facebook.com' in url or 'fb.watch' in url:
            return self.download_facebook(url)
        else:
            return {'error': 'Unsupported platform. Use TikTok, YouTube, or Facebook.'}

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
        'version': '3.0',
        'supported_platforms': ['TikTok', 'YouTube', 'Facebook'],
        'note': 'Instagram temporarily disabled due to restrictions'
    })

@app.route('/test')
def test():
    return jsonify({'message': 'API is working!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
