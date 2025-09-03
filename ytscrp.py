from fastapi import FastAPI, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import json
import uuid
from typing import List, Optional, Dict
import asyncio
import os
import threading
import time
from datetime import datetime, timedelta
import zipfile
import shutil
from concurrent.futures import ThreadPoolExecutor
import yt_dlp
from dataclasses import dataclass, asdict
import re
import hashlib
import glob
# Use direct connection (most reliable for YouTube)
print("✅ Using direct connection - most reliable and fastest option")

app = FastAPI()

# Direct connection initialization (most reliable)
print("✅ Direct connection initialized - optimal for YouTube scraping")
# Proxy initialization would go here if needed in future

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for filesystem compatibility"""
    # Remove or replace problematic characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename.strip()

def generate_video_id_hash(url: str) -> str:
    """Generate a consistent hash for video identification"""
    # Extract video ID from URL for consistent hashing
    video_id = None
    if "youtube.com/watch?v=" in url:
        video_id = url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
    elif "/video/" in url:
        video_id = url.split("/video/")[1].split("/")[0]
    
    if video_id:
        return hashlib.md5(video_id.encode()).hexdigest()[:12]
    else:
        # Fallback to URL hash
        return hashlib.md5(url.encode()).hexdigest()[:12]

def check_existing_file(download_dir: str, title: str, video_id_hash: str, audio_only: bool = False) -> Optional[str]:
    """
    Check if a file already exists in the download directory.
    Returns the existing filename if found, None otherwise.
    """
    if not os.path.exists(download_dir):
        return None
    
    sanitized_title = sanitize_filename(title)
    possible_extensions = ['.mp4', '.webm', '.mkv', '.avi', '.mov'] if not audio_only else ['.mp3', '.m4a', '.webm', '.ogg']
    
    # Check for exact matches with video ID hash
    for ext in possible_extensions:
        patterns = [
            f"{sanitized_title}_{video_id_hash}{ext}",
            f"{sanitized_title}_{video_id_hash}.f*{ext}",  # yt-dlp format codes
            f"*{video_id_hash}*{ext}",  # any file with video ID hash
        ]
        
        for pattern in patterns:
            matches = glob.glob(os.path.join(download_dir, pattern))
            if matches:
                return os.path.basename(matches[0])
    
    # Fallback: check by title similarity (70% match)
    existing_files = [f for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))]
    for existing_file in existing_files:
        # Remove extension for comparison
        existing_name = os.path.splitext(existing_file)[0]
        existing_ext = os.path.splitext(existing_file)[1]
        
        # Check if extension matches what we're looking for
        if existing_ext not in possible_extensions:
            continue
            
        # Simple similarity check
        title_words = set(sanitized_title.lower().split())
        existing_words = set(existing_name.lower().split())
        
        if len(title_words) > 0:
            similarity = len(title_words.intersection(existing_words)) / len(title_words.union(existing_words))
            if similarity > 0.7:  # 70% similarity threshold
                return existing_file
    
    return None

def get_shared_download_dir(audio_only: bool = False) -> str:
    """Get the shared download directory based on content type"""
    base_dir = "downloads"
    if audio_only:
        shared_dir = os.path.join(base_dir, "audio")
    else:
        shared_dir = os.path.join(base_dir, "videos")
    
    os.makedirs(shared_dir, exist_ok=True)
    return shared_dir

def create_task_zip_file(task_id: str, shared_download_dir: str, zip_path: str):
    """Create a zip file containing only the files downloaded in this specific task"""
    with storage_lock:
        videos = video_downloads.get(task_id, [])
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for video in videos:
            if video.status in ['completed', 'skipped'] and video.filename:
                file_path = os.path.join(shared_download_dir, video.filename)
                if os.path.exists(file_path):
                    # Add file to zip with just the filename (no folder structure)
                    zipf.write(file_path, video.filename)

# Global event loop reference (set on startup)
MAIN_LOOP: Optional[asyncio.AbstractEventLoop] = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.lock = threading.Lock()
    
    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        with self.lock:
            self.active_connections[task_id] = websocket
    
    def disconnect(self, task_id: str):
        with self.lock:
            if task_id in self.active_connections:
                del self.active_connections[task_id]
    
    async def send_update(self, task_id: str, data: dict):
        ws = None
        with self.lock:
            ws = self.active_connections.get(task_id)
        if ws:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                # Connection closed or error — cleanup
                self.disconnect(task_id)

manager = ConnectionManager()

# Helpers for human readable formatting
def format_bytes(num_bytes: Optional[float]) -> str:
    if not num_bytes:
        return "0 B/s"
    b = float(num_bytes)
    for unit in ['B','KB','MB','GB','TB']:
        if abs(b) < 1024.0:
            return f"{b:3.1f} {unit}/s"
        b /= 1024.0
    return f"{b:.1f} PB/s"

def format_eta(seconds: Optional[float]) -> str:
    if seconds is None:
        return "Unknown"
    try:
        sec = int(seconds)
    except Exception:
        return "Unknown"
    return str(timedelta(seconds=sec))

# Enhanced data structures
@dataclass
class VideoDownload:
    url: str
    title: str = "Unknown"
    status: str = "pending"  # pending, checking, skipped, downloading, completed, failed
    progress: float = 0.0
    speed: str = "0 B/s"
    eta: str = "Unknown"
    file_size: int = 0
    downloaded_size: int = 0
    filename: str = ""
    error: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    video_id_hash: str = ""
    skipped_reason: str = ""

# In-memory storage
tasks_storage: Dict[str, dict] = {}
video_downloads: Dict[str, List[VideoDownload]] = {}
download_executor = ThreadPoolExecutor(max_workers=4)
storage_lock = threading.Lock()  # protects tasks_storage and video_downloads for thread-safety

class DownloadRequest(BaseModel):
    channel_url: str
    quality: Optional[str] = "best"
    audio_only: Optional[bool] = False
    max_videos: Optional[int] = 10
    skip_duplicates: Optional[bool] = True  # New option to control duplicate checking
    convert_to_mp3: Optional[bool] = False  # If True, converts audio to MP3 (slower but consistent format)

def convert_channel_to_playlist(channel_url: str) -> str:
    """Convert channel URL to uploads playlist/page URL - keep as-is otherwise."""
    if "/playlist?" in channel_url or "/watch" in channel_url:
        return channel_url
    if "/@" in channel_url:
        channel_id = channel_url.split("/@")[-1].split("/")[0]
        return f"https://www.youtube.com/@{channel_id}/videos"
    if "/channel/" in channel_url:
        channel_id = channel_url.split("/channel/")[-1].split("/")[0]
        return f"https://www.youtube.com/channel/{channel_id}/videos"
    return channel_url

@app.on_event("startup")
async def startup_event():
    global MAIN_LOOP
    MAIN_LOOP = asyncio.get_running_loop()
    # ensure downloads dir exists
    os.makedirs("downloads", exist_ok=True)

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await manager.connect(websocket, task_id)
    try:
        # Send current status immediately
        if task_id in tasks_storage:
            await manager.send_update(task_id, {"type": "status_update", "data": tasks_storage[task_id]})
        while True:
            # Sleep briefly to keep connection alive; most updates are pushed from worker
            await asyncio.sleep(5)
            # Optionally send a heartbeat/status if available
            if task_id in tasks_storage:
                await manager.send_update(task_id, {"type": "status_update", "data": tasks_storage[task_id]})
    except WebSocketDisconnect:
        manager.disconnect(task_id)

@app.post("/api/download")
async def start_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Start a bulk download task"""
    task_id = str(uuid.uuid4())
    optimized_url = convert_channel_to_playlist(request.channel_url)
    
    # Initialize video downloads list and task status
    with storage_lock:
        video_downloads[task_id] = []
        task_status = {
            "status": "initializing",
            "progress": 0,
            "total_videos": request.max_videos,
            "current_video": "Fetching video list...",
            "channel_url": optimized_url,
            "created_at": datetime.now().isoformat(),
            "error_message": None,
            "downloaded_files": [],
            "zip_available": False,
            "completed": False,
            "active_downloads": 0,
            "download_speed": "0 B/s",
            "eta": "Calculating...",
            "success_count": 0,
            "failure_count": 0,
            "updated_at": datetime.now().isoformat()
        }
        tasks_storage[task_id] = task_status

    # Run background worker
    background_tasks.add_task(process_download_enhanced, task_id, request, optimized_url)
    
    return {"task_id": task_id, "message": "Download started"}

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    """Get current status of a download task"""
    with storage_lock:
        if task_id not in tasks_storage:
            raise HTTPException(status_code=404, detail="Task not found")
        status = tasks_storage[task_id].copy()
        if task_id in video_downloads:
            status["video_downloads"] = [asdict(v) for v in video_downloads[task_id]]
    return status

