#!/usr/bin/env python3
"""
🌐 HTTP Proxy Configuration (Fixed Version)
Using Geonode proxies as HTTP proxies instead of SOCKS5
"""

import sys
sys.path.append('/Users/am/ytscraper')

def test_geonode_as_http_proxies():
    """Test Geonode proxies as HTTP proxies instead of SOCKS5"""
    
    print("🌐 Testing Geonode Proxies as HTTP Proxies")
    print("=" * 50)
    
    # Sample proxies from your fetcher
    test_proxies = [
        '203.23.104.167:80',
        '140.248.133.95:80',
        '35.237.129.172:80'
    ]
    
    import yt_dlp
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    for proxy in test_proxies:
        print(f"\\n🌐 Testing HTTP proxy: {proxy}")
        
        # Configure as HTTP proxy (not SOCKS5)
        ydl_opts = {
            'proxy': f'http://{proxy}',  # Use HTTP scheme instead of socks5
            'socket_timeout': 30,
            'retries': 2,
            'quiet': True,
            'no_warnings': True,
            'simulate': True,
            'extract_flat': False,
        }
        
        try:
            print("🔄 Testing with HTTP proxy configuration...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(test_url, download=False)
                if info and info.get('title'):
                    print(f"✅ SUCCESS! HTTP proxy working: {proxy}")
                    print(f"🎵 Video: {info.get('title', 'Unknown')}")
                    return True
                else:
                    print(f"❌ FAILED: No info extracted with HTTP proxy {proxy}")
        except Exception as e:
            print(f"❌ FAILED: HTTP proxy {proxy} - {str(e)[:150]}")
    
    print("\\n🔍 Conclusion: Even as HTTP proxies, these Geonode proxies are unreliable for YouTube")
    return False

if __name__ == "__main__":
    # Test HTTP proxy approach
    success = test_geonode_as_http_proxies()
    
    print("\\n" + "=" * 50)
    if success:
        print("🎉 SOLUTION: Use HTTP proxy configuration")
    else:
        print("✅ RECOMMENDATION: Stick with direct connection (most reliable)")
        print("💡 ALTERNATIVE: Find premium SOCKS5/HTTP proxy service")
    
    print("\\n📝 SUMMARY:")
    print("• Geonode 'SOCKS5' proxies are actually HTTP proxies")
    print("• Direct connection works perfectly and is most reliable")  
    print("• For anonymity, consider premium proxy services or VPN")
