#!/usr/bin/env python3
"""
🧪 YouTube Proxy Tester
Test proxies specifically with YouTube and yt-dlp to ensure compatibility
"""

import requests
import yt_dlp
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dynamic_proxy_fetcher import GeonodeProxyFetcher
import json

class YouTubeProxyTester:
    def __init__(self):
        self.test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - always available
        self.test_channel = "https://youtube.com/@PewDiePie"  # Popular channel for testing
        
    def test_proxy_basic_http(self, proxy: str, timeout: int = 10) -> dict:
        """Test basic HTTP connectivity through proxy"""
        result = {
            'proxy': proxy,
            'basic_http': False,
            'response_time': None,
            'ip_info': None,
            'error': None
        }
        
        try:
            proxy_dict = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            
            start_time = time.time()
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxy_dict,
                timeout=timeout
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result['basic_http'] = True
                result['response_time'] = round(response_time, 2)
                result['ip_info'] = response.json()
            else:
                result['error'] = f"HTTP {response.status_code}"
                
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def test_proxy_youtube_access(self, proxy: str, timeout: int = 30) -> dict:
        """Test if proxy can access YouTube homepage"""
        result = {
            'proxy': proxy,
            'youtube_access': False,
            'response_time': None,
            'error': None
        }
        
        try:
            proxy_dict = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            
            start_time = time.time()
            response = requests.get(
                'https://www.youtube.com',
                proxies=proxy_dict,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200 and 'YouTube' in response.text:
                result['youtube_access'] = True
                result['response_time'] = round(response_time, 2)
            else:
                result['error'] = f"HTTP {response.status_code}"
                
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def test_proxy_ytdlp(self, proxy: str, timeout: int = 60) -> dict:
        """Test if proxy works with yt-dlp for YouTube video extraction"""
        result = {
            'proxy': proxy,
            'ytdlp_compatible': False,
            'video_title': None,
            'extraction_time': None,
            'error': None
        }
        
        try:
            ydl_opts = {
                'proxy': f'http://{proxy}',
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # Don't download, just extract info
                'socket_timeout': timeout,
                'retries': 1
            }
            
            start_time = time.time()
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.test_url, download=False)
                
                if info and info.get('title'):
                    extraction_time = time.time() - start_time
                    result['ytdlp_compatible'] = True
                    result['video_title'] = info.get('title', 'Unknown')
                    result['extraction_time'] = round(extraction_time, 2)
                else:
                    result['error'] = 'No video info extracted'
                    
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def test_proxy_comprehensive(self, proxy: str) -> dict:
        """Comprehensive proxy test for YouTube usage"""
        print(f"🧪 Testing proxy: {proxy}")
        
        # Test 1: Basic HTTP connectivity
        basic_result = self.test_proxy_basic_http(proxy)
        
        # Test 2: YouTube homepage access (only if basic passes)
        youtube_access = {'youtube_access': False, 'error': 'Basic test failed'}
        if basic_result['basic_http']:
            youtube_access = self.test_proxy_youtube_access(proxy)
        
        # Test 3: yt-dlp compatibility (only if YouTube access works)
        ytdlp_result = {'ytdlp_compatible': False, 'error': 'YouTube access failed'}
        if youtube_access['youtube_access']:
            ytdlp_result = self.test_proxy_ytdlp(proxy)
        
        # Combine results
        comprehensive_result = {
            'proxy': proxy,
            'basic_http': basic_result['basic_http'],
            'basic_response_time': basic_result['response_time'],
            'youtube_access': youtube_access['youtube_access'],
            'youtube_response_time': youtube_access.get('response_time'),
            'ytdlp_compatible': ytdlp_result['ytdlp_compatible'],
            'ytdlp_extraction_time': ytdlp_result.get('extraction_time'),
            'video_title': ytdlp_result.get('video_title'),
            'ip_info': basic_result['ip_info'],
            'errors': {
                'basic': basic_result['error'],
                'youtube': youtube_access['error'],
                'ytdlp': ytdlp_result['error']
            },
            'overall_score': self._calculate_score(basic_result, youtube_access, ytdlp_result)
        }
        
        return comprehensive_result
    
    def _calculate_score(self, basic: dict, youtube: dict, ytdlp: dict) -> int:
        """Calculate overall proxy score for YouTube usage (0-100)"""
        score = 0
        
        # Basic connectivity (20 points)
        if basic['basic_http']:
            score += 20
            
            # Response time bonus (10 points max)
            if basic['response_time']:
                if basic['response_time'] < 2:
                    score += 10
                elif basic['response_time'] < 5:
                    score += 7
                elif basic['response_time'] < 10:
                    score += 5
                else:
                    score += 2
        
        # YouTube access (30 points)
        if youtube['youtube_access']:
            score += 30
        
        # yt-dlp compatibility (40 points - most important)
        if ytdlp['ytdlp_compatible']:
            score += 40
            
        return score
    
    def test_batch_parallel(self, proxies: list, max_workers: int = 10) -> list:
        """Test multiple proxies in parallel"""
        print(f"🚀 Testing {len(proxies)} proxies for YouTube compatibility...")
        print(f"📺 Test URL: {self.test_url}")
        print(f"⚡ Using {max_workers} parallel workers")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_proxy = {
                executor.submit(self.test_proxy_comprehensive, proxy): proxy 
                for proxy in proxies
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Show progress with detailed status
                    if result['overall_score'] >= 90:
                        status = "🟢 EXCELLENT"
                    elif result['overall_score'] >= 70:
                        status = "🟡 GOOD"
                    elif result['overall_score'] >= 40:
                        status = "🟠 PARTIAL"
                    else:
                        status = "🔴 FAILED"
                    
                    ytdlp_status = "✅" if result['ytdlp_compatible'] else "❌"
                    
                    print(f"{status} {proxy} - Score: {result['overall_score']}/100 - yt-dlp: {ytdlp_status}")
                    
                except Exception as e:
                    print(f"❌ ERROR {proxy}: {e}")
                    results.append({
                        'proxy': proxy,
                        'basic_http': False,
                        'youtube_access': False,
                        'ytdlp_compatible': False,
                        'overall_score': 0,
                        'error': str(e)
                    })
        
        return results
    
    def generate_report(self, results: list) -> dict:
        """Generate comprehensive test report"""
        if not results:
            return {"error": "No results to analyze"}
        
        total = len(results)
        basic_working = sum(1 for r in results if r.get('basic_http'))
        youtube_working = sum(1 for r in results if r.get('youtube_access'))
        ytdlp_working = sum(1 for r in results if r.get('ytdlp_compatible'))
        
        # Best working proxies (yt-dlp compatible)
        working_proxies = [r for r in results if r.get('ytdlp_compatible')]
        working_proxies.sort(key=lambda x: x.get('overall_score', 0), reverse=True)
        
        report = {
            'summary': {
                'total_tested': total,
                'basic_connectivity': f"{basic_working}/{total} ({basic_working/total*100:.1f}%)",
                'youtube_access': f"{youtube_working}/{total} ({youtube_working/total*100:.1f}%)",
                'ytdlp_compatible': f"{ytdlp_working}/{total} ({ytdlp_working/total*100:.1f}%)",
                'success_rate': f"{ytdlp_working/total*100:.1f}%"
            },
            'working_proxies': [
                {
                    'proxy': p['proxy'],
                    'score': p.get('overall_score', 0),
                    'basic_time': p.get('basic_response_time'),
                    'ytdlp_time': p.get('ytdlp_extraction_time'),
                    'country': p.get('ip_info', {}).get('origin', 'Unknown') if p.get('ip_info') else 'Unknown'
                }
                for p in working_proxies[:20]  # Top 20
            ],
            'recommendations': self._get_recommendations(results)
        }
        
        return report
    
    def _get_recommendations(self, results: list) -> list:
        """Get recommendations based on test results"""
        recommendations = []
        
        total = len(results)
        ytdlp_working = sum(1 for r in results if r.get('ytdlp_compatible'))
        
        if ytdlp_working == 0:
            recommendations.append("❌ No proxies work with yt-dlp. Consider using direct connection or different proxy source.")
        elif ytdlp_working / total < 0.1:
            recommendations.append("⚠️ Very few proxies work with YouTube. YouTube has strong anti-proxy measures.")
        elif ytdlp_working / total < 0.3:
            recommendations.append("🔶 Some proxies work, but success rate is low. Consider filtering by score.")
        else:
            recommendations.append(f"✅ Good proxy compatibility! {ytdlp_working} proxies work with yt-dlp.")
        
        if ytdlp_working > 0:
            recommendations.append(f"💡 Use the {min(ytdlp_working, 10)} highest-scoring proxies for best performance.")
        
        return recommendations if recommendations else ["✅ Proxy performance looks good!"]

def test_current_geonode_proxies():
    """Test current Geonode proxies"""
    print("🌐 Testing Current Geonode Proxies for YouTube Compatibility")
    print("=" * 70)
    
    # Get proxies from current fetcher
    fetcher = GeonodeProxyFetcher()
    stats = fetcher.get_stats()
    
    print(f"📊 Proxy Stats: {stats['total_proxies']} total, {stats['available_proxies']} available")
    
    # Test first 20 proxies
    test_proxies = []
    for _ in range(min(20, stats['available_proxies'])):
        proxy = fetcher.get_next_proxy()
        if proxy:
            test_proxies.append(proxy)
    
    if not test_proxies:
        print("❌ No proxies available to test")
        return
    
    # Run comprehensive tests
    tester = YouTubeProxyTester()
    results = tester.test_batch_parallel(test_proxies, max_workers=5)
    
    # Generate and display report
    report = tester.generate_report(results)
    
    print("\n" + "=" * 70)
    print("📋 YOUTUBE PROXY TEST REPORT")
    print("=" * 70)
    
    print(f"\n📈 SUMMARY:")
    for key, value in report['summary'].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    if report['working_proxies']:
        print(f"\n🏆 TOP WORKING PROXIES (yt-dlp compatible):")
        for i, proxy in enumerate(report['working_proxies'][:10], 1):
            print(f"  {i:2d}. {proxy['proxy']} [{proxy['country']}] - Score: {proxy['score']}/100")
    else:
        print(f"\n❌ NO WORKING PROXIES FOUND")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for rec in report['recommendations']:
        print(f"  {rec}")
    
    # Save results
    with open('youtube_proxy_test_results.json', 'w') as f:
        json.dump({
            'results': results,
            'report': report,
            'timestamp': time.time()
        }, f, indent=2)
    
    print(f"\n💾 Full results saved to: youtube_proxy_test_results.json")
    
    return report

if __name__ == "__main__":
    test_current_geonode_proxies()
