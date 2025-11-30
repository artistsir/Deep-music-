from flask import Flask, request, jsonify, render_template
import requests
import re
import os
from urllib.parse import urlparse, parse_qs
import json

app = Flask(__name__)

class SocialMediaDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def download_instagram(self, url):
        """Instagram download using alternative API"""
        try:
            # Use instagram-scraper API
            api_url = "https://downloadgram.org/wp-json/wppress/v2/downloader"
            payload = {
                "url": url,
                "token": ""
            }
            
            response = self.session.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('media'):
                    return {
                        'success': True,
                        'platform': 'instagram',
                        'media_urls': [data['media']],
                        'post_url': url
                    }
            
            # Alternative method
            return self.download_instagram_direct(url)
            
        except Exception as e:
            return {'error': f'Instagram error: {str(e)}'}
    
    def download_instagram_direct(self, url):
        """Direct Instagram scraping"""
        try:
            response = self.session.get(url, timeout=30)
            
            # Multiple patterns try karte hain
            patterns = [
                r'"display_url":"([^"]+)"',
                r'"video_url":"([^"]+)"',
                r'src="([^"]+mp4[^"]*)"',
                r'content="([^"]+mp4[^"]*)"'
            ]
            
            media_links = []
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    clean_url = match.replace('\\u0026', '&').replace('\\', '')
                    if clean_url.startswith('http') and clean_url not in media_links:
                        media_links.append(clean_url)
            
            if media_links:
                return {
                    'success': True,
                    'platform': 'instagram',
                    'media_count': len(media_links),
                    'media_urls': media_links,
                    'post_url': url
                }
            else:
                return {'error': 'No media found. Try different post.'}
                
        except Exception as e:
            return {'error': f'Instagram direct error: {str(e)}'}
    
    def download_youtube(self, url):
        """YouTube download using alternative APIs"""
        try:
            # Method 1: y2mate API
            api_url = "https://y2mate.com/mates/analyzeV2/ajax"
            payload = {
                "k_query": url,
                "k_page": "home",
                "hl": "en",
                "q_auto": 0
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "X-Requested-With": "XMLHttpRequest"
            }
            
            response = self.session.post(api_url, data=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('links'):
                    formats = []
                    for quality, info in data['links'].items():
                        if isinstance(info, dict) and info.get('dlink'):
                            formats.append({
                                'quality': quality,
                                'url': info['dlink'],
                                'format': info.get('f', 'mp4'),
                                'size': info.get('size', 'Unknown')
                            })
                    
                    if formats:
                        return {
                            'success': True,
                            'platform': 'youtube',
                            'formats': formats[:5],  # Limit to 5 formats
                            'video_url': url
                        }
            
            # Method 2: Simple API fallback
            return self.download_youtube_simple(url)
            
        except Exception as e:
            return {'error': f'YouTube error: {str(e)}'}
    
    def download_youtube_simple(self, url):
        """Simple YouTube download using external service"""
        try:
            # Use savefrom.net API
            api_url = f"https://api.savefrom.net/service/convert"
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
            
            return {'error': 'YouTube download not available'}
            
        except Exception as e:
            return {'error': f'YouTube simple error: {str(e)}'}
    
    def download_tiktok(self, url):
        """TikTok download - yeh better work karta hai"""
        try:
            api_url = "https://www.tikwm.com/api/"
            payload = {
                "url": url,
                "count": 12,
                "cursor": 0,
                "web": 1,
                "hd": 1
            }
            
            response = self.session.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    video_url = data['data'].get('play')
                    if video_url:
                        if not video_url.startswith('http'):
                            video_url = 'https:' + video_url
                            
                        return {
                            'success': True,
                            'platform': 'tiktok',
                            'media_urls': [video_url],
                            'post_url': url
                        }
            
            return {'error': 'TikTok download failed'}
            
        except Exception as e:
            return {'error': f'TikTok error: {str(e)}'}
    
    def download_media(self, url):
        """Main download function"""
        if 'instagram.com' in url or 'instagr.am' in url:
            return self.download_instagram(url)
        elif 'youtube.com' in url or 'youtu.be' in url:
            return self.download_youtube(url)
        elif 'tiktok.com' in url:
            return self.download_tiktok(url)
        else:
            return {'error': 'Unsupported platform. Use Instagram, YouTube, or TikTok.'}

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
        'version': '2.0',
        'supported_platforms': ['Instagram', 'YouTube', 'TikTok']
    })

@app.route('/test')
def test():
    return jsonify({'message': 'API is working!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
