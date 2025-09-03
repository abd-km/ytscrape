#!/usr/bin/env python3
"""
Simple script to check your current IP address
"""

import requests
import socket
import json
from datetime import datetime

def get_external_ip():
    """Get external (public) IP address"""
    try:
        # Try multiple services in case one is down
        services = [
            'https://api.ipify.org?format=json',
            'https://httpbin.org/ip',
            'https://api.ip.sb/ip'
        ]
        
        for service in services:
            try:
                response = requests.get(service, timeout=5)
                if response.status_code == 200:
                    if 'ipify' in service:
                        return response.json()['ip']
                    elif 'httpbin' in service:
                        return response.json()['origin']
                    else:
                        return response.text.strip()
            except:
                continue
        return "Unable to determine"
    except Exception as e:
        return f"Error: {e}"

def get_local_ip():
    """Get local network IP address"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return f"Error: {e}"

def get_hostname():
    """Get system hostname"""
    try:
        return socket.gethostname()
    except Exception as e:
        return f"Error: {e}"

def get_ip_info(ip):
    """Get detailed information about an IP address"""
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def main():
    print("🌐 IP Address Information")
    print("=" * 40)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get basic IP information
    external_ip = get_external_ip()
    local_ip = get_local_ip()
    hostname = get_hostname()
    
    print(f"🌍 External IP: {external_ip}")
    print(f"🏠 Local IP:    {local_ip}")
    print(f"💻 Hostname:    {hostname}")
    print()
    
    # Get detailed information about external IP
    if external_ip and "Error" not in external_ip and "Unable" not in external_ip:
        print("📍 Location Information:")
        print("-" * 25)
        ip_info = get_ip_info(external_ip)
        if ip_info and ip_info.get('status') == 'success':
            print(f"Country: {ip_info.get('country', 'Unknown')}")
            print(f"Region:  {ip_info.get('regionName', 'Unknown')}")
            print(f"City:    {ip_info.get('city', 'Unknown')}")
            print(f"ISP:     {ip_info.get('isp', 'Unknown')}")
            print(f"Org:     {ip_info.get('org', 'Unknown')}")
            print(f"Timezone: {ip_info.get('timezone', 'Unknown')}")
        else:
            print("Location information not available")
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    main()
