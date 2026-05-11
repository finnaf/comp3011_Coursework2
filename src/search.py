import math

class SearchEngine:
    def __init__(self, index = None, doc_lengths = None, url_vocab = None):
        self.loaded = False
        if index and doc_lengths and url_vocab:
            self.load(index, doc_lengths, url_vocab)

    def load(self, index: dict, doc_lengths: dict, url_vocab: dict):
        """
        Loads invertex index
        """
        self.loaded = True
        self.index = index
        self.doc_lengths = doc_lengths # { url: total_word_count }
        self.url_vocab = url_vocab
        self.total_docs = len(doc_lengths)

    def find(self, query_terms):
        """
        Finds pages containing ALL terms in the query (Intersection).
        """
        if not query_terms:
            return []

        # index is lowercase
        query_terms = [term.lower() for term in query_terms]
        
        # set of URLs for the first word
        first_word = query_terms[0]
        if first_word not in self.index:
            return []
                
        result_ids = set(self.index[first_word].keys())
        
        # intersect with URL sets of the remaining words
        for term in query_terms[1:]:
            if term in self.index:
                result_ids &= set(self.index[term].keys())
            else:
                return []
            
        # score each url with TF-IDF
        ranked_results = []
        for url_id in result_ids:
            score = 0.0
            for term in query_terms:
                tf = len(self.index[term][url_id]) / self.doc_lengths[url_id]
                docs_with_term = len(self.index[term])

                # variant of idf so result cannot be negative
                idf = math.log((1 + self.total_docs) / (1 + docs_with_term)) + 1
                score += tf * idf
            url = self.url_vocab[url_id]
            ranked_results.append((url, round(score, 4)))

        # highest first
        ranked_results.sort(key=lambda x: x[1], reverse=True)
        return ranked_results