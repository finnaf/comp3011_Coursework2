import json
import re
import os

class Indexer:
    def __init__(self, storage_path="../data/index.json"):
        self.index = {}
        self.doc_lengths = {}
        self.storage_path = storage_path

    def build_index(self, pages_data):
        """
        Processes a list of {'url': ..., 'content': ...} and populates the index
        """
        self.index = {}
        self.doc_lengths = {}
        
        for page in pages_data:
            url = page['url']
            # get words (without punctuation)
            words = re.findall(r'\w+', page['content'].lower())
            
            # update frequency count
            for word in words:
                if word not in self.index:
                    self.index[word] = {}

                self.doc_lengths[url] = len(words)

                # set or increment word-url count by one
                self.index[word][url] = self.index[word].get(url, 0) + 1
        
        self.save()

    def save(self):
        """Saves the index as a JSON file"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

        with open(self.storage_path, 'w') as f:
            json.dump({"index": self.index, 
                       "doc_lengths": self.doc_lengths
                    }, f, indent=4)
        print(f"Index successfully saved to {self.storage_path}")

    def load(self):
        """Loads the index from the file system"""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            self.index = data["index"]
            self.doc_lengths = data["doc_lengths"]
            return True
        
        print("Error: Index file not found. Run 'build' first.")
        return False