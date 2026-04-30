class SearchEngine:
    def __init__(self, index):
        """
        Initializes with the inverted index dictionary:
        { "word": { "url1": count, "url2": count } }
        """
        self.index = index

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
                
        result_urls = set(self.index[first_word].keys())

        # intersect with URL sets of the remaining words
        for term in query_terms[1:]:
            if term in self.index:
                word_urls = set(self.index[term].keys())
                result_urls = result_urls.intersection(word_urls)
            else:
                # if any word in the query doesn't exist, the intersection is empty
                return []

        # rank results by total frequency
        ranked_results = []
        for url in result_urls:
            total_score = sum(self.index[term][url] for term in query_terms)
            ranked_results.append((url, total_score))

        # highest frequency first
        ranked_results.sort(key=lambda x: x[1], reverse=True)
        
        return ranked_results