#!/usr/bin/env python3
"""
🔄 Proxy Rotation Manager for YouTube Scraper
Automatically rotates through valid proxies for yt-dlp downloads
"""

import random
import threading
import time
import requests
from typing import List, Optional
import json

class ProxyRotator:
    def __init__(self, proxy_file: str = "proxies.txt", test_proxies: bool = True):
        self.proxy_file = proxy_file
        self.valid_proxies = []
        self.current_index = 0
        self.lock = threading.Lock()
        self.failed_proxies = set()
        
        # Load and optionally test proxies
        self.load_proxies(test_proxies)
    
    def load_proxies(self, test: bool = True):
        """Load proxies from file and optionally test them"""
        try:
            with open(self.proxy_file, 'r') as f:
                proxies = [line.strip() for line in f if line.strip()]
            
            print(f"📁 Loaded {len(proxies)} proxies from {self.proxy_file}")
            
            if test:
                print("🔍 Testing proxies... (this may take a moment)")
                self.valid_proxies = self.test_proxies_batch(proxies[:50])  # Test first 50 for speed
            else:
                self.valid_proxies = proxies
                
            print(f"✅ {len(self.valid_proxies)} proxies ready for rotation")
            
        except FileNotFoundError:
            print(f"❌ Proxy file {self.proxy_file} not found")
            self.valid_proxies = []
        except Exception as e:
            print(f"❌ Error loading proxies: {e}")
            self.valid_proxies = []
    
    def test_proxies_batch(self, proxies: List[str], max_threads: int = 20) -> List[str]:
        """Test proxies in parallel and return valid ones"""
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
                
                if self.test_single_proxy(proxy):
                    with valid_lock:
                        valid_proxies.append(proxy)
                        print(f"✅ Valid: {proxy}")
                
                q.task_done()
        
        # Start worker threads
        threads = []
        for _ in range(min(max_threads, len(proxies))):
            t = threading.Thread(target=test_worker)
            t.start()
            threads.append(t)
        
        # Wait for completion
        for t in threads:
            t.join()
        
        return valid_proxies
    
    def test_single_proxy(self, proxy: str, timeout: int = 10) -> bool:
        """Test a single proxy"""
        try:
            proxy_dict = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            
            response = requests.get(
                'http://httpbin.org/ip', 
                proxies=proxy_dict, 
                timeout=timeout
            )
            
            if response.status_code == 200:
                return True
                
        except Exception:
            pass
        
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
    
    def get_proxy_dict(self, proxy: str) -> dict:
        """Convert proxy string to yt-dlp format"""
        if not proxy:
            return {}
        
        return {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
    
    def get_stats(self) -> dict:
        """Get proxy rotation statistics"""
        with self.lock:
            return {
                'total_proxies': len(self.valid_proxies),
                'failed_proxies': len(self.failed_proxies),
                'available_proxies': len(self.valid_proxies) - len(self.failed_proxies),
                'current_index': self.current_index
            }

# Global proxy rotator instance
proxy_rotator = None

def init_proxy_rotator(proxy_file: str = "proxies.txt", test_proxies: bool = False):
    """Initialize the global proxy rotator"""
    global proxy_rotator
    proxy_rotator = ProxyRotator(proxy_file, test_proxies)
    return proxy_rotator

def get_current_proxy() -> Optional[str]:
    """Get current proxy for yt-dlp"""
    global proxy_rotator
    if proxy_rotator:
        return proxy_rotator.get_next_proxy()
    return None

def get_proxy_for_ytdlp() -> dict:
    """Get proxy configuration for yt-dlp options"""
    proxy = get_current_proxy()
    if proxy:
        return {'proxy': f'http://{proxy}'}
    return {}

if __name__ == "__main__":
    # Test the proxy rotator
    print("🔄 Testing Proxy Rotator...")
    
    rotator = ProxyRotator(test_proxies=True)
    
    print(f"\n📊 Stats: {rotator.get_stats()}")
    
    print("\n🔄 Testing rotation:")
    for i in range(5):
        proxy = rotator.get_next_proxy()
        print(f"Proxy {i+1}: {proxy}")
    
    print(f"\n📊 Final Stats: {rotator.get_stats()}")
