import math

# type alias
InvertedIndex = dict[str, dict[int, list[int]]]

class SearchEngine:
    def __init__(self, 
        index: InvertedIndex | None = None, 
        doc_lengths: dict[int, int] | None = None, 
        url_vocab: list[str] | None = None
    ):
        self.loaded = False
        if index and doc_lengths and url_vocab:
            self.load(index, doc_lengths, url_vocab)

    def load(self,
            index: InvertedIndex,
            doc_lengths: dict[int, int], 
            url_vocab: list[str]
        ) -> None:
        """
        Loads invertex index
        """
        self.loaded = True
        self.index = index
        self.doc_lengths = doc_lengths # { url: total_word_count }
        self.url_vocab = url_vocab
        self.total_docs = len(doc_lengths)

    def find(self, query_terms: list[str], 
             is_connected: bool = False, is_ascending: bool = False) -> list[tuple[str, float]]:
        """
        Finds pages containing ALL terms in the query (Intersection).
        """
        if not query_terms:
            return []

        # index is lowercase
        query_terms = [term.lower() for term in query_terms]
        for term in query_terms:
            if term not in self.index:
                return []
                
        # intersect urls across all terms
        result_ids = set(self.index[query_terms[0]].keys())
        for term in query_terms[1:]:
            result_ids &= set(self.index[term].keys())

        if is_connected:
            result_ids = self._filter_connected_phrases(query_terms, result_ids)
            
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
        ranked_results.sort(key=lambda x: x[1], reverse=not is_ascending)
        return ranked_results
    
    def _filter_connected_phrases(self, query_terms: list[str], result_ids: set[int]) -> list[int]:
        phrase_match_ids = []
        for url_id in result_ids:
            # start: candidate positions from the first term
            candidate_starts = set(self.index[query_terms[0]][url_id])

            for offset, term in enumerate(query_terms[1:], start=1):
                term_positions = set(self.index[term][url_id])

                # keep only starts where position + offset exists in next term
                candidate_starts = {p for p in candidate_starts if p + offset in term_positions}
                if not candidate_starts:
                    break # skip url if no valid start

            if candidate_starts:
                phrase_match_ids.append(url_id)

        return phrase_match_ids