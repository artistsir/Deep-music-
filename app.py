from flask import Flask, request, jsonify, render_template
import requests
import re
import json
import os
from urllib.parse import unquote

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
    
    def download_instagram(self, url):
        """Instagram download using FREE methods"""
        try:
            # Method 1: Use instadownloader.co
            api_url = "https://www.instadownloader.co/fetch"
            payload = {
                "url": url
            }
            
            response = self.session.post(api_url, data=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('medias'):
                    media_urls = []
                    for media in data['medias']:
                        if media.get('url'):
                            media_urls.append(media['url'])
                    
                    if media_urls:
                        return {
                            'success': True,
                            'platform': 'instagram',
                            'media_urls': media_urls,
                            'post_url': url,
                            'note': 'Click download button to save media'
                        }
            
            # Method 2: Use savefrom.net
            return self.download_instagram_savefrom(url)
            
        except Exception as e:
            return {'error': f'Instagram error: {str(e)}'}
    
    def download_instagram_savefrom(self, url):
        """Instagram download using savefrom.net"""
        try:
            api_url = "https://api.savefrom.net/service/convert"
            payload = {
                "url": url
            }
            
            response = self.session.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('url'):
                    return {
                        'success': True,
                        'platform': 'instagram',
                        'media_urls': [data['url']],
                        'post_url': url
                    }
            
            # Method 3: Direct HTML parsing
            return self.download_instagram_direct(url)
            
        except Exception as e:
            return {'error': f'Instagram savefrom error: {str(e)}'}
    
    def download_instagram_direct(self, url):
        """Direct Instagram download using HTML parsing"""
        try:
            # Add ?__a=1 to get JSON data
            json_url = url + "?__a=1&__d=dis"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Referer': 'https://www.instagram.com/',
            }
            
            response = self.session.get(json_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract media from JSON response
                media_urls = []
                
                # For single image/video posts
                if 'graphql' in data:
                    post = data['graphql']['shortcode_media']
                    if post['is_video']:
                        media_urls.append(post['video_url'])
                    else:
                        media_urls.append(post['display_url'])
                
                # For carousel posts
                elif 'items' in data:
                    for item in data['items']:
                        if 'video_versions' in item:
                            media_urls.append(item['video_versions'][0]['url'])
                        elif 'image_versions2' in item:
                            media_urls.append(item['image_versions2']['candidates'][0]['url'])
                
                if media_urls:
                    return {
                        'success': True,
                        'platform': 'instagram',
                        'media_urls': media_urls,
                        'post_url': url
                    }
            
            return {'error': 'Could not download this Instagram post. Try another URL.'}
            
        except Exception as e:
            return {'error': f'Instagram direct error: {str(e)}'}
    
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
    
    def download_youtube(self, url):
        """YouTube download using free services"""
        try:
            # Use y2mate.guru API
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
                        'media_urls': [data['url']],
                        'title': data.get('title', 'YouTube Video'),
                        'post_url': url
                    }
            
            return {'error': 'YouTube service temporarily unavailable'}
            
        except Exception as e:
            return {'error': f'YouTube error: {str(e)}'}
    
    def download_media(self, url):
        """Main download function"""
        if 'instagram.com' in url:
            return self.download_instagram(url)
        elif 'tiktok.com' in url:
            return self.download_tiktok(url)
        elif 'youtube.com' in url or 'youtu.be' in url:
            return self.download_youtube(url)
        else:
            return {'error': 'Unsupported platform. Use Instagram, TikTok, or YouTube.'}

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
        'version': '6.0',
        'supported_platforms': ['Instagram', 'TikTok', 'YouTube'],
        'note': 'Using free APIs - no RapidAPI key required'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
