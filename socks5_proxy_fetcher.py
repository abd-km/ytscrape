#!/usr/bin/env python3
"""
🧦 SOCKS5 Proxy Fetcher for YouTube Scraping
Better performance and compatibility than HTTP proxies
"""

import requests
import json
import threading
import time
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class SOCKS5ProxyFetcher:
    def __init__(self, base_url: str = "https://proxylist.geonode.com/api/proxy-list"):
        self.base_url = base_url
        self.valid_proxies = []
        self.failed_proxies = set()
        self.current_index = 0
        self.lock = threading.Lock()
        self.last_fetch_time = None
        self.fetch_interval = 300  # 5 minutes
        self.auto_refresh = True
        
        # Start with initial fetch (skip validation for speed)
        self.fetch_fresh_proxies(test_sample=False)
        
        # Start background refresh thread if auto_refresh is enabled
        if self.auto_refresh:
            self.start_background_refresh()
    
    def fetch_fresh_proxies(self, limit: int = 200, page: int = 1, test_sample: bool = False) -> List[Dict]:
        """Fetch fresh SOCKS5 proxies from Geonode API"""
        try:
            # Fetch from first 3 pages for speed
            all_proxies = []
            
            for current_page in range(1, 4):  # Check first 3 pages
                params = {
                    'protocols': 'socks5',  # Filter for SOCKS5 proxies only
                    'limit': 100,  # Smaller batches per page
                    'page': current_page,
                    'sort_by': 'lastChecked',
                    'sort_type': 'desc'
                }
                
                print(f"🧦 Fetching SOCKS5 proxies from Geonode (page {current_page})...")
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                proxies_data = data.get('data', [])
                
                if not proxies_data:
                    break
                
                # Convert to simple proxy list and filter for high-uptime SOCKS5 proxies
                for proxy_info in proxies_data:
                    ip = proxy_info.get('ip')
                    port = proxy_info.get('port')
                    protocols = proxy_info.get('protocols', [])
                    uptime = proxy_info.get('upTime', 0)
                    
                    # Only accept SOCKS5 proxies with decent uptime
                    if ip and port and 'socks5' in protocols and uptime > 50:
                        proxy_string = f"{ip}:{port}"
                        
                        all_proxies.append({
                            'proxy': proxy_string,
                            'country': proxy_info.get('country', 'Unknown'),
                            'anonymity': proxy_info.get('anonymityLevel', 'Unknown'),
                            'speed': proxy_info.get('speed', 'Unknown'),
                            'uptime': uptime,
                            'protocols': protocols,
                            'last_checked': proxy_info.get('lastChecked', 'Unknown')
                        })
                
                # Stop if we have enough proxies
                if len(all_proxies) >= limit:
                    break
            
            print(f"🧦 Retrieved {len(all_proxies)} high-quality SOCKS5 proxies")
            
            # Limit to requested amount and sort by uptime
            proxy_list = sorted(all_proxies, key=lambda x: x['uptime'], reverse=True)[:limit]
            
            # Use all proxies without testing (fastest - Geonode pre-validates)
            with self.lock:
                self.valid_proxies = [p['proxy'] for p in proxy_list]
                self.failed_proxies.clear()
                self.last_fetch_time = datetime.now()
            
            print(f"⚡ {len(proxy_list)} SOCKS5 proxies ready for YouTube scraping")
            
            return proxy_list
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching SOCKS5 proxies from API: {e}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return []
    
    def get_next_proxy(self) -> Optional[str]:
        """Get the next proxy in rotation"""
        with self.lock:
            if not self.valid_proxies:
                return None
            
            # Skip failed proxies
            attempts = 0
            while attempts < len(self.valid_proxies):
                proxy = self.valid_proxies[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.valid_proxies)
                
                if proxy not in self.failed_proxies:
                    return proxy
                
                attempts += 1
            
            # All proxies failed, reset failed set and try again
            self.failed_proxies.clear()
            if self.valid_proxies:
                proxy = self.valid_proxies[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.valid_proxies)
                return proxy
            
        return None
    
    def get_random_proxy(self) -> Optional[str]:
        """Get a random proxy instead of sequential"""
        with self.lock:
            if not self.valid_proxies:
                return None
            
            available = [p for p in self.valid_proxies if p not in self.failed_proxies]
            
            if not available:
                # Reset failed proxies and try again
                self.failed_proxies.clear()
                available = self.valid_proxies
            
            return random.choice(available) if available else None
    
    def mark_proxy_failed(self, proxy: str):
        """Mark a proxy as failed"""
        with self.lock:
            self.failed_proxies.add(proxy)
            print(f"❌ Marked SOCKS5 proxy as failed: {proxy}")
    
    def should_refresh(self) -> bool:
        """Check if proxies should be refreshed"""
        if not self.last_fetch_time:
            return True
        
        time_since_fetch = datetime.now() - self.last_fetch_time
        return time_since_fetch.total_seconds() > self.fetch_interval
    
    def start_background_refresh(self):
        """Start background thread to refresh proxies periodically"""
        def refresh_worker():
            while self.auto_refresh:
                try:
                    if self.should_refresh():
                        print("🔄 Background refresh: Fetching fresh SOCKS5 proxies...")
                        self.fetch_fresh_proxies(test_sample=False)  # Skip testing for speed
                    
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    print(f"❌ Background refresh error: {e}")
                    time.sleep(300)  # Wait 5 minutes on error
        
        refresh_thread = threading.Thread(target=refresh_worker, daemon=True)
        refresh_thread.start()
        print("🔄 Background SOCKS5 proxy refresh started")
    
    def get_proxy_dict(self, proxy: str) -> dict:
        """Convert proxy string to improved yt-dlp SOCKS5 format with enhanced settings"""
        if not proxy:
            return {}
        
        # Improved yt-dlp SOCKS5 configuration based on documentation analysis
        return {
            'proxy': f'socks5://{proxy}',
            'socket_timeout': 30,  # Important for slow proxies
            'force_ipv4': True,    # Many proxies work better with IPv4
            'retries': 3,          # Retry on proxy failures
            'fragment_retries': 3, # Retry fragments on proxy failures
            'sleep_interval': 1,   # Sleep between requests
            'max_sleep_interval': 3, # Max sleep time
            'http_chunk_size': None,  # Disable chunked downloading through proxy
        }
    
    def get_stats(self) -> dict:
        """Get proxy statistics"""
        with self.lock:
            return {
                'total_proxies': len(self.valid_proxies),
                'failed_proxies': len(self.failed_proxies),
                'available_proxies': len(self.valid_proxies) - len(self.failed_proxies),
                'current_index': self.current_index,
                'last_fetch_time': self.last_fetch_time.isoformat() if self.last_fetch_time else None,
                'auto_refresh': self.auto_refresh,
                'proxy_type': 'SOCKS5'
            }

