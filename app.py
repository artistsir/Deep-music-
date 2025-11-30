from flask import Flask, request, jsonify, render_template
import requests
import http.client
import json

app = Flask(__name__)

class SocialMediaDownloader:
    def __init__(self):
        self.rapidapi_key = "c39530dad2msh8aa5bb904864303p188dbbjsn30e79193a8fc"
    
    def download_instagram(self, url):
        """Instagram download using YOUR WORKING RapidAPI"""
        try:
            conn = http.client.HTTPSConnection("instagram-reels-downloader-api.p.rapidapi.com")
            encoded_url = requests.utils.quote(url, safe='')
            
            conn.request("GET", f"/download?url={encoded_url}", headers={
                'x-rapidapi-key': self.rapidapi_key,
                'x-rapidapi-host': "instagram-reels-downloader-api.p.rapidapi.com"
            })
            
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            result = json.loads(data)
            
            print("FULL API RESPONSE:", json.dumps(result, indent=2))
            
            if result.get('success') and result.get('data'):
                data = result['data']
                
                # Video URL extract karo
                video_url = None
                
                # Method 1: medias array se video URL lo
                if data.get('medias') and isinstance(data['medias'], list):
                    for media in data['medias']:
                        if media.get('type') == 'video' and media.get('url'):
                            video_url = media['url']
                            break
                
                # Method 2: Direct URL
                if not video_url and data.get('url'):
                    video_url = data['url']
                
                if video_url and video_url.startswith('http'):
                    return {
                        'success': True,
                        'platform': 'instagram',
                        'media_urls': [video_url],
                        'title': data.get('title', 'Instagram Reel'),
                        'author': data.get('author', ''),
                        'thumbnail': data.get('thumbnail', ''),
                        'post_url': url
                    }
                else:
                    return {'error': 'No video URL found in response'}
            else:
                return {'error': result.get('message', 'API request failed')}
                
        except Exception as e:
            return {'error': f'Instagram API error: {str(e)}'}
    
    def download_tiktok(self, url):
        """TikTok download"""
        try:
            api_url = "https://tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com/vid/index"
            params = {"url": url}
            headers = {
                "x-rapidapi-key": self.rapidapi_key,
                "x-rapidapi-host": "tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com"
            }
            
            response = requests.get(api_url, params=params, headers=headers, timeout=30)
            
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
            return {'error': 'Unsupported platform'}

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
        'version': '1.0',
        'supported_platforms': ['Instagram', 'TikTok']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