@app.get("/api/tasks")
async def list_tasks():
    """List all recent tasks"""
    with storage_lock:
        tasks = []
        for task_id, task_data in tasks_storage.items():
            tasks.append({"task_id": task_id, **task_data})
    return tasks

@app.get("/api/download/{task_id}")
async def list_downloads(task_id: str):
    """List downloaded files for a task"""
    download_dir = f"downloads/{task_id}"
    if not os.path.exists(download_dir):
        raise HTTPException(status_code=404, detail="Download directory not found")
    
    files = []
    for filename in os.listdir(download_dir):
        if os.path.isfile(os.path.join(download_dir, filename)) and not filename.endswith('.zip'):
            file_path = os.path.join(download_dir, filename)
            file_size = os.path.getsize(file_path)
            files.append({
                "filename": filename,
                "size": file_size,
                "download_url": f"/api/file/{task_id}/{filename}"
            })
    
    return {"files": files}

@app.get("/api/file/{task_id}/{filename}")
async def download_file(task_id: str, filename: str):
    """Serve downloaded video files"""
    # Get the shared download directory for this task
    with storage_lock:
        if task_id in tasks_storage:
            download_dir = tasks_storage[task_id].get('download_dir')
        else:
            # Fallback: try to determine from filename extension
            if filename.lower().endswith(('.mp3', '.m4a', '.ogg', '.webm')):
                download_dir = get_shared_download_dir(audio_only=True)
            else:
                download_dir = get_shared_download_dir(audio_only=False)
    
    file_path = os.path.join(download_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path, 
        media_type='application/octet-stream', 
        filename=filename
    )

