import json
import re
import os

class Indexer:
    def __init__(self, storage_path: str | None = None):
        self.urls = []
        self.url_to_id = {}
        self.index = {}
        self.doc_lengths = {}

        if storage_path is not None:
            self.storage_path = storage_path
        else:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            self.storage_path  = os.path.join(BASE_DIR, "..", "data", "index.json")

    def _get_url_id(self, url: str) -> int:
        if url not in self.url_to_id:
            uid = len(self.urls) # increments the id
            self.urls.append(url)
            self.url_to_id[url] = uid
        return self.url_to_id[url]

    def build_index(self, pages_data: list[dict[str, str]]) -> None:
        """
        Processes a list of {'url': ..., 'content': ...} and populates the index, saving URLs as integers
        """
        self.urls = []
        self.url_to_id = {}
        self.index = {}
        self.doc_lengths = {}
        
        for page in pages_data:
            url = page['url']
            url_id = self._get_url_id(url)
            words = re.findall(r'\w+', page['content'].lower())

            self.doc_lengths[url_id] = len(words)
            
            # appends position, therefore updating frequency count
            for pos, word in enumerate(words):
                if word not in self.index:
                    self.index[word] = {}
                if url_id not in self.index[word]:
                    self.index[word][url_id] = []
                self.index[word][url_id].append(pos)
        
        self.save()

    def save(self) -> None:
        """Saves the index as a JSON file"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump({
                "urls": self.urls, 
                "index": self.index, 
                "doc_lengths": self.doc_lengths
            }, f, indent=4)
        print(f"Index successfully saved to {self.storage_path}")
    
    def load(self, path: str | None = None) -> bool:
        """Loads the index from the file system"""
        target = path if path is not None else self.storage_path
        if os.path.exists(target):
            with open(target, 'r') as f:
                data = json.load(f)
            
            # reconstruct the vocabulary
            self.urls = data["urls"]
            self.url_to_id = {url: i for i, url in enumerate(self.urls)}
            
            # convert doc_lengths keys back to integers
            self.doc_lengths = {int(uid): length for uid, length in data["doc_lengths"].items()}

            self.index = {}
            for word, postings in data["index"].items():
                self.index[word] = {int(uid): pos_list for uid, pos_list in postings.items()}
                
            return True
        
        print(f"Error: Index file not found at '{target}'. Run 'build' first.")
        return False
    
    def get_word_stats(self, word: str, 
                        ascending: bool = False, top: int | None = None
                        ) -> list[tuple[str, int]] | None:
        """Returns a sorted list of (url, frequency) for a given word."""
        if word not in self.index:
            return None
        
        stats = [
            (self.urls[int(uid)], len(pos)) 
            for uid, pos in self.index[word].items()
        ]
        stats.sort(key=lambda x: x[1], reverse=not ascending)
        return stats[:top]