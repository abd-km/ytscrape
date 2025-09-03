#!/usr/bin/env python3
"""
🧪 Comprehensive Proxy Testing Suite
Test your rotating IPs with YouTube and other services
"""

import requests
import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from proxy_rotator import ProxyRotator
import yt_dlp

class ProxyTester:
    def __init__(self, proxy_file: str = "proxies.txt"):
        self.proxy_file = proxy_file
        self.results = []
        
    def test_proxy_basic(self, proxy: str, timeout: int = 10) -> dict:
        """Basic proxy connectivity test"""
        result = {
            'proxy': proxy,
            'basic_connectivity': False,
            'ip_info': None,
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
                'http://httpbin.org/ip',
                proxies=proxy_dict,
                timeout=timeout
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result['basic_connectivity'] = True
                result['response_time'] = round(response_time, 2)
                result['ip_info'] = response.json()
            else:
                result['error'] = f"HTTP {response.status_code}"
                
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def test_proxy_youtube(self, proxy: str, timeout: int = 30) -> dict:
        """Test proxy with YouTube (yt-dlp)"""
        result = {
            'proxy': proxy,
            'youtube_compatible': False,
            'test_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',  # Rick Roll for testing
            'error': None
        }
        
        try:
            ydl_opts = {
                'proxy': f'http://{proxy}',
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'socket_timeout': timeout
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Try to extract basic info (no download)
                info = ydl.extract_info(result['test_url'], download=False)
                if info and info.get('title'):
                    result['youtube_compatible'] = True
                    result['title'] = info.get('title', 'Unknown')
                else:
                    result['error'] = 'No video info extracted'
                    
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def test_proxy_comprehensive(self, proxy: str) -> dict:
        """Comprehensive proxy test (basic + YouTube)"""
        print(f"🧪 Testing proxy: {proxy}")
        
        # Basic test
        basic_result = self.test_proxy_basic(proxy)
        
        # YouTube test (only if basic test passes)
        youtube_result = {'youtube_compatible': False, 'error': 'Basic test failed'}
        if basic_result['basic_connectivity']:
            youtube_result = self.test_proxy_youtube(proxy)
        
        # Combine results
        comprehensive_result = {
            'proxy': proxy,
            'basic_connectivity': basic_result['basic_connectivity'],
            'response_time': basic_result['response_time'],
            'ip_info': basic_result['ip_info'],
            'youtube_compatible': youtube_result['youtube_compatible'],
            'basic_error': basic_result['error'],
            'youtube_error': youtube_result['error'],
            'overall_score': self._calculate_score(basic_result, youtube_result)
        }
        
        return comprehensive_result
    
    def _calculate_score(self, basic: dict, youtube: dict) -> int:
        """Calculate overall proxy score (0-100)"""
        score = 0
        
        if basic['basic_connectivity']:
            score += 30
            
            # Response time bonus
            if basic['response_time']:
                if basic['response_time'] < 2:
                    score += 20
                elif basic['response_time'] < 5:
                    score += 15
                elif basic['response_time'] < 10:
                    score += 10
                else:
                    score += 5
        
        if youtube['youtube_compatible']:
            score += 50
            
        return score
    
    def test_batch_parallel(self, proxies: list, max_workers: int = 20) -> list:
        """Test multiple proxies in parallel"""
        print(f"🚀 Testing {len(proxies)} proxies with {max_workers} workers...")
        
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
                    
                    # Show progress
                    status = "✅ GOOD" if result['overall_score'] >= 80 else \
                           "⚠️ OK" if result['overall_score'] >= 50 else \
                           "❌ BAD"
                    
                    print(f"{status} {proxy} - Score: {result['overall_score']}/100")
                    
                except Exception as e:
                    print(f"❌ ERROR {proxy}: {e}")
                    results.append({
                        'proxy': proxy,
                        'basic_connectivity': False,
                        'youtube_compatible': False,
                        'overall_score': 0,
                        'error': str(e)
                    })
        
        return results
    
    def generate_report(self, results: list) -> dict:
        """Generate comprehensive test report"""
        if not results:
            return {"error": "No results to analyze"}
        
        total = len(results)
        basic_working = sum(1 for r in results if r.get('basic_connectivity'))
        youtube_working = sum(1 for r in results if r.get('youtube_compatible'))
        
        # Score distribution
        excellent = sum(1 for r in results if r.get('overall_score', 0) >= 80)
        good = sum(1 for r in results if 50 <= r.get('overall_score', 0) < 80)
        poor = sum(1 for r in results if r.get('overall_score', 0) < 50)
        
        # Best proxies (top 10)
        best_proxies = sorted(
            results, 
            key=lambda x: x.get('overall_score', 0), 
            reverse=True
        )[:10]
        
        # Response time stats
        response_times = [r.get('response_time') for r in results if r.get('response_time')]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        report = {
            'summary': {
                'total_tested': total,
                'basic_connectivity': f"{basic_working}/{total} ({basic_working/total*100:.1f}%)",
                'youtube_compatible': f"{youtube_working}/{total} ({youtube_working/total*100:.1f}%)",
                'average_response_time': f"{avg_response_time:.2f}s" if avg_response_time else "N/A"
            },
            'score_distribution': {
                'excellent (80-100)': excellent,
                'good (50-79)': good,
                'poor (0-49)': poor
            },
            'top_10_proxies': [
                {
                    'proxy': p['proxy'],
                    'score': p.get('overall_score', 0),
                    'response_time': p.get('response_time'),
                    'youtube_ok': p.get('youtube_compatible', False)
                }
                for p in best_proxies
            ],
            'recommendations': self._get_recommendations(results)
        }
        
        return report
    
    def _get_recommendations(self, results: list) -> list:
        """Get recommendations based on test results"""
        recommendations = []
        
        total = len(results)
        basic_working = sum(1 for r in results if r.get('basic_connectivity'))
        youtube_working = sum(1 for r in results if r.get('youtube_compatible'))
        
        if basic_working / total < 0.3:
            recommendations.append("⚠️ Low success rate for basic connectivity. Consider updating your proxy list.")
        
        if youtube_working / total < 0.2:
            recommendations.append("⚠️ Very few proxies work with YouTube. YouTube has strong anti-proxy measures.")
            
        if youtube_working > 0:
            recommendations.append(f"✅ Found {youtube_working} YouTube-compatible proxies. Use these for your scraper.")
            
        # Response time recommendations
        response_times = [r.get('response_time') for r in results if r.get('response_time')]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            if avg_time > 10:
                recommendations.append("🐌 Average response time is high. Consider filtering by response time.")
        
        return recommendations if recommendations else ["✅ Proxy performance looks good!"]

def main():
    """Run comprehensive proxy testing"""
    print("🧪 Comprehensive Proxy Testing Suite")
    print("=" * 50)
    
    # Load proxies
    tester = ProxyTester()
    
    try:
        with open(tester.proxy_file, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        
        print(f"📁 Loaded {len(proxies)} proxies from {tester.proxy_file}")
        
        # Test a subset for demo (first 20)
        test_proxies = proxies[:20]
        print(f"🧪 Testing first {len(test_proxies)} proxies for demonstration...")
        
        # Run tests
        results = tester.test_batch_parallel(test_proxies, max_workers=10)
        
        # Generate report
        print("\n📊 Generating report...")
        report = tester.generate_report(results)
        
        # Display report
        print("\n" + "=" * 50)
        print("📋 TEST REPORT")
        print("=" * 50)
        
        print(f"\n📈 SUMMARY:")
        for key, value in report['summary'].items():
            print(f"  {key}: {value}")
        
        print(f"\n📊 SCORE DISTRIBUTION:")
        for key, value in report['score_distribution'].items():
            print(f"  {key}: {value}")
        
        print(f"\n🏆 TOP 10 PROXIES:")
        for i, proxy in enumerate(report['top_10_proxies'], 1):
            youtube_icon = "🎵" if proxy['youtube_ok'] else "❌"
            print(f"  {i:2d}. {proxy['proxy']} - Score: {proxy['score']}/100 {youtube_icon}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        # Save results to file
        with open('proxy_test_results.json', 'w') as f:
            json.dump({
                'results': results,
                'report': report,
                'timestamp': time.time()
            }, f, indent=2)
        
        print(f"\n💾 Full results saved to: proxy_test_results.json")
        
    except FileNotFoundError:
        print(f"❌ Proxy file '{tester.proxy_file}' not found!")
        print("   Create the file with one proxy per line (IP:PORT format)")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
