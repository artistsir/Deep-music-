import os
import uuid
import time
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def download_reel_with_cookies(url, download_folder, cookies_folder):
    """
    Download reel using cookies to bypass login requirements
    """
    try:
        import yt_dlp
        
        logger.info(f"Attempting download: {url}")
        
        filename = f"reel_{uuid.uuid4().hex}.mp4"
        filepath = os.path.join(download_folder, filename)
        
        # Find available cookies files
        cookies_file = find_best_cookies(cookies_folder, url)
        
        # Advanced yt-dlp configuration with cookie support
        ydl_opts = build_ydl_options(filepath, cookies_file)
        
        if cookies_file:
            logger.info(f"Using cookies file: {cookies_file}")
        else:
            logger.info("No cookies file found, attempting without cookies")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return try_alternative_methods(url, download_folder)
                
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
                if os.path.exists(final_filepath) and os.path.getsize(final_filepath) > 1024:
                    file_size = os.path.getsize(final_filepath)
                    
                    return {
                        "success": True,
                        "filename": filename,
                        "filepath": final_filepath,
                        "file_size": file_size,
                        "title": clean_title(info.get('title', 'reel')),
                        "duration": format_duration(info.get('duration')),
                        "thumbnail": info.get('thumbnail'),
                        "quality": info.get('format_note', 'HD'),
                        "message": "Download completed successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Downloaded file is empty or too small",
                        "solution": "The content might be restricted or cookies expired"
                    }
                    
            except yt_dlp.utils.DownloadError as e:
                error_msg = str(e)
                logger.error(f"DownloadError: {error_msg}")
                
                return handle_download_error(error_msg, cookies_file)
                
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return try_alternative_methods(url, download_folder)

def build_ydl_options(filepath, cookies_file):
    """Build optimized yt-dlp options with cookie support"""
    
    # Default headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://www.instagram.com/',
        'Origin': 'https://www.instagram.com',
    }
    
    ydl_opts = {
        # Output
        'outtmpl': filepath.replace('.mp4', ''),
        
        # Format selection - SIMPLIFIED to avoid conflicts
        'format': 'best',
        
        # Cookies - ONLY use cookiefile, remove browser cookies
        'cookiefile': cookies_file,
        
        # Download settings
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'continue_dl': True,
        
        # Timeouts
        'socket_timeout': 30,
        'retry_sleep': 1,
        
        # Rate limiting
        'ratelimit': 2000000,
        
        # Headers
        'http_headers': headers,
        
        # Extractor args
        'extractor_args': {
            'instagram': {
                'format': 'best',
            },
            'facebook': {
                'format': 'best',
            }
        },
        
        # Verbosity
        'quiet': True,
        'no_warnings': False,
        
        # Progress hooks
        'progress_hooks': [lambda d: progress_hook(d)],
        
        # Post-processing - removed problematic options
        'postprocessors': [],
    }
    
    # Platform-specific optimizations
    if 'instagram.com' in url:
        ydl_opts['http_headers'].update({
            'Referer': 'https://www.instagram.com/',
            'Origin': 'https://www.instagram.com',
            'X-IG-App-ID': '936619743392459',
        })
    elif 'facebook.com' in url:
        ydl_opts['http_headers'].update({
            'Referer': 'https://www.facebook.com/',
            'Origin': 'https://www.facebook.com',
        })
    
    return ydl_opts

def try_alternative_methods(url, download_folder):
    """Try alternative download methods when main method fails"""
    logger.info("Trying alternative download methods...")
    
    # Method 1: Simple download without cookies
    result = simple_download(url, download_folder)
    if result['success']:
        return result
    
    # Method 2: Try with different format selection
    result = alternative_format_download(url, download_folder)
    if result['success']:
        return result
    
    # Method 3: Last resort - minimal configuration
    result = minimal_download(url, download_folder)
    if result['success']:
        return result
    
    return {
        "success": False,
        "error": "All download methods failed",
        "solution": "The reel might be private, geo-restricted, or unavailable. Try uploading cookies for private accounts."
    }

