#!/usr/bin/env python3
"""
Test script to demonstrate efficient audio-only downloads
"""

import time
import requests
import json

def test_audio_download_efficiency():
    """Test the efficiency of different audio download modes"""
    
    print("=== Audio Download Efficiency Test ===\n")
    
    base_url = "http://localhost:8000"
    
    # Test data - use a short video for quick testing
    test_request = {
        "channel_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll (short video)
        "max_videos": 1,
        "audio_only": True,
        "skip_duplicates": False
    }
    
    print("🎵 Testing Audio Download Modes:\n")
    
    # Test 1: Ultra-efficient mode (no conversion)
    print("1️⃣ ULTRA-EFFICIENT MODE (Direct audio stream, no conversion)")
    print("   - Downloads native audio format (m4a/mp3/webm)")
    print("   - No FFmpeg processing")
    print("   - Fastest possible audio download")
    
    test1_request = {**test_request, "convert_to_mp3": False}
    
    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/api/download_enhanced", json=test1_request)
        if response.status_code == 200:
            print(f"   ✅ Request sent successfully: {response.json()}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: MP3 conversion mode
    print("2️⃣ MP3 CONVERSION MODE (Audio stream + conversion)")
    print("   - Downloads audio stream")
    print("   - Converts to MP3 using FFmpeg")
    print("   - Slower but consistent MP3 format")
    
    test2_request = {**test_request, "convert_to_mp3": True}
    
    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/api/download_enhanced", json=test2_request)
        if response.status_code == 200:
            print(f"   ✅ Request sent successfully: {response.json()}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Video download for comparison
    print("3️⃣ VIDEO DOWNLOAD (For comparison)")
    print("   - Downloads full video stream")
    print("   - Much larger file size")
    print("   - Significantly slower")
    
    test3_request = {**test_request, "audio_only": False}
    
    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/api/download_enhanced", json=test3_request)
        if response.status_code == 200:
            print(f"   ✅ Request sent successfully: {response.json()}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")

def explain_audio_efficiency():
    """Explain how the audio efficiency works"""
    print("\n" + "="*60)
    print("🔧 HOW THE ULTRA-EFFICIENT AUDIO MODE WORKS")
    print("="*60 + "\n")
    
    print("📋 FORMAT SELECTION PRIORITY:")
    print("   1. bestaudio[ext=m4a]     - Native M4A audio (no conversion needed)")
    print("   2. bestaudio[ext=mp3]     - Native MP3 audio (no conversion needed)")
    print("   3. bestaudio[ext=webm]    - Native WebM audio (no conversion needed)")
    print("   4. bestaudio[ext=ogg]     - Native OGG audio (no conversion needed)")
    print("   5. bestaudio[acodec=mp3]  - MP3 audio codec (any container)")
    print("   6. bestaudio[acodec=aac]  - AAC audio codec (any container)")
    print("   7. bestaudio              - Best available audio-only stream")
    print("   8. best[height<=360]      - Fallback: low-res video if no audio-only")
    
    print("\n⚡ EFFICIENCY BENEFITS:")
    print("   ✅ No video stream download (saves 90%+ bandwidth)")
    print("   ✅ No FFmpeg conversion (saves processing time)")
    print("   ✅ Direct audio stream (3-10x faster than video)")
    print("   ✅ Native format preservation (best quality)")
    print("   ✅ Smaller file sizes (typically 3-10MB vs 50-200MB for video)")
    
    print("\n🎯 USE CASES:")
    print("   • Podcasts & music downloads")
    print("   • Large batch audio extraction")
    print("   • Limited bandwidth situations")
    print("   • Mobile device downloads")
    print("   • Audio-only content consumption")
    
    print("\n📊 EXPECTED PERFORMANCE:")
    print("   • Ultra-efficient mode: ~10-30 seconds for typical video")
    print("   • MP3 conversion mode:  ~15-45 seconds for typical video")
    print("   • Video download mode:  ~30-120 seconds for typical video")
    print("   • Bandwidth usage:      Audio ~5-15MB vs Video ~50-200MB")

if __name__ == "__main__":
    explain_audio_efficiency()
    
    print("\n" + "="*60)
    print("🧪 READY TO TEST? Make sure your server is running on localhost:8000")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8000/api/tasks")
        if response.status_code == 200:
            print("✅ Server is running! Starting efficiency test...\n")
            test_audio_download_efficiency()
        else:
            print("❌ Server is not responding correctly")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("   Please start the server with: uvicorn ytscrp:app --reload")
