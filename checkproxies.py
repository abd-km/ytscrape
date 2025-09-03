import threading
import queue 
import requests


q = queue.Queue()
valid_proxies=[]

with open("proxies.txt","r") as f:
    proxies = f.read().split("\n")
    for proxy in proxies:
        if proxy.strip():  # Only add non-empty proxies
            q.put(proxy.strip())

print(f"Loaded {q.qsize()} proxies from file")

def check_proxy():
    while True:
        try:
            proxy = q.get(timeout=1)  # Wait up to 1 second for a proxy
        except queue.Empty:
            break
        
        try:
            response = requests.get("http://ipinfo.io/json",
                                    proxies={"http":f"http://{proxy}",
                                             "https":f"http://{proxy}"},timeout=5)
            if response.status_code == 200:
                print(f"Valid proxy: {proxy}")
                valid_proxies.append(proxy)
        except Exception as e:
            # Optionally print errors for debugging
            # print(f"Failed proxy {proxy}: {str(e)}")
            pass
        finally:
            q.task_done()

# Start threads
threads = []
for _ in range(10):
    t = threading.Thread(target=check_proxy)
    t.start()
    threads.append(t)

# Wait for all threads to complete
for t in threads:
    t.join()

print(f"\nFound {len(valid_proxies)} valid proxies:")
for proxy in valid_proxies:
    print(proxy)