def simple_download(url, download_folder):
    """Simple download method with minimal configuration"""
    try:
        import yt_dlp
        
        filename = f"reel_simple_{uuid.uuid4().hex}.mp4"
        filepath = os.path.join(download_folder, filename)
        
        ydl_opts = {
            'outtmpl': filepath,
            'format': 'best[height<=720]',
            'quiet': True,
            'retries': 3,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return {
                "success": True,
                "filename": filename,
                "file_size": os.path.getsize(filepath),
                "title": clean_title(info.get('title', 'reel')),
                "duration": format_duration(info.get('duration')),
            }
        else:
            return {"success": False}
            
    except Exception as e:
        logger.error(f"Simple download failed: {str(e)}")
        return {"success": False}

def alternative_format_download(url, download_folder):
    """Try with different format selection"""
    try:
        import yt_dlp
        
        filename = f"reel_alt_{uuid.uuid4().hex}.mp4"
        filepath = os.path.join(download_folder, filename)
        
        # Try different format combinations
        format_preferences = [
            'best[ext=mp4]',
            'worst[height>=240]',
            'best[height<=480]',
            'best'
        ]
        
        for format_str in format_preferences:
            try:
                ydl_opts = {
                    'outtmpl': filepath,
                    'format': format_str,
                    'quiet': True,
                    'retries': 2,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    return {
                        "success": True,
                        "filename": filename,
                        "file_size": os.path.getsize(filepath),
                        "title": clean_title(info.get('title', 'reel')),
                        "duration": format_duration(info.get('duration')),
                    }
                    
            except Exception as e:
                continue
                
        return {"success": False}
        
    except Exception as e:
        return {"success": False}

def minimal_download(url, download_folder):
    """Minimal configuration download as last resort"""
    try:
        import yt_dlp
        
        filename = f"reel_min_{uuid.uuid4().hex}.mp4"
        filepath = os.path.join(download_folder, filename)
        
        ydl_opts = {
            'outtmpl': filepath,
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return {
                "success": True,
                "filename": filename,
                "file_size": os.path.getsize(filepath),
                "title": clean_title(info.get('title', 'reel')),
            }
        else:
            return {"success": False}
            
    except Exception as e:
        return {"success": False}

def find_best_cookies(cookies_folder, url):
    """Find the best cookies file for the given URL"""
    try:
        cookies_files = []
        
        # Look for cookies files
        for file in os.listdir(cookies_folder):
            if file.endswith('.txt'):
                cookies_files.append(os.path.join(cookies_folder, file))
        
        if not cookies_files:
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
        return max(cookies_files, key=os.path.getctime)
        
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
            "solution": "Upload valid cookies file to download private reels"
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
            "solution": "Upload fresh cookies file"
        }
    
    elif 'rate limit' in error_lower:
        return {
            "success": False,
            "error": "Rate limit exceeded",
            "solution": "Wait a few minutes and try again"
        }
    
    elif 'unsupported' in error_lower or 'keyring' in error_lower:
        return {
            "success": False,
            "error": "Configuration error",
            "solution": "Trying alternative download methods..."
        }
    
    else:
        return {
            "success": False,
            "error": f"Download failed: {error_msg}",
            "solution": "Trying alternative methods..."
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
        
        # Look for recent video files
        recent_files = []
        for file in os.listdir(download_folder):
            if file.endswith(('.mp4', '.webm', '.mkv', '.m4a')):
                file_path = os.path.join(download_folder, file)
                if time.time() - os.path.getmtime(file_path) < 300:
                    recent_files.append(file_path)
        
        if recent_files:
            return recent_files[0]
        
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
            logger.info(f"Progress: {percent} at {speed}")
        elif d['status'] == 'finished':
            logger.info("Download finished")
    except Exception:
        pass

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

def clean_title(title):
    """Clean video title from special characters"""
    if not title:
        return 'reel'
    
    # Remove special characters and limit length
    import re
    title = re.sub(r'[^\w\s-]', '', title)
    title = title.strip()[:50]
    
    return title if title else 'reel'

# Direct public download function
def download_public_reel(url, download_folder):
    """Direct public reel download without cookies"""
    try:
        import yt_dlp
        
        filename = f"public_{uuid.uuid4().hex}.mp4"
        filepath = os.path.join(download_folder, filename)
        
        ydl_opts = {
            'outtmpl': filepath,
            'format': 'best[height<=720]',
            'quiet': True,
            'retries': 5,
            'socket_timeout': 30,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return {
                "success": True,
                "filename": filename,
                "file_size": os.path.getsize(filepath),
                "title": clean_title(info.get('title', 'reel')),
                "duration": format_duration(info.get('duration')),
            }
        else:
            return {"success": False, "error": "Download failed"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}
