from flask import Flask, request, jsonify, render_template
import requests
import re
import json
import os
from urllib.parse import quote

app = Flask(__name__)

class SocialMediaDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })
    
    def download_instagram(self, url):
        """Instagram download using WORKING APIs"""
        try:
            # Method 1: Use instadownloader.co (FREE & WORKING)
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
                print("InstaDownloader Response:", data)  # Debug
                
                if data.get('medias') and isinstance(data['medias'], list):
                    media_urls = []
                    for media in data['medias']:
                        if media.get('url') and media['url'].startswith('http'):
                            media_urls.append(media['url'])
                    
                    if media_urls:
                        return {
                            'success': True,
                            'platform': 'instagram',
                            'media_urls': media_urls,
                            'title': data.get('title', 'Instagram Reel'),
                            'post_url': url,
                            'note': 'Click download button to save video'
                        }
            
            # Method 2: Use savefrom.net
            return self.download_instagram_savefrom(url)
            
        except Exception as e:
            return {'error': f'Instagram error: {str(e)}'}
    
    def download_instagram_savefrom(self, url):
        """Instagram download using savefrom.net"""
        try:
            api_url = "https://api.savefrom.net/api/convert"
            payload = {
                "url": url
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = self.session.post(api_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print("SaveFrom Response:", data)  # Debug
                
                if data.get('url'):
                    return {
                        'success': True,
                        'platform': 'instagram',
                        'media_urls': [data['url']],
                        'post_url': url,
                        'note': 'Using savefrom.net service'
                    }
                elif data.get('links') and isinstance(data['links'], list):
                    for link in data['links']:
                        if link.get('url'):
                            return {
                                'success': True,
                                'platform': 'instagram',
                                'media_urls': [link['url']],
                                'post_url': url,
                                'note': 'Using savefrom.net service'
                            }
            
            # Method 3: Use online downloader
            return self.download_instagram_direct(url)
            
        except Exception as e:
            return {'error': f'SaveFrom error: {str(e)}'}
    
    def download_instagram_direct(self, url):
        """Direct Instagram download using web service"""
        try:
            # Use snapinsta.app
            encoded_url = quote(url)
            api_url = f"https://snapinsta.app/api/ajaxSearch"
            
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
                print("SnapInsta Response:", data)  # Debug
                
                if data.get('data'):
                    # Extract download link from HTML response
                    html = data['data']
                    # Look for video download links
                    video_patterns = [
                        r'href="(https://[^"]*\.mp4[^"]*)"',
                        r'download_url":"([^"]+)"',
                        r'data-video="([^"]+)"'
                    ]
                    
                    for pattern in video_patterns:
                        matches = re.findall(pattern, html)
                        for match in matches:
                            video_url = match.replace('\\u0026', '&')
                            if video_url.startswith('http'):
                                return {
                                    'success': True,
                                    'platform': 'instagram',
                                    'media_urls': [video_url],
                                    'post_url': url,
                                    'note': 'Using snapinsta.app service'
                                }
            
            return {'error': 'All Instagram download methods failed. Try another URL.'}
            
        except Exception as e:
            return {'error': f'Direct download error: {str(e)}'}
    
    def download_tiktok(self, url):
        """TikTok download - MOST RELIABLE"""
        try:
            # Use tikdown.org API
            api_url = "https://tikdown.org/api/ajaxSearch"
            payload = {
                "url": url,
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://tikdown.org",
                "Referer": "https://tikdown.org/",
            }
            
            response = self.session.post(api_url, data=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    # Extract download link from HTML response
                    html = data['data']
                    download_match = re.search(r'href="(https:[^"]*\.mp4[^"]*)"', html)
                    if download_match:
                        return {
                            'success': True,
                            'platform': 'tiktok',
                            'media_urls': [download_match.group(1)],
                            'post_url': url
                        }
            
            # Alternative method
            return self.download_tiktok_alternative(url)
            
        except Exception as e:
            return {'error': f'TikTok error: {str(e)}'}
    
    def download_tiktok_alternative(self, url):
        """Alternative TikTok download"""
        try:
            api_url = "https://www.tikwm.com/api/"
            payload = {
                "url": url
            }
            
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
            
            return {'error': 'TikTok download service busy. Try again.'}
            
        except Exception as e:
            return {'error': f'TikTok alternative error: {str(e)}'}
    
    def download_media(self, url):
        """Main download function"""
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
        'version': '9.0',
        'supported_platforms': ['Instagram', 'TikTok'],
        'note': 'Using FREE working APIs - No RapidAPI'
    })

@app.route('/api/test-instagram')
def test_instagram():
    """Test endpoint for Instagram"""
    test_url = "https://www.instagram.com/reel/DRopk8PEXPn/"
    result = downloader.download_instagram(test_url)
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
