import requests
from bs4 import BeautifulSoup
import time, re
from urllib import parse, robotparser

class PoliteTimer:
    def __init__(self, delay: float):
        self.delay = delay # seconds
        self.last_request_time = 0
        self.do_print = False

    def wait(self) -> None:
        '''Stalls until the politeness window is over'''
        elapsed = time.time() - self.last_request_time

        if elapsed < self.delay:
            wait_time = self.delay - elapsed

            if (self.do_print):
                print(f"Stalling: {wait_time:.2f} seconds")
            time.sleep(wait_time)

        self.last_request_time = time.time()


class Crawler:
    def __init__(self, base_url: str = "https://quotes.toscrape.com/"):
        self.base_url = base_url
        self.visited = set()
        self.pages_data = []  # stores (url, text_content)
        self.politeness_timer = PoliteTimer(6)
        self.robot_parser = robotparser.RobotFileParser()
        self.base_netloc = parse.urlparse(base_url).netloc
        self.verbosity = 1

    def crawl(self, verbosity_level: int) -> list[dict[str, str]]:
        """
        Starts crawling from the base URL\n
        Verbosity: 0 (silent + errors), 1 (web pages), 2 (stalling)
        """
        self.verbosity = verbosity_level
        self.politeness_timer.do_print = (self.verbosity >= 2)

        self.visited = set()
        self.pages_data = []
        self._parse_robots()

        if self.verbosity > 0:
            print(f"Building index of {self.base_url}")

        try:
            self._visit_page(self.base_url)
        except KeyboardInterrupt:
            print(f"\nCrawl interrupted. {len(self.pages_data)} pages collected.")

        return self.pages_data
    
    def _normalise_url(self, url: str) -> str:
        '''
        Standardise the URL\n
        URL normalisation should be handled differently for different websites, for https://quotes.toscrape.com:\n
        /tag/books/ and /tag/books/page/1/ hold the same content, so they are treated as equivalent
        '''
        parsed = parse.urlparse(url)

        # remove trailing slash (not for the root)
        path = parsed.path.rstrip('/') or '/'

        # treat /page/1/ as the same as the base paginated path
        path = re.sub(r'/page/1/?$', '/', path).rstrip('/') or '/'
    
        # drop empty query strings and fragments
        return parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            path,
            '',   # params
            '',   # query (ignore ?q= style URLs)
            ''    # fragment
        ))

    def _visit_page(self, url: str) -> None:
        url = self._normalise_url(url)
        if url in self.visited or not self.robot_parser.can_fetch("*", url):
            return
        
        self.visited.add(url)
        
        try:
            self.politeness_timer.wait()
            
            if (self.verbosity >= 1):
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

                # handle relative URLs safely
                full_url = parse.urljoin(self.base_url, link)
                full_netloc = parse.urlparse(full_url).netloc
                if self.base_netloc == full_netloc and full_url not in self.visited:
                    self._visit_page(full_url)

        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
            # Don't add to self.pages_data
            # But keep it in self.visited so we don't infinitely retry a broken link
            return

    def _parse_robots(self) -> None:
        robots_url = parse.urljoin(self.base_url, "/robots.txt")

        try:
            self.robot_parser.set_url(robots_url)
            self.robot_parser.read()

            delay = self.robot_parser.crawl_delay("*")
            if delay and delay > 6:
                self.politeness_timer.delay = delay

        except Exception as e:
            print(f"Could not parse robots.txt: {e}")