import os
import uuid
import time
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def download_reel(url, download_folder):
    """
    Main download function using yt-dlp with optimized settings
    """
    try:
        import yt_dlp
        
        logger.info(f"Starting download for: {url}")
        
        # Generate unique filename
        filename = f"reel_{uuid.uuid4().hex}.mp4"
        filepath = os.path.join(download_folder, filename)
        
        # OPTIMIZED yt-dlp configuration for Reels
        ydl_opts = {
            # Output template
            'outtmpl': os.path.join(download_folder, 'temp_%(id)s.%(ext)s'),
            
            # Format selection - prioritize MP4, then quality
            'format': 'best[ext=mp4]/best[height<=720]/best',
            'format_sort': ['res:720', 'ext:mp4:m4a', 'acodec:mp4a'],
            
            # Download settings
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            'continue_dl': True,
            
            # Timeout settings
            'socket_timeout': 30,
            'retry_sleep': 1,
            
            # Throttling to avoid detection
            'ratelimit': 2500000,  # 2.5 MB/s
            'throttledratelimit': 5000000,
            
            # HTTP headers
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.instagram.com/',
                'Origin': 'https://www.instagram.com',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            },
            
            # Extractor specific settings
            'extractor_args': {
                'instagram': {
                    'format': 'best',
                    'feed': {'endpoints': False},
                    'client': {'endpoints': False},
                },
                'facebook': {
                    'format': 'best',
                }
            },
            
            # Post-processing
            'postprocessors': [],
            
            # Verbosity
            'quiet': True,
            'no_warnings': False,
            'verbose': False,
            
            # Progress hooks
            'progress_hooks': [lambda d: progress_hook(d, url)],
        }
        
        # Platform-specific optimizations
        if 'instagram.com' in url:
            ydl_opts.update({
                'extractor_args': {
                    'instagram': {
                        'format': 'best[height<=720]',
                        'reel': {'endpoints': True},
                    }
                },
            })
        elif 'facebook.com' in url:
            ydl_opts.update({
                'extractor_args': {
                    'facebook': {
                        'format': 'best[height<=720]',
                    }
                },
            })
        
        logger.info(f"Downloading with optimized settings...")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # First extract info without downloading
                info_dict = ydl.extract_info(url, download=False)
                
                if not info_dict:
                    return {
                        "success": False,
                        "error": "Could not extract video information"
                    }
                
                logger.info(f"Video found: {info_dict.get('title', 'Unknown')}")
                
                # Now download
                ydl.download([url])
                
                # Find the downloaded file
                temp_filename = ydl.prepare_filename(info_dict)
                actual_filepath = find_downloaded_file(temp_filename, download_folder)
                
                if not actual_filepath:
                    return {
                        "success": False,
                        "error": "Downloaded file not found"
                    }
                
                # Rename to our final filename
                final_filepath = os.path.join(download_folder, filename)
                os.rename(actual_filepath, final_filepath)
                
                # Verify the file
                if not os.path.exists(final_filepath) or os.path.getsize(final_filepath) == 0:
                    return {
                        "success": False,
                        "error": "Downloaded file is empty"
                    }
                
                file_size = os.path.getsize(final_filepath)
                
                return {
                    "success": True,
                    "filename": filename,
                    "filepath": final_filepath,
                    "file_size": file_size,
                    "title": info_dict.get('title', 'reel'),
                    "duration": format_duration(info_dict.get('duration')),
                    "thumbnail": info_dict.get('thumbnail'),
                    "message": "Download completed successfully"
                }
                
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            logger.error(f"DownloadError: {error_msg}")
            
            # Handle specific error cases
            if 'Private' in error_msg:
                return {"success": False, "error": "This reel is private and cannot be downloaded"}
            elif 'not found' in error_msg.lower():
                return {"success": False, "error": "Reel not found or has been removed"}
            elif 'age restriction' in error_msg.lower():
                return {"success": False, "error": "Age-restricted content"}
            elif 'login required' in error_msg.lower():
                return {"success": False, "error": "Login required - this may be a private account"}
            elif 'URL could not be processed' in error_msg:
                return {"success": False, "error": "Invalid URL or reel not accessible"}
            else:
                return {"success": False, "error": f"Download failed: {error_msg}"}
                
    except ImportError:
        return {
            "success": False,
            "error": "yt-dlp not installed properly. Please check requirements."
        }
    except Exception as e:
        logger.error(f"Unexpected error in download_reel: {str(e)}")
        return {
            "success": False,
            "error": f"Download failed: {str(e)}"
        }

def find_downloaded_file(temp_path, download_folder):
    """
    Find the actual downloaded file
    """
    try:
        # If the temp file exists, return it
        if os.path.exists(temp_path):
            return temp_path
        
        # Look for files with similar names
        base_name = os.path.basename(temp_path).split('.')[0]
        for file in os.listdir(download_folder):
            if file.startswith(base_name):
                return os.path.join(download_folder, file)
        
        # Look for any recent MP4 files
        recent_files = []
        for file in os.listdir(download_folder):
            if file.endswith('.mp4') and file.startswith('temp_'):
                file_path = os.path.join(download_folder, file)
                # Check if modified in last 2 minutes
                if time.time() - os.path.getmtime(file_path) < 120:
                    recent_files.append(file_path)
        
        if recent_files:
            return recent_files[0]
        
        return None
        
    except Exception as e:
        logger.error(f"Error finding downloaded file: {str(e)}")
        return None

def progress_hook(d, url):
    """Progress hook for downloads"""
    try:
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'Unknown')
            speed = d.get('_speed_str', 'Unknown')
            logger.info(f"Downloading {url}: {percent} at {speed}")
        elif d['status'] == 'finished':
            logger.info(f"Finished downloading: {url}")
        elif d['status'] == 'error':
            logger.error(f"Error downloading {url}: {d.get('error', 'Unknown error')}")
    except Exception as e:
        logger.error(f"Progress hook error: {str(e)}")

def format_duration(seconds):
    """Format duration in seconds to readable format"""
    if not seconds:
        return 'Unknown'
    
    minutes, seconds = divmod(seconds, 60)
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"

# Alternative method for Instagram specifically
def download_instagram_specific(url, download_folder):
    """
    Specialized method for Instagram reels
    """
    try:
        import yt_dlp
        
        filename = f"ig_reel_{uuid.uuid4().hex}.mp4"
        filepath = os.path.join(download_folder, filename)
        
        ydl_opts = {
            'outtmpl': filepath,
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'instagram': {
                    'format': 'best',
                    'reel': {'endpoints': True},
                }
            },
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return {"success": True, "filename": filename}
        else:
            return {"success": False, "error": "Instagram download failed"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}
