from flask import Flask, request, jsonify, render_template
import requests
import os
import http.client
import json

app = Flask(__name__)

class SocialMediaDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # Your RapidAPI Key
        self.rapidapi_key = "c39530dad2msh8aa5bb904864303p188dbbjsn30e79193a8fc"
    
    def download_instagram(self, url):
        """Instagram download using YOUR WORKING RapidAPI"""
        try:
            # Use the exact API you provided
            conn = http.client.HTTPSConnection("instagram-reels-downloader-api.p.rapidapi.com")
            
            # URL encode the Instagram URL
            encoded_url = requests.utils.quote(url, safe='')
            
            # Make the API request
            conn.request("GET", f"/download?url={encoded_url}", headers={
                'x-rapidapi-key': self.rapidapi_key,
                'x-rapidapi-host': "instagram-reels-downloader-api.p.rapidapi.com"
            })
            
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            
            # Parse the response
            result = json.loads(data)
            
            if result.get('success') and result.get('data'):
                video_url = result['data'].get('url')
                if video_url:
                    return {
                        'success': True,
                        'platform': 'instagram',
                        'media_urls': [video_url],
                        'title': result['data'].get('title', 'Instagram Reel'),
                        'post_url': url
                    }
            else:
                return {'error': result.get('message', 'Instagram download failed')}
                
        except Exception as e:
            return {'error': f'Instagram API error: {str(e)}'}
    
    def download_instagram_alternative(self, url):
        """Alternative method if main API fails"""
        try:
            # Alternative free method
            api_url = "https://insta-downloader-youtube.p.rapidapi.com/index"
            params = {
                "url": url
            }
            headers = {
                "x-rapidapi-key": self.rapidapi_key,
                "x-rapidapi-host": "insta-downloader-youtube.p.rapidapi.com"
            }
            
            response = self.session.get(api_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('media'):
                    return {
                        'success': True,
                        'platform': 'instagram',
                        'media_urls': [data['media']],
                        'post_url': url
                    }
            
            return {'error': 'Instagram download not available'}
            
        except Exception as e:
            return {'error': f'Instagram alternative error: {str(e)}'}
    
    def download_tiktok(self, url):
        """TikTok download"""
        try:
            api_url = "https://tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com/vid/index"
            params = {
                "url": url
            }
            headers = {
                "x-rapidapi-key": self.rapidapi_key,
                "x-rapidapi-host": "tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com"
            }
            
            response = self.session.get(api_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('video'):
                    return {
                        'success': True,
                        'platform': 'tiktok',
                        'media_urls': [data['video'][0]],
                        'title': data.get('title', 'TikTok Video'),
                        'post_url': url
                    }
                elif data.get('wmplay'):
                    return {
                        'success': True,
                        'platform': 'tiktok',
                        'media_urls': [data['wmplay']],
                        'post_url': url
                    }
            
            return {'error': 'TikTok download failed'}
            
        except Exception as e:
            return {'error': f'TikTok error: {str(e)}'}
    
    def download_youtube(self, url):
        """YouTube download using RapidAPI"""
        try:
            api_url = "https://youtube-media-downloader.p.rapidapi.com/v2/video/details"
            params = {
                "videoId": self.extract_youtube_id(url)
            }
            headers = {
                "x-rapidapi-key": self.rapidapi_key,
                "x-rapidapi-host": "youtube-media-downloader.p.rapidapi.com"
            }
            
            response = self.session.get(api_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('videos'):
                    # Get the highest quality video
                    videos = data['videos']['items']
                    if videos:
                        best_quality = max(videos, key=lambda x: x.get('quality', 0))
                        return {
                            'success': True,
                            'platform': 'youtube',
                            'media_urls': [best_quality['url']],
                            'title': data.get('title', 'YouTube Video'),
                            'post_url': url
                        }
            
            return {'error': 'YouTube download failed'}
            
        except Exception as e:
            return {'error': f'YouTube error: {str(e)}'}
    
    def extract_youtube_id(self, url):
        """Extract YouTube video ID from URL"""
        if 'youtu.be/' in url:
            return url.split('youtu.be/')[1].split('?')[0]
        elif 'youtube.com/watch?v=' in url:
            return url.split('v=')[1].split('&')[0]
        else:
            return url
    
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
        'version': '7.0',
        'supported_platforms': ['Instagram', 'TikTok', 'YouTube'],
        'note': 'Using RapidAPI - PROPER WORKING'
    })

@app.route('/test-instagram')
def test_instagram():
    """Test Instagram download with your API"""
    test_url = "https://www.instagram.com/reel/DJg8Hc_zkot/"
    result = downloader.download_instagram(test_url)
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
