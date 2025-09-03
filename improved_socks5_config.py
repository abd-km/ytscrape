#!/usr/bin/env python3
"""
🧦 Improved SOCKS5 Configuration for yt-dlp
Based on yt-dlp documentation analysis
"""

def get_improved_socks5_config(proxy: str) -> dict:
    """
    Create yt-dlp configuration with proper SOCKS5 settings
    Based on yt-dlp documentation requirements
    """
    if not proxy:
        return {}
    
    # Ensure proper socks5:// scheme format
    if not proxy.startswith('socks5://'):
        proxy = f'socks5://{proxy}'
    
    config = {
        # Core proxy setting
        'proxy': proxy,
        
        # Socket timeout (important for slow proxies)
        'socket_timeout': 30,
        
        # Force IPv4 (many proxies work better with IPv4)
        'force_ipv4': True,
        
        # Add retries for proxy failures
        'retries': 3,
        'fragment_retries': 3,
        
        # Sleep between requests to avoid overwhelming proxy
        'sleep_interval': 1,
        'max_sleep_interval': 3,
        
        # More aggressive timeout settings
        'http_chunk_size': None,  # Disable chunked downloading through proxy
    }
    
    return config

def get_fallback_socks5_options() -> list:
    """
    Get fallback options if SOCKS5 proxy fails
    Based on yt-dlp workaround options
    """
    return [
        # Option 1: Direct connection
        {'proxy': ''},
        
        # Option 2: Force IPv6 instead of IPv4
        {'proxy': '', 'force_ipv6': True, 'force_ipv4': False},
        
        # Option 3: Prefer insecure connection
        {'proxy': '', 'prefer_insecure': True},
        
        # Option 4: No certificate check
        {'proxy': '', 'no_check_certificate': True},
    ]

def test_socks5_proxy_with_ytdlp(proxy: str) -> bool:
    """
    Test a SOCKS5 proxy using yt-dlp with proper configuration
    """
    import yt_dlp
    import tempfile
    import os
    
    config = get_improved_socks5_config(proxy)
    
    # Test with a simple YouTube video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        ydl_opts = {
            **config,
            'quiet': True,
            'no_warnings': True,
            'simulate': True,  # Don't actually download
            'extract_flat': False,
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Try to extract info (this tests the proxy)
                info = ydl.extract_info(test_url, download=False)
                if info and info.get('id'):
                    print(f"✅ SOCKS5 proxy working: {proxy}")
                    return True
                else:
                    print(f"❌ SOCKS5 proxy failed (no info): {proxy}")
                    return False
                    
        except Exception as e:
            print(f"❌ SOCKS5 proxy failed: {proxy} - {str(e)}")
            return False

if __name__ == "__main__":
    # Test the improved configuration
    print("🧦 Testing Improved SOCKS5 Configuration")
    print("=" * 50)
    
    # Example proxy (replace with actual proxy)
    test_proxy = "127.0.0.1:1080"
    
    print("📋 Improved SOCKS5 Config:")
    config = get_improved_socks5_config(test_proxy)
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    print("\n🔄 Fallback Options:")
    for i, fallback in enumerate(get_fallback_socks5_options(), 1):
        print(f"  {i}. {fallback}")
    
    print(f"\n🧪 Testing proxy: {test_proxy}")
    # test_socks5_proxy_with_ytdlp(test_proxy)
    print("(Uncomment test line to run actual proxy test)")
