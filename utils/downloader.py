import os
import uuid
import time
import random
import logging
from urllib.parse import unquote

logger = logging.getLogger(__name__)

def download_reel_smart(url, download_folder):
    """
    Smart downloader that uses multiple methods with proper configuration
    """
    try:
        logger.info(f"Starting smart download for: {url}")
        
        # Method 1: Try yt-dlp with proper configuration (Primary)
        try:
            result = download_with_ytdlp_advanced(url, download_folder)
            if result['success']:
                logger.info("Successfully downloaded with yt-dlp")
                return result
        except Exception as e:
            logger.warning(f"yt-dlp method failed: {str(e)}")
        
        # Method 2: Try alternative approach
        try:
            result = download_with_alternative(url, download_folder)
            if result['success']:
                logger.info("Successfully downloaded with alternative method")
                return result
        except Exception as e:
            logger.warning(f"Alternative method failed: {str(e)}")
        
        return {
            "success": False,
            "error": "All download methods failed. The reel might be private, geo-restricted, or unavailable."
        }
            
    except Exception as e:
        logger.error(f"Smart download failed: {str(e)}")
        return {
            "success": False,
            "error": f"Download failed: {str(e)}"
        }

def download_with_ytdlp_advanced(url, download_folder):
    """
    Advanced yt-dlp downloader with proper configuration
    """
    try:
        import yt_dlp
        
        # Generate unique filename
        filename = f"reel_{uuid.uuid4().hex}.mp4"
        filepath = os.path.join(download_folder, filename)
        
        # Advanced yt-dlp configuration
        ydl_opts = {
            'outtmpl': filepath.replace('.mp4', '') + '.%(ext)s',
            'format': 'best[height<=720]/best',
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'writeinfojson': False,
            'writethumbnail': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'consoletitle': False,
            
            # HTTP settings
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'skip_unavailable_fragments': True,
            
            # Throttling to avoid blocks
            'ratelimit': 1024000,  # 1 MB/s
            'throttledratelimit': 2048000,
            
            # Extractor options
            'extractor_args': {
                'instagram': {
                    'feed': {'endpoints': False},
                    'story': {'endpoints': False},
                    'highlights': {'endpoints': False},
                }
            },
            
            # Post-processing
            'postprocessors': [],
            
            # Cookies and headers
            'cookiefile': None,
            
            # Progress hooks
            'progress_hooks': [lambda d: _progress_hook(d, url)],
        }
        
        # Platform-specific options
        if 'instagram.com' in url:
            ydl_opts.update({
                'extractor_args': {'instagram': {'feed': {'endpoints': False}}},
            })
        elif 'facebook.com' in url or 'fb.watch' in url:
            ydl_opts.update({
                'extractor_args': {'facebook': {}},
            })
        
        logger.info(f"Downloading with yt-dlp: {url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            info = ydl.extract_info(url, download=False)
            logger.info(f"Video info: {info.get('title', 'Unknown')}")
            
            # Now download
            ydl.download([url])
            
            # Get the actual downloaded filename
            actual_filename = ydl.prepare_filename(info)
            final_filename = f"reel_{uuid.uuid4().hex}.mp4"
            final_filepath = os.path.join(download_folder, final_filename)
            
            # Rename to our format
            if os.path.exists(actual_filename):
                os.rename(actual_filename, final_filepath)
            else:
                # Try with .mp4 extension
                actual_filename_mp4 = actual_filename.replace('.webm', '.mp4').replace('.mkv', '.mp4')
                if os.path.exists(actual_filename_mp4):
                    os.rename(actual_filename_mp4, final_filepath)
                else:
                    # Find the actual downloaded file
                    for f in os.listdir(download_folder):
                        if f.startswith(os.path.basename(actual_filename).split('.')[0]):
                            os.rename(os.path.join(download_folder, f), final_filepath)
                            break
                    else:
                        return {
                            "success": False,
                            "error": "Downloaded file not found"
                        }
        
        # Verify download
        if os.path.exists(final_filepath) and os.path.getsize(final_filepath) > 0:
            file_size = os.path.getsize(final_filepath)
            
            return {
                "success": True,
                "filename": final_filename,
                "filepath": final_filepath,
                "file_size": file_size,
                "title": info.get('title', 'reel'),
                "duration": info.get('duration', 'Unknown'),
                "thumbnail": info.get('thumbnail', ''),
                "message": "Download completed successfully"
            }
        else:
            return {
                "success": False,
                "error": "Downloaded file is empty or missing"
            }
        
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        logger.error(f"yt-dlp DownloadError: {error_msg}")
        
        # Handle specific errors
        if 'Private' in error_msg:
            return {"success": False, "error": "This reel is private and cannot be downloaded"}
        elif 'not found' in error_msg.lower():
            return {"success": False, "error": "Reel not found or deleted"}
        elif 'age restricted' in error_msg.lower():
            return {"success": False, "error": "Age-restricted content cannot be downloaded"}
        elif 'login required' in error_msg.lower():
            return {"success": False, "error": "Login required to access this content"}
        else:
            return {"success": False, "error": f"Download failed: {error_msg}"}
            
    except Exception as e:
        logger.error(f"yt-dlp unexpected error: {str(e)}")
        return {"success": False, "error": f"Download error: {str(e)}"}

def download_with_alternative(url, download_folder):
    """
    Alternative download method as fallback
    """
    try:
        import yt_dlp
        
        filename = f"reel_alt_{uuid.uuid4().hex}.mp4"
        filepath = os.path.join(download_folder, filename)
        
        # Simpler configuration for fallback
        ydl_opts = {
            'outtmpl': filepath,
            'format': 'worst[height>=240]',  # Try lower quality
            'quiet': True,
            'no_warnings': True,
            'retries': 2,
            'fragment_retries': 2,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return {
                "success": True,
                "filename": filename,
                "filepath": filepath,
                "file_size": os.path.getsize(filepath),
                "title": info.get('title', 'reel'),
                "duration": info.get('duration', 'Unknown'),
            }
        else:
            return {"success": False, "error": "Alternative method failed"}
            
    except Exception as e:
        logger.error(f"Alternative method error: {str(e)}")
        return {"success": False, "error": str(e)}

def _progress_hook(d, url):
    """Progress hook for yt-dlp"""
    if d['status'] == 'downloading':
        logger.info(f"Downloading {url}: {d.get('_percent_str', 'Unknown')} - {d.get('_speed_str', 'Unknown')}")
    elif d['status'] == 'finished':
        logger.info(f"Finished downloading {url}")
    elif d['status'] == 'error':
        logger.error(f"Error downloading {url}: {d.get('error', 'Unknown error')}")
