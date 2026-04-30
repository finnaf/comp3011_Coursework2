import requests
from bs4 import BeautifulSoup
import time
import urllib.parse

class PoliteTimer:
    def __init__(self, delay):
        self.delay = delay # seconds
        self.last_request_time = 0

    def wait(self):
        '''
        Stalls until the politeness window is over
        '''
        elapsed = time.time() - self.last_request_time

        if elapsed < self.delay:
            wait_time = self.delay - elapsed
            print(f"Stalling: {wait_time:.2f} seconds")
            time.sleep(wait_time)

        self.last_request_time = time.time()


class Crawler:
    def __init__(self, base_url):
        self.base_url = base_url
        self.visited = set()
        self.pages_data = []  # Stores (url, text_content)
        self.politeness_timer = PoliteTimer(6)

    def crawl(self):
        """ Starts crawling from the base URL"""
        self._visit_page(self.base_url)
        return self.pages_data

    def _visit_page(self, url):
        if url in self.visited:
            return
        
        self.visited.add(url)
        
        try:
            self.politeness_timer.wait()
            
            print(f"Crawling: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # extract text data for indexing
            page_text = soup.get_text(separator=' ', strip=True)
            self.pages_data.append({'url': url, 'content': page_text})
            
            # pagination
            for a_tag in soup.find_all('a', href=True):
                link = a_tag['href']

                # handle relative URLs (and stay on base domain)
                full_url = urllib.parse.urljoin(self.base_url, link)
                if self.base_url in full_url and full_url not in self.visited:
                    self._visit_page(full_url)

        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
            # Don't add to self.pages_data
            # But keep it in self.visited so we don't infinitely retry a broken link
            return
                    
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch {url}: {e}")

if __name__ == "__main__":
    crawler = Crawler()
    results = crawler.crawl()
    print(f"Crawl complete. Total pages found: {len(results)}")