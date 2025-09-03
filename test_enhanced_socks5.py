#!/usr/bin/env python3
"""
🧪 Test Enhanced SOCKS5 Proxy Configuration
Verify that the improved yt-dlp settings work with YouTube
"""

import sys
import os
sys.path.append('/Users/am/ytscraper')

from socks5_proxy_fetcher import SOCKS5ProxyFetcher
import yt_dlp

def test_enhanced_socks5_config():
    """Test the enhanced SOCKS5 configuration with a real YouTube video"""
    
    print("🧪 Testing Enhanced SOCKS5 Configuration")
    print("=" * 50)
    
    # Initialize proxy fetcher
    fetcher = SOCKS5ProxyFetcher()
    stats = fetcher.get_stats()
    print(f"📊 Available proxies: {stats['total_proxies']}")
    
    # Test YouTube URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    print(f"🎬 Test URL: {test_url}")
    
    # Test with enhanced SOCKS5 proxy
    for attempt in range(3):
        proxy = fetcher.get_next_proxy()
        if not proxy:
            print("❌ No proxy available")
            continue
            
        print(f"\n🧦 Attempt {attempt + 1}: Testing proxy {proxy}")
        
        # Get enhanced proxy configuration
        proxy_config = fetcher.get_proxy_dict(proxy)
        print(f"🔧 Proxy config: {proxy_config}")
        
        # Create yt-dlp options with enhanced config
        ydl_opts = {
            **proxy_config,
            'quiet': True,
            'no_warnings': True,
            'simulate': True,  # Don't download, just test connection
            'extract_flat': False,
        }
        
        try:
            print("🔄 Testing proxy connection...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(test_url, download=False)
                if info and info.get('title'):
                    print(f"✅ SUCCESS! Proxy working: {proxy}")
                    print(f"🎵 Video title: {info.get('title', 'Unknown')}")
                    print(f"👤 Uploader: {info.get('uploader', 'Unknown')}")
                    print(f"⏱️ Duration: {info.get('duration', 'Unknown')} seconds")
                    return True
                else:
                    print(f"❌ FAILED: No video info extracted with proxy {proxy}")
                    
        except Exception as e:
            print(f"❌ FAILED: Proxy {proxy} - {str(e)}")
            fetcher.mark_proxy_failed(proxy)
            
    print("❌ All proxy attempts failed")
    return False

def compare_direct_vs_proxy():
    """Compare direct connection vs SOCKS5 proxy performance"""
    
    print("\n🔄 Comparing Direct vs SOCKS5 Performance")
    print("=" * 50)
    
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # Test 1: Direct connection
    print("1️⃣ Testing direct connection...")
    try:
        ydl_opts_direct = {
            'quiet': True,
            'no_warnings': True,
            'simulate': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts_direct) as ydl:
            info = ydl.extract_info(test_url, download=False)
            if info:
                print("✅ Direct connection: SUCCESS")
            else:
                print("❌ Direct connection: FAILED")
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
    
    # Test 2: Enhanced SOCKS5 proxy
    print("\n2️⃣ Testing enhanced SOCKS5 proxy...")
    success = test_enhanced_socks5_config()
    
    if success:
        print("\n🎉 CONCLUSION: Enhanced SOCKS5 configuration is working!")
    else:
        print("\n⚠️ CONCLUSION: SOCKS5 proxies still having issues")

if __name__ == "__main__":
    compare_direct_vs_proxy()
