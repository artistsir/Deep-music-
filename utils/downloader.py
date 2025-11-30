import os
import uuid
import time
import logging
import random
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def download_reel_with_cookies(url, download_folder, cookies_folder):
    """
    Download reel using cookies to bypass login requirements
    """
    try:
        import yt_dlp
        
        logger.info(f"Attempting download with cookies: {url}")
        
        filename = f"reel_{uuid.uuid4().hex}.mp4"
        filepath = os.path.join(download_folder, filename)
        
        # Find available cookies files
        cookies_file = find_best_cookies(cookies_folder, url)
        
        # Advanced yt-dlp configuration with cookie support
        ydl_opts = build_ydl_options(filepath, cookies_file)
        
        logger.info(f"Using cookies: {cookies_file}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return {
                        "success": False, 
                        "error": "Could not extract video information",
                        "solution": "The reel might be private or unavailable"
                    }
                
                logger.info(f"Video info extracted: {info.get('title', 'Unknown')}")
                
                # Download the video
                ydl.download([url])
                
                # Find the actual downloaded file
                actual_filepath = find_downloaded_file(ydl.prepare_filename(info), download_folder)
                
                if not actual_filepath:
                    return {
                        "success": False,
                        "error": "Downloaded file not found",
                        "solution": "Try again or use different cookies"
                    }
                
                # Rename to final filename
                final_filepath = os.path.join(download_folder, filename)
                if actual_filepath != final_filepath:
                    if os.path.exists(final_filepath):
                        os.remove(final_filepath)
                    os.rename(actual_filepath, final_filepath)
                
                # Verify download
                if os.path.exists(final_filepath) and os.path.getsize(final_filepath) > 1024:  # At least 1KB
                    file_size = os.path.getsize(final_filepath)
                    
                    return {
                        "success": True,
                        "filename": filename,
                        "filepath": final_filepath,
                        "file_size": file_size,
                        "title": info.get('title', 'reel'),
                        "duration": format_duration(info.get('duration')),
                        "thumbnail": info.get('thumbnail'),
                        "quality": info.get('format_note', 'HD'),
                        "message": "Download completed with cookie authentication"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Downloaded file is empty or too small",
                        "solution": "The cookies might be invalid or expired"
                    }
                    
            except yt_dlp.utils.DownloadError as e:
                error_msg = str(e)
                logger.error(f"DownloadError: {error_msg}")
                
                return handle_download_error(error_msg, cookies_file)
                
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "success": False,
            "error": f"Download failed: {str(e)}",
            "solution": "Try again later or contact support"
        }

def build_ydl_options(filepath, cookies_file):
    """Build optimized yt-dlp options with cookie support"""
    
    # Default headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    ydl_opts = {
        # Output
        'outtmpl': filepath.replace('.mp4', '') + '.%(ext)s',
        
        # Format selection
        'format': 'best[height<=1080]/best[ext=mp4]/best',
        'format_sort': ['res:1080', 'ext:mp4', 'acodec:mp4a'],
        
        # Cookies
        'cookiefile': cookies_file,
        'cookiesfrombrowser': get_browser_cookies_config(),
        
        # Download settings
        'retries': 20,
        'fragment_retries': 20,
        'skip_unavailable_fragments': True,
        'continue_dl': True,
        
        # Timeouts
        'socket_timeout': 60,
        'retry_sleep': 2,
        
        # Rate limiting
        'ratelimit': 1500000,
        'throttledratelimit': 3000000,
        
        # Headers
        'http_headers': headers,
        
        # Extractor args
        'extractor_args': {
            'instagram': {
                'format': 'best',
                'feed': {'endpoints': False},
                'client': {'endpoints': False},
                'cookies': {'required': True},
            },
            'facebook': {
                'format': 'best',
                'cookies': {'required': True},
            }
        },
        
        # Verbosity
        'quiet': False,
        'no_warnings': False,
        
        # Progress hooks
        'progress_hooks': [lambda d: progress_hook(d)],
        
        # Post-processing
        'postprocessors': [],
    }
    
    return ydl_opts

def get_browser_cookies_config():
    """Configuration for browser cookies fallback"""
    return {
        'chrome': None,  # Auto-detect Chrome
        'firefox': None, # Auto-detect Firefox
        'edge': None,    # Auto-detect Edge
    }

