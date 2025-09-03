#!/usr/bin/env python3
"""
🍎 iCloud Private Relay Integration
Configure yt-dlp to use system proxy settings (iCloud Private Relay)
"""

import os
import subprocess
import requests
from typing import Dict, Optional

class iCloudPrivateRelayManager:
    def __init__(self):
        self.is_enabled = False
        self.current_ip = None
        self.original_ip = None
        self.check_private_relay_status()
    
    def check_private_relay_status(self):
        """Check if iCloud Private Relay is active"""
        try:
            # Get current IP to see if it's different from original
            response = requests.get('http://httpbin.org/ip', timeout=10)
            if response.status_code == 200:
                self.current_ip = response.json().get('origin', 'Unknown')
                print(f"🌐 Current IP: {self.current_ip}")
                
                # Check if we're using Apple's infrastructure
                self.is_enabled = self.detect_apple_relay()
                
        except Exception as e:
            print(f"❌ Error checking IP: {e}")
            self.is_enabled = False
    
    def detect_apple_relay(self) -> bool:
        """Detect if we're using Apple's Private Relay"""
        try:
            # Check system network settings for proxy
            result = subprocess.run([
                'networksetup', '-getwebproxy', 'Wi-Fi'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                output = result.stdout.lower()
                if 'enabled: yes' in output:
                    print("🍎 System proxy detected (likely iCloud Private Relay)")
                    return True
            
            # Alternative: Check if our IP appears to be from Apple's ranges
            if self.current_ip:
                # This is a simplified check - Apple uses various IP ranges
                apple_indicators = ['apple', 'cupertino', 'icloud']
                ip_info = self.get_ip_info()
                
                if ip_info:
                    org_info = ip_info.get('org', '').lower()
                    for indicator in apple_indicators:
                        if indicator in org_info:
                            print(f"🍎 Apple infrastructure detected: {org_info}")
                            return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error detecting Apple relay: {e}")
            return False
    
    def get_ip_info(self) -> Optional[Dict]:
        """Get detailed IP information"""
        try:
            response = requests.get('http://ipinfo.io/json', timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    def get_ytdlp_config(self) -> Dict:
        """Get yt-dlp configuration for system proxy usage"""
        if self.is_enabled:
            # Use system proxy settings
            return {
                # yt-dlp will automatically use system proxy when no explicit proxy is set
                'prefer_system_proxy': True
            }
        else:
            print("⚠️ iCloud Private Relay not detected - using direct connection")
            return {}
    
    def test_youtube_access(self) -> Dict:
        """Test YouTube access through current connection"""
        try:
            print("🧪 Testing YouTube access...")
            
            # Test 1: Basic YouTube homepage
            response = requests.get('https://www.youtube.com', timeout=15)
            youtube_accessible = response.status_code == 200 and 'YouTube' in response.text
            
            # Test 2: yt-dlp extraction test
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'socket_timeout': 30
            }
            
            test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            ytdlp_working = False
            video_title = None
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(test_url, download=False)
                    if info and info.get('title'):
                        ytdlp_working = True
                        video_title = info.get('title')
            except Exception as e:
                print(f"yt-dlp test failed: {e}")
            
            return {
                'private_relay_active': self.is_enabled,
                'current_ip': self.current_ip,
                'youtube_accessible': youtube_accessible,
                'ytdlp_working': ytdlp_working,
                'video_title': video_title,
                'recommendation': self.get_recommendation(youtube_accessible, ytdlp_working)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'private_relay_active': self.is_enabled,
                'recommendation': 'Unable to test - check your internet connection'
            }
    
    def get_recommendation(self, youtube_ok: bool, ytdlp_ok: bool) -> str:
        """Get recommendation based on test results"""
        if youtube_ok and ytdlp_ok:
            if self.is_enabled:
                return "🟢 Perfect! iCloud Private Relay is working great with YouTube"
            else:
                return "🟢 Direct connection working fine - no proxy needed"
        elif youtube_ok and not ytdlp_ok:
            return "🟡 YouTube accessible but yt-dlp having issues - try enabling iCloud Private Relay"
        elif not youtube_ok:
            return "🔴 YouTube not accessible - check your connection or enable iCloud Private Relay"
        else:
            return "🟡 Mixed results - try different settings"
    
    def configure_for_scraper(self) -> Dict:
        """Get configuration for YouTube scraper"""
        config = {
            'use_private_relay': self.is_enabled,
            'current_ip': self.current_ip,
            'ytdlp_config': self.get_ytdlp_config()
        }
        
        if self.is_enabled:
            print("🍎 Configuring scraper to use iCloud Private Relay")
        else:
            print("🌐 Configuring scraper for direct connection")
            
        return config

def test_icloud_private_relay():
    """Test iCloud Private Relay setup"""
    print("🍎 Testing iCloud Private Relay Integration")
    print("=" * 50)
    
    manager = iCloudPrivateRelayManager()
    
    # Show current status
    print(f"\n📊 Status:")
    print(f"  Private Relay Active: {manager.is_enabled}")
    print(f"  Current IP: {manager.current_ip}")
    
    # Get IP details
    ip_info = manager.get_ip_info()
    if ip_info:
        print(f"  Location: {ip_info.get('city', 'Unknown')}, {ip_info.get('country', 'Unknown')}")
        print(f"  ISP: {ip_info.get('org', 'Unknown')}")
    
    # Test YouTube access
    test_results = manager.test_youtube_access()
    
    print(f"\n🧪 YouTube Test Results:")
    print(f"  YouTube Accessible: {test_results.get('youtube_accessible')}")
    print(f"  yt-dlp Working: {test_results.get('ytdlp_working')}")
    if test_results.get('video_title'):
        print(f"  Test Video: {test_results.get('video_title')}")
    
    print(f"\n💡 Recommendation:")
    print(f"  {test_results.get('recommendation')}")
    
    # Get scraper configuration
    scraper_config = manager.configure_for_scraper()
    
    print(f"\n⚙️ Scraper Configuration:")
    for key, value in scraper_config.items():
        print(f"  {key}: {value}")
    
    return manager

if __name__ == "__main__":
    test_icloud_private_relay()
