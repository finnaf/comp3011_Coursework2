import json
import re
import os

class Indexer:
    def __init__(self, storage_path="../data/index.json"):
        self.url_vocab = {} # maps url to integer ids
        self.id_to_url = {}
        self.index = {}
        self.doc_lengths = {}
        self.storage_path = storage_path

    def get_url(self, url_id):
        """Helper to look up a URL by its integer ID."""
        return self.id_to_url.get(url_id)

    def _get_url_id(self, url):
        """Returns existing ID for a URL, or assigns a new one."""
        if url not in self.url_vocab:
            uid = len(self.url_vocab)
            self.url_vocab[url] = uid
            self.id_to_url[uid] = url
        return self.url_vocab[url]

    def build_index(self, pages_data):
        """
        Processes a list of {'url': ..., 'content': ...} and populates the index, saving URLs as integers
        """
        self.url_vocab = {}
        self.id_to_url = {}
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

    def save(self):
        """Saves the index as a JSON file"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        id_to_url = {str(uid): url for url, uid in self.url_vocab.items()}
        with open(self.storage_path, 'w') as f:
            json.dump({
                "url_vocab": id_to_url,
                "index": self.index,
                "doc_lengths": self.doc_lengths
            }, f, indent=4)
        print(f"Index successfully saved to {self.storage_path}")
    
    def load(self):
        """Loads the index from the file system"""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # reconstruct the vocabulary with integers
            self.url_vocab = {url: int(uid) for uid, url in data["url_vocab"].items()}
            self.id_to_url = {int(uid): url for uid, url in data["url_vocab"].items()}
            
            # convert doc_lengths keys back to integers
            self.doc_lengths = {int(uid): length for uid, length in data["doc_lengths"].items()}
            
            self.index = {}
            for word, postings in data["index"].items():
                self.index[word] = {int(uid): pos_list for uid, pos_list in postings.items()}
                
            return True
        
        print("Error: Index file not found. Run 'build' first.")
        return False