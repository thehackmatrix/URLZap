import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import threading
import queue
import time
import random
import sys
import signal

# ANSI colors for pink color only
PINK = '\033[95m'
RESET = '\033[0m'

# HackMatrix banner (clean, no glitch)
banner = [
"░▒▓█▓▒░░▒▓█▓▒░  ░▒▓██████▓▒░   ░▒▓██████▓▒░  ░▒▓█▓▒░░▒▓█▓▒░       ░▒▓██████████████▓▒░   ░▒▓██████▓▒░  ░▒▓████████▓▒░ ░▒▓███████▓▒░  ░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ",
"░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░       ░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░    ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ",
"░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░        ░▒▓█▓▒░░▒▓█▓▒░       ░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░    ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ",
"░▒▓████████▓▒░ ░▒▓████████▓▒░ ░▒▓█▓▒░        ░▒▓███████▓▒░        ░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░ ░▒▓████████▓▒░    ░▒▓█▓▒░     ░▒▓███████▓▒░  ░▒▓█▓▒░  ░▒▓██████▓▒░  ",
"░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░        ░▒▓█▓▒░░▒▓█▓▒░       ░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░    ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ",
"░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░       ░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░    ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ",
"░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░  ░▒▓██████▓▒░  ░▒▓█▓▒░░▒▓█▓▒░       ░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░    ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ",
]

def print_banner():
    for line in banner:
        print(PINK + line + RESET)
        time.sleep(0.05)
    print()

# Crawler code
class HackMatrixCrawler:
    def __init__(self, base_url, max_pages=100, max_threads=10):
        self.base_url = base_url
        self.max_pages = max_pages
        self.visited = set()
        self.to_visit = queue.Queue()
        self.to_visit.put(base_url)
        self.lock = threading.Lock()
        self.count = 0
        self.max_threads = max_threads
        self.session = requests.Session()

    def crawl_page(self):
        while True:
            try:
                url = self.to_visit.get(timeout=5)
            except queue.Empty:
                return

            with self.lock:
                if self.count >= self.max_pages:
                    self.to_visit.task_done()
                    return
                if url in self.visited:
                    self.to_visit.task_done()
                    continue
                self.visited.add(url)
                self.count += 1
                print(f"[*] Crawled [{self.count}/{self.max_pages}] - {url}")

            try:
                resp = self.session.get(url, timeout=5)
                if 'text/html' in resp.headers.get('Content-Type', ''):
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        abs_link = urljoin(url, link['href'])
                        if self.is_valid_url(abs_link):
                            with self.lock:
                                if abs_link not in self.visited:
                                    self.to_visit.put(abs_link)
            except Exception:
                pass
            finally:
                self.to_visit.task_done()

    def is_valid_url(self, url):
        parsed = urlparse(url)
        base_domain = urlparse(self.base_url).netloc
        return parsed.scheme in ('http', 'https') and parsed.netloc == base_domain

    def start(self):
        print_banner()
        print(f"[+] Starting HackMatrixCrawler on {self.base_url}\n")

        threads = []
        for _ in range(self.max_threads):
            t = threading.Thread(target=self.crawl_page, daemon=True)
            t.start()
            threads.append(t)

        try:
            while any(t.is_alive() for t in threads):
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[!] Ctrl+C detected! Stopping crawler...")
            with self.lock:
                while not self.to_visit.empty():
                    try:
                        self.to_visit.get_nowait()
                        self.to_visit.task_done()
                    except queue.Empty:
                        break
            sys.exit(0)

if __name__ == "__main__":
    base_url = input("Enter the URL to crawl (e.g. https://example.com): ").strip()
    crawler = HackMatrixCrawler(base_url, max_pages=100, max_threads=10)
    crawler.start()
