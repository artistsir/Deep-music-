from flask import Flask, request, jsonify, render_template
import requests
import os
import http.client
import json
import re

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
            print("RapidAPI Response:", result)  # Debug log
            
            # FIX: Different response formats handle karo
            if result.get('success') and result.get('data'):
                video_data = result['data']
                
                # Format 1: Direct video URL
                if video_data.get('url'):
                    video_url = video_data['url']
                # Format 2: Media array
                elif video_data.get('media') and isinstance(video_data['media'], list):
                    video_url = video_data['media'][0].get('url', '')
                # Format 3: Video versions
                elif video_data.get('video_versions'):
                    video_url = video_data['video_versions'][0].get('url', '')
                else:
                    # Agar URL nahi mila toh alternative method use karo
                    return self.download_instagram_alternative(url)
                
                if video_url and video_url.startswith('http'):
                    return {
                        'success': True,
                        'platform': 'instagram',
                        'media_urls': [video_url],
                        'title': video_data.get('title', 'Instagram Reel'),
                        'post_url': url
                    }
                else:
                    # Agar video URL invalid hai
                    return self.download_instagram_fallback(url)
                    
            else:
                return {'error': result.get('message', 'Instagram download failed')}
                
        except Exception as e:
            print(f"Instagram API error: {str(e)}")  # Debug log
            return {'error': f'Instagram API error: {str(e)}'}
    
    def download_instagram_fallback(self, url):
        """Fallback method for Instagram download"""
        try:
            # Use alternative free API
            api_url = "https://instagram-downloader-download-instagram-videos-stories.p.rapidapi.com/index"
            params = {
                "url": url
            }
            headers = {
                "x-rapidapi-key": self.rapidapi_key,
                "x-rapidapi-host": "instagram-downloader-download-instagram-videos-stories.p.rapidapi.com"
            }
            
            response = self.session.get(api_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print("Fallback API Response:", data)  # Debug log
                
                if data.get('media'):
                    return {
                        'success': True,
                        'platform': 'instagram',
                        'media_urls': [data['media']],
                        'post_url': url
                    }
                elif data.get('url'):
                    return {
                        'success': True,
                        'platform': 'instagram',
                        'media_urls': [data['url']],
                        'post_url': url
                    }
            
            # Last resort: Use online downloader
            return self.download_instagram_web(url)
            
        except Exception as e:
            return {'error': f'Instagram fallback error: {str(e)}'}
    
    def download_instagram_web(self, url):
        """Web-based Instagram download as last resort"""
        try:
            # Use savefrom.net
            api_url = "https://api.savefrom.net/api/convert"
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
                        'post_url': url,
                        'note': 'Using web downloader'
                    }
            
            return {'error': 'Could not download this Instagram post'}
            
        except Exception as e:
            return {'error': f'Web download error: {str(e)}'}
    
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
        'version': '8.0',
        'supported_platforms': ['Instagram', 'TikTok'],
        'note': 'Fixed Instagram download response parsing'
    })

@app.route('/api/debug-instagram')
def debug_instagram():
    """Debug endpoint to check Instagram API response"""
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter required'})
    
    try:
        conn = http.client.HTTPSConnection("instagram-reels-downloader-api.p.rapidapi.com")
        encoded_url = requests.utils.quote(url, safe='')
        
        conn.request("GET", f"/download?url={encoded_url}", headers={
            'x-rapidapi-key': "c39530dad2msh8aa5bb904864303p188dbbjsn30e79193a8fc",
            'x-rapidapi-host': "instagram-reels-downloader-api.p.rapidapi.com"
        })
        
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        result = json.loads(data)
        
        return jsonify({
            'rapidapi_response': result,
            'response_keys': list(result.keys()) if isinstance(result, dict) else 'Not a dictionary',
            'data_keys': list(result.get('data', {}).keys()) if result.get('data') else 'No data key'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
