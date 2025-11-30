# Reels Downloader API

A Flask-based API to download Instagram and Facebook reels.

## Deployment on Render

1. Fork/Create this repository
2. Connect your GitHub to Render
3. Create new Web Service
4. Connect your repository
5. Use these settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

## API Endpoints

### GET /
Returns API information and usage.

### POST /download
Download a reel from URL.

**Request:**
```json
{
    "url": "https://www.instagram.com/reel/EXAMPLE/"
}