@app.get("/api/zip/{task_id}")
async def download_zip(task_id: str):
    """Download all files as a zip archive"""
    zip_path = f"downloads/tasks/{task_id}.zip"
    
    if not os.path.exists(zip_path):
        # Try to recreate the zip if task data is available
        with storage_lock:
            if task_id in tasks_storage and task_id in video_downloads:
                download_dir = tasks_storage[task_id].get('download_dir')
                if download_dir:
                    create_task_zip_file(task_id, download_dir, zip_path)
        
        if not os.path.exists(zip_path):
            raise HTTPException(status_code=404, detail="Zip file not found")
    
    return FileResponse(
        path=zip_path,
        filename=f"{task_id}.zip",
        media_type='application/zip'
    )

@app.post("/api/download_enhanced")
async def start_download_enhanced(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Enhanced download endpoint with real-time updates"""
    task_id = str(uuid.uuid4())
    optimized_url = convert_channel_to_playlist(request.channel_url)
    
    # Initialize video downloads list and task status
    with storage_lock:
        video_downloads[task_id] = []
        task_status = {
            "status": "initializing",
            "progress": 0,
            "total_videos": request.max_videos,
            "current_video": "Starting...",
            "channel_url": optimized_url,
            "created_at": datetime.now().isoformat(),
            "error_message": None,
            "downloaded_files": [],
            "zip_available": False,
            "completed": False
        }
        tasks_storage[task_id] = task_status
    
    # Start the background task
    background_tasks.add_task(process_download_enhanced, task_id, request, optimized_url)
    
    return {"task_id": task_id, "message": "Enhanced download started"}

@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    """Get progress log for a task"""
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Generate progress text from task status and video downloads
    with storage_lock:
        task_data = tasks_storage[task_id].copy()
        videos = video_downloads.get(task_id, []).copy()
    
    progress_lines = []
    progress_lines.append(f"Task ID: {task_id}")
    progress_lines.append(f"Status: {task_data['status']}")
    progress_lines.append(f"Progress: {task_data['progress']}/{task_data['total_videos']}")
    progress_lines.append(f"Current: {task_data['current_video']}")
    progress_lines.append("")
    
    # Add individual video progress
    for i, video in enumerate(videos, 1):
        status_emoji = {"pending": "⏳", "downloading": "⬇️", "completed": "✅", "failed": "❌"}.get(video.status, "❓")
        progress_lines.append(f"{i:2d}. {status_emoji} {video.title[:60]}")
        if video.status == "downloading" and video.progress > 0:
            progress_lines.append(f"     📊 {video.progress:.1f}% | {video.speed} | ETA: {video.eta}")
        elif video.status == "failed" and video.error:
            progress_lines.append(f"     ❌ Error: {video.error}")
    
    if task_data['status'] == 'completed':
        progress_lines.append("")
        progress_lines.append("🎉 All downloads finished! You can download the ZIP file now.")
    elif task_data['status'] == 'failed':
        progress_lines.append("")
        progress_lines.append(f"❌ Task failed: {task_data.get('error_message', 'Unknown error')}")
    
    return {"progress": "\n".join(progress_lines)}

@app.get("/api/proxy/stats")
async def get_proxy_stats():
    """Get SOCKS5 proxy statistics from Geonode"""
    if socks5_proxy_fetcher:
        stats = socks5_proxy_fetcher.get_stats()
        return {
            "proxy_source": "Geonode SOCKS5 API",
            "proxy_enabled": True,
            "stats": stats
        }
    return {"proxy_enabled": False}

@app.post("/api/proxy/test")
async def test_current_proxy():
    """Test the current SOCKS5 proxy from Geonode"""
    if not socks5_proxy_fetcher:
        return {"success": False, "message": "SOCKS5 proxy fetcher not initialized"}
    
    current_proxy = socks5_proxy_fetcher.get_next_proxy()
    if not current_proxy:
        return {"success": False, "message": "No SOCKS5 proxies available"}
    
    return {
        "success": True,
        "proxy": current_proxy,
        "proxy_type": "SOCKS5",
        "source": "Geonode API",
        "message": f"SOCKS5 proxy ready: {current_proxy}"
    }

@app.post("/api/proxy/test_youtube")
async def test_youtube_proxies():
    """Test current SOCKS5 proxies specifically with YouTube/yt-dlp"""
    if not socks5_proxy_fetcher:
        return {"success": False, "message": "SOCKS5 proxy fetcher not initialized"}
    
    # Test a few SOCKS5 proxies quickly
    test_proxies = []
    for _ in range(5):
        proxy = socks5_proxy_fetcher.get_next_proxy()
        if proxy:
            test_proxies.append(proxy)
    
    if not test_proxies:
        return {"success": False, "message": "No SOCKS5 proxies available to test"}
    
    # Quick yt-dlp test with SOCKS5
    working_proxies = []
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    for proxy in test_proxies:
        try:
            ydl_opts = {
                'proxy': f'socks5://{proxy}',
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'socket_timeout': 15,
                'retries': 1
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(test_url, download=False)
                if info and info.get('title'):
                    working_proxies.append({
                        'proxy': proxy,
                        'proxy_type': 'SOCKS5',
                        'title': info.get('title', 'Unknown'),
                        'status': 'working'
                    })
                    break  # Found one working proxy
                    
        except Exception as e:
            socks5_proxy_fetcher.mark_proxy_failed(proxy)
            continue
    
    return {
        "success": True,
        "proxy_type": "SOCKS5",
        "tested_proxies": len(test_proxies),
        "working_proxies": len(working_proxies),
        "results": working_proxies,
        "message": f"Found {len(working_proxies)} working SOCKS5 proxies out of {len(test_proxies)} tested"
    }

@app.post("/api/proxy/refresh")
async def refresh_proxies():
    """Force refresh SOCKS5 proxies from Geonode API"""
    # Direct connection doesn't need proxy refreshing
    return {
        "success": True, 
        "message": "Direct connection active - no proxy refresh needed",
        "stats": {"connection_type": "direct", "status": "optimal"}
    }

@app.post("/api/proxy/disable")
async def disable_proxies():
    """Temporarily disable proxy usage"""
    global socks5_proxy_fetcher
    if socks5_proxy_fetcher:
        # Direct connection (most reliable option) 
        print("✅ Using direct connection - fastest and most reliable")
        # force_refresh_socks5_proxies()
        return {"success": True, "message": "Using direct connection - no proxy refresh needed"}
    return {"success": False, "message": "SOCKS5 proxy fetcher not initialized"}

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

async def process_download_enhanced(task_id: str, request: DownloadRequest, optimized_url: str):
    """Enhanced background worker with real-time updates"""
    try:
        await update_task_status_realtime(task_id, "fetching", 0, request.max_videos, "Fetching video information...")
        
        # Use shared download directory instead of task-specific one
        download_dir = get_shared_download_dir(request.audio_only)
        
        # Create task-specific folder for zip file organization
        task_dir = f"downloads/tasks"
        os.makedirs(task_dir, exist_ok=True)
        
        # Get video information (titles, URLs, etc.)
        video_info_list = await get_video_info_detailed(optimized_url, request.max_videos)
        
        if not video_info_list:
            await update_task_status_realtime(task_id, "failed", 0, request.max_videos, "No videos found", completed=True)
            return
        
        # Initialize video download objects
        with storage_lock:
            video_downloads[task_id] = [
                VideoDownload(
                    url=info['url'],
                    title=(info.get('title') or 'Unknown Video')[:120],
                    status='pending',
                    video_id_hash=info.get('video_id_hash', '')
                ) for info in video_info_list
            ]
            tasks_storage[task_id]['total_videos'] = len(video_info_list)
            tasks_storage[task_id]['download_dir'] = download_dir  # Store the shared dir
        
        total_videos = len(video_info_list)
        duplicate_check_msg = " (checking for duplicates)" if request.skip_duplicates else ""
        await update_task_status_realtime(task_id, "downloading", 0, total_videos, 
                                        f"Starting download of {total_videos} {'audio' if request.audio_only else 'video'} files{duplicate_check_msg}...")
        
        # Start parallel downloads (run blocking downloads in threadpool)
        await download_videos_realtime(task_id, video_info_list, download_dir, request)
        
        # Create zip file with downloaded files for this specific task
        zip_path = f"downloads/tasks/{task_id}.zip"
        create_task_zip_file(task_id, download_dir, zip_path)
        
        with storage_lock:
            success_count = sum(1 for v in video_downloads[task_id] if v.status in ['completed', 'skipped'])
            failure_count = sum(1 for v in video_downloads[task_id] if v.status == 'failed')
            skipped_count = sum(1 for v in video_downloads[task_id] if v.status == 'skipped')
        
        status_msg = f"Download completed! {success_count} successful"
        if skipped_count > 0:
            status_msg += f", {skipped_count} skipped (duplicates)"
        if failure_count > 0:
            status_msg += f", {failure_count} failed"
            
        await update_task_status_realtime(task_id, "completed", success_count, total_videos, 
                                        status_msg, zip_available=True, completed=True)
        
    except Exception as e:
        await update_task_status_realtime(task_id, "failed", 0, request.max_videos, f"Error: {str(e)}", completed=True)

async def get_video_info_detailed(channel_url: str, max_videos: int) -> List[dict]:
    """Get detailed video information including titles. Uses yt_dlp to extract list."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,  # faster for playlist listing
        'playlistend': max_videos,
    }
    
    # ✅ Direct connection (most reliable for YouTube)  
    proxy_config = {}
    print("✅ Using direct connection for info extraction - optimal performance")
    # Enhanced proxy configuration would go here if needed in future
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            entries = []
            if not info:
                return []
            if 'entries' in info and info['entries']:
                # entries are flat dicts with "url" or "id"/"webpage_url"
                for entry in info['entries']:
                    if not entry:
                        continue
                    # Some entries may be dicts with 'url' or 'webpage_url'
                    url = entry.get('url') or entry.get('webpage_url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                    title = entry.get('title') or entry.get('fulltitle') or url
                    video_id_hash = generate_video_id_hash(url)
                    entries.append({
                        'url': url, 
                        'title': title,
                        'video_id_hash': video_id_hash
                    })
            else:
                # Single video case
                url = info.get('webpage_url') or info.get('url') or f"https://www.youtube.com/watch?v={info.get('id')}"
                title = info.get('title') or url
                video_id_hash = generate_video_id_hash(url)
                if url:
                    entries.append({
                        'url': url, 
                        'title': title,
                        'video_id_hash': video_id_hash
                    })
            return entries[:max_videos]
    except Exception as e:
        print(f"Error fetching video info: {e}")
        return []

async def download_videos_realtime(task_id: str, video_info_list: List[dict], 
                                 download_dir: str, request: DownloadRequest):
    """Download videos with realtime progress updates. Worker functions run in threads."""
    if MAIN_LOOP is None:
        raise RuntimeError("MAIN_LOOP is not set. Ensure FastAPI startup event ran.")

    thread_lock = threading.Lock()  # local lock for this download run

    # Configure yt-dlp options for optimized audio-only downloads
    ydl_base_opts = {
        'ignoreerrors': True,
        'no_warnings': True,
        'concurrent_fragment_downloads': 4,
        'fragment_retries': 3,
        'retries': 2,
        'no_overwrites': True,
        'continuedl': True,
        'restrictfilenames': True,
    }

    # ✅ Direct connection (most reliable for YouTube downloads)
    proxy_config = {}
    print("✅ Using direct connection for downloads - optimal performance and reliability")
    # Enhanced proxy configuration would go here if needed in future

    if request.audio_only:
        # ULTRA-optimized for audio-only: download audio stream directly without any processing
        ydl_base_opts.update({
            'format': (
                'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio[ext=webm]/bestaudio[ext=ogg]/'
                'bestaudio[acodec=mp3]/bestaudio[acodec=aac]/bestaudio/best[height<=360]'
            ),
            'outtmpl': f'{download_dir}/%(title)s_%(id)s.%(ext)s',
            'writesubtitles': False,
            'writeautomaticsub': False,
            'writethumbnail': False,
            'writeinfojson': False,
            'writedescription': False,
            'extract_flat': False,
        })
        
        # Only add conversion if explicitly requested (slower but consistent format)
        if request.convert_to_mp3:
            ydl_base_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
    else:
        # Video downloads
        ydl_base_opts.update({
            'format': request.quality or 'best[height<=1080]',
            'outtmpl': f'{download_dir}/%(title)s_%(id)s.%(ext)s',
        })

    # progress hook that will be called by yt_dlp inside worker thread
    def progress_hook(d):
        try:
            status = d.get('status')
            # Determine index of downloading video (find the first with status 'downloading' or matching filepath)
            with storage_lock:
                videos = video_downloads.get(task_id, [])
            idx = None
            # Try to find by filename if present
            filename = d.get('filename') or d.get('tmpfilename') or d.get('filepath')
            if filename:
                base = os.path.basename(filename)
                for i, v in enumerate(videos):
                    # note: videos titles were restricted in outtmpl; we can match by startswith title or by presence of base in filename
                    if v.filename and base == v.filename:
                        idx = i
                        break
                    # fallback: compare sanitized title or video ID hash
                    if v.video_id_hash and v.video_id_hash in base:
                        idx = i
                        break
            # fallback: pick first 'downloading'
            if idx is None:
                for i, v in enumerate(videos):
                    if v.status == 'downloading':
                        idx = i
                        break
            if idx is None:
                return  # cannot attribute progress

            # Update fields
            with storage_lock:
                v = video_downloads[task_id][idx]
                if status == 'downloading':
                    downloaded = d.get('downloaded_bytes') or d.get('downloaded_bytes_estimate') or 0
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    v.downloaded_size = int(downloaded) if downloaded else v.downloaded_size
                    v.file_size = int(total) if total else v.file_size
                    if v.file_size:
                        try:
                            v.progress = (v.downloaded_size / v.file_size) * 100
                        except Exception:
                            v.progress = 0.0
                    else:
                        v.progress = 0.0
                    v.speed = format_bytes(d.get('speed'))
                    v.eta = format_eta(d.get('eta'))
                elif status == 'finished':
                    # finished downloading fragments — yt-dlp will soon postprocess/rename
                    v.progress = 100.0
                    v.speed = '0 B/s'
                    v.eta = '0:00:00'
            # Schedule async update safely on MAIN_LOOP
            asyncio.run_coroutine_threadsafe(send_video_progress_update(task_id), MAIN_LOOP)
        except Exception as e:
            # don't crash the hook
            print("progress_hook error:", e)

    def download_single_video(video_info: dict, index: int):
        """Blocking function executed in thread pool to download a single video."""
        try:
            title = video_info.get('title', 'Unknown Video')
            url = video_info['url']
            video_id_hash = video_info.get('video_id_hash', generate_video_id_hash(url))
            
            # Mark as checking for duplicates
            with storage_lock:
                vd = video_downloads[task_id][index]
                vd.status = 'checking'
                vd.video_id_hash = video_id_hash
            asyncio.run_coroutine_threadsafe(send_video_progress_update(task_id), MAIN_LOOP)

            # Check for existing files if skip_duplicates is enabled
            if request.skip_duplicates:
                existing_file = check_existing_file(download_dir, title, video_id_hash, request.audio_only)
                if existing_file:
                    with storage_lock:
                        vd = video_downloads[task_id][index]
                        vd.status = 'skipped'
                        vd.filename = existing_file
                        vd.file_size = os.path.getsize(os.path.join(download_dir, existing_file))
                        vd.progress = 100.0
                        vd.skipped_reason = f"Already exists: {existing_file}"
                        vd.end_time = datetime.now()
                        # update task counters
                        completed = sum(1 for v in video_downloads[task_id] if v.status in ['completed', 'skipped'])
                        tasks_storage[task_id]['progress'] = completed
                        tasks_storage[task_id]['success_count'] = completed
                    asyncio.run_coroutine_threadsafe(send_video_progress_update(task_id), MAIN_LOOP)
                    return True

            # Mark downloading
            with storage_lock:
                vd = video_downloads[task_id][index]
                vd.status = 'downloading'
                vd.start_time = datetime.now()
                # reset per-run fields
                vd.progress = 0.0
                vd.speed = '0 B/s'
                vd.eta = 'Unknown'
                vd.error = ''
                vd.filename = ''
            # push update
            asyncio.run_coroutine_threadsafe(send_video_progress_update(task_id), MAIN_LOOP)

            # copy base opts so each call can have its own hooks
            ydl_opts = dict(ydl_base_opts)
            ydl_opts['progress_hooks'] = [progress_hook]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # After download, try to infer downloaded filepath(s)
                downloaded_filename = None
                # yt-dlp can return a dict with 'requested_downloads'
                if info and isinstance(info, dict):
                    # If postprocessing changed the filename, 'requested_downloads' might contain filepaths
                    rds = info.get('requested_downloads')
                    if rds:
                        for dwn in rds:
                            fp = dwn.get('filepath') or dwn.get('filename')
                            if fp and os.path.exists(fp):
                                downloaded_filename = os.path.basename(fp)
                                break
                    # Another fallback: 'files' key or 'filename'
                    if not downloaded_filename:
                        candidate = info.get('filename') or info.get('requested_formats', [{}])[0].get('filepath')
                        if candidate and os.path.exists(candidate):
                            downloaded_filename = os.path.basename(candidate)

                # If not found, attempt to guess by looking in download_dir for recent files with video ID
                if not downloaded_filename:
                    # Look for files containing the video ID hash
                    pattern = f"*{video_id_hash}*"
                    matches = glob.glob(os.path.join(download_dir, pattern))
                    if matches:
                        # Get most recently created file
                        matches.sort(key=lambda x: os.path.getctime(x), reverse=True)
                        downloaded_filename = os.path.basename(matches[0])

                with storage_lock:
                    if downloaded_filename:
                        vd = video_downloads[task_id][index]
                        vd.status = 'completed'
                        vd.filename = downloaded_filename
                        file_path = os.path.join(download_dir, downloaded_filename)
                        if os.path.exists(file_path):
                            vd.file_size = os.path.getsize(file_path)
                        vd.progress = 100.0
                        vd.end_time = datetime.now()
                        # update task counters
                        completed = sum(1 for v in video_downloads[task_id] if v.status in ['completed', 'skipped'])
                        tasks_storage[task_id]['progress'] = completed
                        tasks_storage[task_id]['success_count'] = completed
                    else:
                        vd = video_downloads[task_id][index]
                        vd.status = 'failed'
                        vd.error = 'Downloaded but file not found'
                        vd.end_time = datetime.now()
                        failed = sum(1 for v in video_downloads[task_id] if v.status == 'failed')
                        tasks_storage[task_id]['failure_count'] = failed

            # final update for this video
            asyncio.run_coroutine_threadsafe(send_video_progress_update(task_id), MAIN_LOOP)
            return True
        except Exception as e:
            with storage_lock:
                video_downloads[task_id][index].status = 'failed'
                video_downloads[task_id][index].error = str(e)
                video_downloads[task_id][index].end_time = datetime.now()
                failed = sum(1 for v in video_downloads[task_id] if v.status == 'failed')
                tasks_storage[task_id]['failure_count'] = failed
            asyncio.run_coroutine_threadsafe(send_video_progress_update(task_id), MAIN_LOOP)
            return False

    # Submit download tasks to threadpool
    futures = []
    for i, video_info in enumerate(video_info_list):
        futures.append(download_executor.submit(download_single_video, video_info, i))

    # Wait for all to finish (this excludes internal progress coroutine scheduling, which runs on MAIN_LOOP)
    for future in futures:
        try:
            future.result()
        except Exception as e:
            # already handled per-video
            print("download thread error:", e)

async def send_video_progress_update(task_id: str):
    """Send real-time progress update via WebSocket (safe to call from MAIN_LOOP)."""
    with storage_lock:
        if task_id not in tasks_storage or task_id not in video_downloads:
            return
        videos = video_downloads[task_id]
        completed = sum(1 for v in videos if v.status in ['completed', 'skipped'])
        failed = sum(1 for v in videos if v.status == 'failed')
        downloading = sum(1 for v in videos if v.status == 'downloading')
        checking = sum(1 for v in videos if v.status == 'checking')
        skipped = sum(1 for v in videos if v.status == 'skipped')
        # choose an active speed (first non-zero)
        active_speed = next((v.speed for v in videos if v.status == 'downloading' and v.speed != '0 B/s'), '0 B/s')
        tasks_storage[task_id].update({
            'progress': completed,
            'success_count': completed,
            'failure_count': failed,
            'downloading_count': downloading,
            'checking_count': checking,
            'skipped_count': skipped,
            'download_speed': active_speed,
            'active_downloads': downloading,
            'current_video': f"{downloading} downloading, {completed} completed, {failed} failed",
            'updated_at': datetime.now().isoformat()
        })
        payload = {
            'type': 'progress_update',
            'task_status': tasks_storage[task_id],
            'video_downloads': [asdict(v) for v in videos]
        }
    await manager.send_update(task_id, payload)

async def update_task_status_realtime(task_id: str, status: str, progress: int, total: int, 
                                    current: str, zip_available: bool = False, completed: bool = False):
    """Update task status with real-time WebSocket notification"""
    with storage_lock:
        if task_id in tasks_storage:
            tasks_storage[task_id].update({
                "status": status,
                "progress": progress,
                "total_videos": total,
                "current_video": current,
                "zip_available": zip_available,
                "completed": completed,
                "updated_at": datetime.now().isoformat()
            })
            payload = {'type': 'status_update', 'data': tasks_storage[task_id]}
        else:
            return
    await manager.send_update(task_id, payload)

def create_zip_file(source_dir: str, zip_path: str):
    """Create a zip file from downloaded files"""
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    if not file.endswith('.zip'):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arcname)
    except Exception as e:
        print(f"Error creating zip file: {e}")

@app.get("/")
async def root():
    """Serve the static HTML file"""
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    os.makedirs("downloads", exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
