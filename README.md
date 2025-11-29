# Social Media Downloader API

A complete API to download media from Instagram, Twitter, YouTube, and Facebook. Deployable on Render's free tier.

## Features

- 📷 Instagram Reels/Posts download
- 🐦 Twitter video download  
- 📺 YouTube video download (multiple qualities)
- 👥 Facebook video download
- 🎯 Simple REST API
- 🌐 Web interface
- 🚀 Easy deployment

## Deployment on Render

1. Fork this repository
2. Go to [Render.com](https://render.com)
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Use these settings:
   - **Name**: social-media-downloader
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. Click "Create Web Service"

## API Usage

### Download Media
```http
POST /api/download
Content-Type: application/json

{
    "url": "https://www.instagram.com/p/Cexample/"
}
