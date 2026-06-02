import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from autorecon_x import RedTeamModule

class WebCrawler(RedTeamModule):
    def __init__(self, target: str):
        super().__init__(target)
        self.description = "Crawl website to find all URLs, endpoints & resources"
        self.visited = set()
        self.max_depth = 3

    def run(self) -> dict:
        print("[🕸️] Starting Web Crawler...")
        start_url = f"http://{self.target}" if not self.target.startswith('http') else self.target
        found_urls = self._crawl(start_url)
        
        return {
            "crawled_urls": list(found_urls),
            "total_found": len(found_urls)
        }

    def _crawl(self, url, depth=0):
        if depth > self.max_depth or url in self.visited:
            return self.visited
        
        try:
            self.visited.add(url)
            res = requests.get(url, timeout=5, headers={"User-Agent": "AutoRecon-X/1.0"})
            soup = BeautifulSoup(res.text, 'html.parser')

            for link in soup.find_all('a', href=True):
                full_url = urljoin(url, link['href'].split('#')[0])
                if self.target in full_url and full_url not in self.visited:
                    self._crawl(full_url, depth+1)

        except Exception as e:
            pass
        return self.visited
      