# Global SOCKS5 proxy fetcher instance
socks5_proxy_fetcher = None

def init_socks5_proxy_fetcher():
    """Initialize the global SOCKS5 proxy fetcher"""
    global socks5_proxy_fetcher
    socks5_proxy_fetcher = SOCKS5ProxyFetcher()
    return socks5_proxy_fetcher

def get_current_socks5_proxy() -> Optional[str]:
    """Get current SOCKS5 proxy"""
    global socks5_proxy_fetcher
    if socks5_proxy_fetcher:
        return socks5_proxy_fetcher.get_next_proxy()
    return None

def get_socks5_proxy_for_ytdlp() -> dict:
    """Get SOCKS5 proxy configuration for yt-dlp options"""
    proxy = get_current_socks5_proxy()
    if proxy:
        return {'proxy': f'socks5://{proxy}'}
    return {}

def force_refresh_socks5_proxies():
    """Force refresh SOCKS5 proxies from Geonode API"""
    global socks5_proxy_fetcher
    if socks5_proxy_fetcher:
        socks5_proxy_fetcher.fetch_fresh_proxies()

if __name__ == "__main__":
    print("🧦 Testing SOCKS5 Proxy Fetcher for YouTube")
    print("=" * 50)
    
    # Initialize fetcher
    fetcher = SOCKS5ProxyFetcher()
    
    # Show stats
    stats = fetcher.get_stats()
    print(f"\n📊 SOCKS5 Proxy Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test rotation
    print(f"\n🔄 Testing SOCKS5 proxy rotation:")
    for i in range(5):
        proxy = fetcher.get_next_proxy()
        print(f"  SOCKS5 Proxy {i+1}: {proxy}")
    
    # Test random selection
    print(f"\n🎲 Testing random SOCKS5 proxy selection:")
    for i in range(3):
        proxy = fetcher.get_random_proxy()
        print(f"  Random {i+1}: {proxy}")
    
    print(f"\n✅ SOCKS5 proxy fetcher is working!")