def find_best_cookies(cookies_folder, url):
    """Find the best cookies file for the given URL"""
    try:
        cookies_files = []
        
        # Look for cookies files
        for file in os.listdir(cookies_folder):
            if file.endswith('.txt'):
                cookies_files.append(os.path.join(cookies_folder, file))
        
        # If no cookies files, return None (yt-dlp will try browser cookies)
        if not cookies_files:
            logger.info("No cookies files found, using browser cookies")
            return None
        
        # Prioritize platform-specific cookies
        if 'instagram.com' in url:
            for cookie_file in cookies_files:
                if 'instagram' in cookie_file.lower():
                    return cookie_file
        
        elif 'facebook.com' in url:
            for cookie_file in cookies_files:
                if 'facebook' in cookie_file.lower():
                    return cookie_file
        
        # Return the most recent cookies file
        most_recent = max(cookies_files, key=os.path.getctime)
        logger.info(f"Using most recent cookies: {most_recent}")
        return most_recent
        
    except Exception as e:
        logger.error(f"Error finding cookies: {str(e)}")
        return None

def handle_download_error(error_msg, cookies_file):
    """Handle specific download errors and provide solutions"""
    
    error_lower = error_msg.lower()
    
    if 'login required' in error_lower or 'private' in error_lower:
        return {
            "success": False,
            "error": "Login required - Private account or content",
            "solution": f"Upload valid cookies file. Current cookies: {cookies_file}"
        }
    
    elif 'age restriction' in error_lower:
        return {
            "success": False,
            "error": "Age-restricted content",
            "solution": "Cannot download age-restricted content"
        }
    
    elif 'not found' in error_lower or 'removed' in error_lower:
        return {
            "success": False,
            "error": "Reel not found or has been removed",
            "solution": "Check the URL and try another reel"
        }
    
    elif 'cookies' in error_lower:
        return {
            "success": False,
            "error": "Invalid or expired cookies",
            "solution": "Upload fresh cookies file or try browser authentication"
        }
    
    elif 'rate limit' in error_lower:
        return {
            "success": False,
            "error": "Rate limit exceeded",
            "solution": "Wait a few minutes and try again"
        }
    
    else:
        return {
            "success": False,
            "error": f"Download failed: {error_msg}",
            "solution": "Try again with different cookies or contact support"
        }

def find_downloaded_file(temp_path, download_folder):
    """Find the actual downloaded file"""
    try:
        # If temp file exists, return it
        if os.path.exists(temp_path):
            return temp_path
        
        # Look for files with similar base name
        base_name = os.path.basename(temp_path).split('.')[0]
        for file in os.listdir(download_folder):
            if file.startswith(base_name):
                return os.path.join(download_folder, file)
        
        # Look for recent MP4 files
        recent_files = []
        for file in os.listdir(download_folder):
            if file.endswith(('.mp4', '.webm', '.mkv')):
                file_path = os.path.join(download_folder, file)
                if time.time() - os.path.getmtime(file_path) < 300:  # 5 minutes
                    recent_files.append((file_path, os.path.getmtime(file_path)))
        
        if recent_files:
            # Return the most recent file
            return max(recent_files, key=lambda x: x[1])[0]
        
        return None
        
    except Exception as e:
        logger.error(f"Error finding downloaded file: {str(e)}")
        return None

def progress_hook(d):
    """Progress hook for downloads"""
    try:
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'Unknown')
            speed = d.get('_speed_str', 'Unknown')
            logger.info(f"Download progress: {percent} at {speed}")
        elif d['status'] == 'finished':
            logger.info("Download finished successfully")
        elif d['status'] == 'error':
            logger.error(f"Download error: {d.get('error', 'Unknown')}")
    except Exception as e:
        logger.error(f"Progress hook error: {str(e)}")

def format_duration(seconds):
    """Format duration in seconds to readable format"""
    if not seconds:
        return 'Unknown'
    
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

# Alternative method without cookies (for public reels)
def download_public_reel(url, download_folder):
    """Download public reels without cookies"""
    try:
        import yt_dlp
        
        filename = f"public_{uuid.uuid4().hex}.mp4"
        filepath = os.path.join(download_folder, filename)
        
        ydl_opts = {
            'outtmpl': filepath,
            'format': 'best[height<=720]',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return {"success": True, "filename": filename}
        else:
            return {"success": False, "error": "Public download failed"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}
