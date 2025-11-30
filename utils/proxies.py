import requests
import os
import uuid
import time
import random
import re
import json
from urllib.parse import urlparse, unquote
import logging

logger = logging.getLogger(__name__)

class ReelDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.setup_headers()
    
    def setup_headers(self):
        """Setup realistic headers to avoid detection"""
        self.headers_list = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
            }
        ]
    
    def get_random_headers(self):
        return random.choice(self.headers_list)
    
    def download_file(self, url, filepath, proxy=None):
        """Download file with retry mechanism"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                headers = self.get_random_headers()
                proxies = {'http': proxy, 'https': proxy} if proxy else None
                
                response = self.session.get(
                    url, 
                    headers=headers, 
                    proxies=proxies,
                    stream=True,
                    timeout=30
                )
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Verify file was downloaded
                if os.path.getsize(filepath) > 0:
                    return True
                else:
                    os.remove(filepath)
                    return False
                    
            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return False
    
    def extract_instagram_reel(self, url, download_folder):
        """Extract Instagram reel using multiple methods"""
        try:
            # Method 1: Use instagram-scraper alternative approach
            return self.extract_instagram_direct(url, download_folder)
        except Exception as e:
            logger.error(f"Instagram extraction failed: {str(e)}")
            return None
    
    def extract_instagram_direct(self, url, download_folder):
        """Direct Instagram extraction method"""
        try:
            # This would use Instagram's private API or alternative methods
            # For now, we'll use a simplified approach
            
            headers = self.get_random_headers()
            response = self.session.get(url, headers=headers, timeout=15)
            
            # Look for video URLs in the HTML
            video_patterns = [
                r'"video_url":"([^"]+)"',
                r'content="[^"]*video_url[^"]*" content="([^"]+)"',
                r'src="([^"]+\.mp4[^"]*)"',
            ]
            
            for pattern in video_patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    video_url = match.replace('\\u0025', '%').replace('\\u0026', '&')
                    if '.mp4' in video_url:
                        return video_url
            
            return None
            
        except Exception as e:
            logger.error(f"Direct extraction failed: {str(e)}")
            return None
    
    def extract_facebook_reel(self, url, download_folder):
        """Extract Facebook reel"""
        try:
            headers = self.get_random_headers()
            response = self.session.get(url, headers=headers, timeout=15)
            
            # Look for video URLs in Facebook's JSON structure
            video_patterns = [
                r'"video_url":"([^"]+)"',
                r'hd_src:"([^"]+)"',
                r'sd_src:"([^"]+)"',
                r'content="[^"]*video:url[^"]*" content="([^"]+)"',
            ]
            
            for pattern in video_patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    video_url = unquote(match.replace('\\u0025', '%').replace('\\u0026', '&'))
                    if any(ext in video_url.lower() for ext in ['.mp4', '.mov', '.avi']):
                        return video_url
            
            return None
            
        except Exception as e:
            logger.error(f"Facebook extraction failed: {str(e)}")
            return None

def download_reel_advanced(url, download_folder, proxy=None):
    """Main download function with advanced features"""
    downloader = ReelDownloader()
    
    try:
        # Generate unique filename
        filename = f"reel_{uuid.uuid4().hex}.mp4"
        filepath = os.path.join(download_folder, filename)
        
        logger.info(f"Starting download process for: {url}")
        
        # Determine platform and extract video URL
        video_url = None
        
        if 'instagram.com' in url:
            logger.info("Detected Instagram URL")
            video_url = downloader.extract_instagram_reel(url, download_folder)
        elif 'facebook.com' in url or 'fb.watch' in url:
            logger.info("Detected Facebook URL")
            video_url = downloader.extract_facebook_reel(url, download_folder)
        
        if not video_url:
            # Fallback: Use yt-dlp if available
            try:
                return download_with_ytdlp(url, download_folder)
            except Exception as e:
                logger.error(f"yt-dlp fallback failed: {str(e)}")
                return {
                    "success": False,
                    "error": "Could not extract video URL. The reel might be private or unavailable."
                }
        
        logger.info(f"Extracted video URL: {video_url[:100]}...")
        
        # Download the video
        success = downloader.download_file(video_url, filepath, proxy)
        
        if success and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            file_size = os.path.getsize(filepath)
            
            return {
                "success": True,
                "filename": filename,
                "filepath": filepath,
                "file_size": file_size,
                "message": "Download completed successfully"
            }
        else:
            if os.path.exists(filepath):
                os.remove(filepath)
            return {
                "success": False,
                "error": "Download failed or file is empty"
            }
            
    except Exception as e:
        logger.error(f"Advanced download failed: {str(e)}")
        return {
            "success": False,
            "error": f"Download failed: {str(e)}"
        }

def download_with_ytdlp(url, download_folder):
    """Fallback method using yt-dlp"""
    try:
        import yt_dlp
        
        ydl_opts = {
            'outtmpl': os.path.join(download_folder, '%(title)s_%(id)s.%(ext)s'),
            'format': 'best[height<=720]',
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        return {
            "success": True,
            "filename": os.path.basename(filename),
            "filepath": filename,
            "duration": info.get('duration', 'Unknown'),
            "thumbnail": info.get('thumbnail', '')
        }
        
    except Exception as e:
        logger.error(f"yt-dlp download failed: {str(e)}")
        raise e
