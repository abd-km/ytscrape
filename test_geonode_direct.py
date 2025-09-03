#!/usr/bin/env python3
"""
🌐 Quick test of Geonode proxy fetching without validation
"""
import requests
import random

def test_geonode_direct():
    """Test fetching proxies directly from Geonode"""
    url = "https://proxylist.geonode.com/api/proxy-list"
    params = {
        'protocols': 'http',
        'limit': 20,
        'page': 1,
        'sort_by': 'lastChecked',
        'sort_type': 'desc'
    }
    
    try:
        print("🌐 Fetching HTTP proxies from Geonode...")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        proxies = data.get('data', [])
        
        print(f"✅ Retrieved {len(proxies)} HTTP proxies")
        
        # Show first 10 proxies
        for i, proxy in enumerate(proxies[:10]):
            ip = proxy.get('ip')
            port = proxy.get('port')
            country = proxy.get('country', '??')
            uptime = proxy.get('upTime', 0)
            protocols = proxy.get('protocols', [])
            
            print(f"  {i+1:2d}. {ip}:{port} [{country}] {uptime:.1f}% uptime - {protocols}")
        
        # Return proxy list for integration
        proxy_list = []
        for proxy in proxies:
            if proxy.get('ip') and proxy.get('port'):
                proxy_list.append(f"{proxy['ip']}:{proxy['port']}")
        
        print(f"\n🎯 Ready to use: {len(proxy_list)} proxies")
        return proxy_list
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    proxies = test_geonode_direct()
    
    if proxies:
        print(f"\n🧪 Sample of 5 proxies for testing:")
        sample = random.sample(proxies, min(5, len(proxies)))
        for i, proxy in enumerate(sample):
            print(f"  {i+1}. {proxy}")
    else:
        print("❌ No proxies available")
