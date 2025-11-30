from flask import Flask, request, jsonify, render_template
import requests
import re
import os
from urllib.parse import urlparse
import yt_dlp

app = Flask(__name__)

class SocialMediaDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_instagram(self, url):
        try:
            response = self.session.get(url)
            if response.status_code != 200:
                return {'error': 'Failed to fetch Instagram page'}
            
            media_links = self.extract_instagram_media(response.text)
            
            if not media_links:
                return {'error': 'No media found in the post'}
            
            return {
                'success': True,
                'platform': 'instagram',
                'media_count': len(media_links),
                'media_urls': media_links,
                'post_url': url
            }
        except Exception as e:
            return {'error': f'Instagram error: {str(e)}'}
    
    def extract_instagram_media(self, html_content):
        media_links = []
        patterns = [
            r'"display_url":"(https://[^"]+)"',
            r'"video_url":"(https://[^"]+)"',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                clean_url = match.replace('\\u0026', '&')
                if clean_url not in media_links:
                    media_links.append(clean_url)
        return media_links
    
    def download_youtube(self, url):
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = []
                for f in info['formats'][:5]:
                    if f.get('url'):
                        formats.append({
                            'format': f.get('format_note', 'unknown'),
                            'quality': f.get('quality', 'unknown'),
                            'url': f['url'],
                            'ext': f.get('ext', 'unknown')
                        })
                
                return {
                    'success': True,
                    'platform': 'youtube',
                    'title': info.get('title', ''),
                    'thumbnail': info.get('thumbnail', ''),
                    'duration': info.get('duration', 0),
                    'formats': formats,
                    'video_url': url
                }
        except Exception as e:
            return {'error': f'YouTube error: {str(e)}'}
    
    def download_media(self, url):
        if 'instagram.com' in url:
            return self.download_instagram(url)
        elif 'youtube.com' in url or 'youtu.be' in url:
            return self.download_youtube(url)
        else:
            return {'error': 'Unsupported platform. Use Instagram or YouTube.'}

downloader = SocialMediaDownloader()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def download_media():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    url = data['url']
    result = downloader.download_media(url)
    return jsonify(result)

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'active',
        'service': 'Social Media Downloader',
        'version': '1.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
