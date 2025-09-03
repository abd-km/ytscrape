import yt_dlp
import random
import time
import os

def get_browser_profile(browser_type=None):
    """Get minimal consistent browser headers that make sense together"""
    profiles = {
        'chrome_mac': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        'firefox_windows': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        },
        'safari_mac': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        },
        'chrome_windows': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }
    
    # If no specific browser requested, randomly choose a logical one
    if browser_type is None:
        browser_type = random.choice(list(profiles.keys()))
    
    return profiles.get(browser_type, profiles['chrome_mac'])

def download_youtube_video(url, output_path="./downloads"):
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    # Get a logical browser profile with consistent headers
    browser_headers = get_browser_profile()
    browser_name = [k for k, v in {
        'Chrome Mac': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Firefox Windows': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0)',
        'Safari Mac': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15',
        'Chrome Windows': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }.items() if v in browser_headers['User-Agent']][0]
    
    print(f"Using browser profile: {browser_name}")
    
    # Configure yt-dlp options with logical headers
    ydl_opts = {
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'format': 'best[height<=720]',  # Get best quality up to 720p
        'ignoreerrors': True,
        'no_warnings': True,  # Clean output
        'http_headers': browser_headers,  # Logical User-Agent rotation
        'sleep_interval': 1,
        'max_sleep_interval': 3,
        'fragment_retries': 3,
        'retries': 2,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video info first
            info = ydl.extract_info(url, download=False)
            if info:
                title = info.get('title', 'Unknown')
                print(f"Downloading: {title}")
                
                # Download the video
                ydl.download([url])
                print(f"✅ Downloaded '{title}' to {output_path}")
            else:
                print(f"❌ Could not extract info for {url}")
            
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")

if __name__ == "__main__":
    video_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=3JZ_D3ELwOQ"
    ]
    
    for url in video_urls:
        download_youtube_video(url)
        time.sleep(random.uniform(1, 3))  # polite delay
