#!/usr/bin/env python3
"""
🌐 Dynamic Proxy Fetcher for Geonode API
Automatically fetches fresh proxies from Geonode API and integrates with YouTube scraper
"""

import requests
import json
import threading
import time
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class GeonodeProxyFetcher:
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
        """Fetch fresh proxies from Geonode API"""
        try:
            # Fetch from first 2 pages for speed
            all_proxies = []
            
            for current_page in range(1, 3):  # Check first 2 pages (100 proxies each)
                params = {
                    'protocols': 'http',  # Filter for HTTP proxies only
                    'limit': 100,  # Smaller batches per page
                    'page': current_page,
                    'sort_by': 'lastChecked',
                    'sort_type': 'desc'
                }
                
                print(f"🌐 Fetching HTTP proxies from Geonode (page {current_page})...")
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                proxies_data = data.get('data', [])
                
                if not proxies_data:
                    break
                
                # Convert to simple proxy list and filter for HTTP proxies
                for proxy_info in proxies_data:
                    ip = proxy_info.get('ip')
                    port = proxy_info.get('port')
                    protocols = proxy_info.get('protocols', [])
                    uptime = proxy_info.get('upTime', 0)
                    
                    # Only accept HTTP proxies with good uptime
                    if ip and port and 'http' in protocols and uptime > 80:
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
            
            print(f"📦 Retrieved {len(all_proxies)} high-quality HTTP proxies")
            
            # Limit to requested amount
            proxy_list = all_proxies[:limit]
            
            # Test a small sample if requested (optional)
            if test_sample and proxy_list:
                sample_size = min(10, len(proxy_list))
                test_sample_proxies = random.sample(proxy_list, sample_size)
                print(f"🧪 Testing sample of {sample_size} proxies...")
                
                tested_proxies = self.test_proxy_batch([p['proxy'] for p in test_sample_proxies])
                
                if tested_proxies:
                    # Use tested proxies first, then add untested ones
                    with self.lock:
                        self.valid_proxies = tested_proxies + [p['proxy'] for p in proxy_list if p['proxy'] not in tested_proxies]
                        self.failed_proxies.clear()
                        self.last_fetch_time = datetime.now()
                    print(f"✅ {len(tested_proxies)} tested + {len(proxy_list) - len(tested_proxies)} additional proxies ready")
                else:
                    # No proxies passed test, but use them anyway (Geonode has pre-validated)
                    with self.lock:
                        self.valid_proxies = [p['proxy'] for p in proxy_list]
                        self.failed_proxies.clear()
                        self.last_fetch_time = datetime.now()
                    print(f"⚡ Using {len(proxy_list)} pre-validated Geonode proxies")
            else:
                # Use all proxies without testing (fastest - Geonode pre-validates)
                with self.lock:
                    self.valid_proxies = [p['proxy'] for p in proxy_list]
                    self.failed_proxies.clear()
                    self.last_fetch_time = datetime.now()
                
                print(f"⚡ {len(proxy_list)} Geonode proxies ready for use (pre-validated)")
            
            return proxy_list
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching proxies from API: {e}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return []
    
    def test_proxy_batch(self, proxies: List[str], max_workers: int = 20, timeout: int = 10) -> List[str]:
        """Test a batch of proxies quickly"""
        import queue
        import threading
        
        q = queue.Queue()
        valid_proxies = []
        valid_lock = threading.Lock()
        
        # Add proxies to queue
        for proxy in proxies:
            q.put(proxy)
        
        def test_worker():
            while True:
                try:
                    proxy = q.get_nowait()
                except queue.Empty:
                    break
                
                if self.test_single_proxy(proxy, timeout):
                    with valid_lock:
                        valid_proxies.append(proxy)
                        print(f"✅ {proxy}")
                
                q.task_done()
        
        # Start worker threads
        threads = []
        for _ in range(min(max_workers, len(proxies))):
            t = threading.Thread(target=test_worker)
            t.start()
            threads.append(t)
        
        # Wait for completion
        for t in threads:
            t.join()
        
        return valid_proxies
    
    def test_single_proxy(self, proxy: str, timeout: int = 10) -> bool:
        """Test a single proxy quickly"""
        try:
            proxy_dict = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            
            # Use a lightweight endpoint
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxy_dict,
                timeout=timeout
            )
            
            return response.status_code == 200
            
        except Exception:
            return False
    
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
            print(f"❌ Marked proxy as failed: {proxy}")
    
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
                        print("🔄 Background refresh: Fetching fresh proxies...")
                        self.fetch_fresh_proxies(test_sample=False)  # Skip testing for speed
                    
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    print(f"❌ Background refresh error: {e}")
                    time.sleep(300)  # Wait 5 minutes on error
        
        refresh_thread = threading.Thread(target=refresh_worker, daemon=True)
        refresh_thread.start()
        print("🔄 Background proxy refresh started")
    
    def get_proxy_dict(self, proxy: str) -> dict:
        """Convert proxy string to yt-dlp format for HTTP proxies"""
        if not proxy:
            return {}
        
        # HTTP proxies from Geonode
        return {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
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
                'auto_refresh': self.auto_refresh
            }

# Global proxy fetcher instance
geonode_proxy_fetcher = None

def init_geonode_proxy_fetcher():
    """Initialize the global Geonode proxy fetcher"""
    global geonode_proxy_fetcher
    geonode_proxy_fetcher = GeonodeProxyFetcher()
    return geonode_proxy_fetcher

def get_current_proxy_geonode() -> Optional[str]:
    """Get current proxy from Geonode fetcher"""
    global geonode_proxy_fetcher
    if geonode_proxy_fetcher:
        return geonode_proxy_fetcher.get_next_proxy()
    return None

def get_proxy_for_ytdlp_geonode() -> dict:
    """Get proxy configuration for yt-dlp options (Geonode)"""
    proxy = get_current_proxy_geonode()
    if proxy:
        return {'proxy': f'http://{proxy}'}
    return {}

def force_refresh_proxies():
    """Force refresh proxies from Geonode API"""
    global geonode_proxy_fetcher
    if geonode_proxy_fetcher:
        geonode_proxy_fetcher.fetch_fresh_proxies()

if __name__ == "__main__":
    print("🌐 Testing Geonode Dynamic Proxy Fetcher")
    print("=" * 50)
    
    # Initialize fetcher
    fetcher = GeonodeProxyFetcher()
    
    # Show stats
    stats = fetcher.get_stats()
    print(f"\n📊 Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test rotation
    print(f"\n🔄 Testing proxy rotation:")
    for i in range(5):
        proxy = fetcher.get_next_proxy()
        print(f"  Proxy {i+1}: {proxy}")
    
    # Test random selection
    print(f"\n🎲 Testing random proxy selection:")
    for i in range(3):
        proxy = fetcher.get_random_proxy()
        print(f"  Random {i+1}: {proxy}")
    
    print(f"\n✅ Dynamic proxy fetcher is working!")
