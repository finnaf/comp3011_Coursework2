import unittest
import math
from src.search import SearchEngine

class TestSearchEngine(unittest.TestCase):

    def setUp(self):
        # Index uses integer URL IDs as keys, with lists of positions (len = frequency)
        self.index = {
            'foo': {
                0: [0, 1, 2],   # 3 occurrences in doc 0
                1: [0],          # 1 occurrence in doc 1
            },
            'bar': {
                0: [3, 4],       # 2 occurrences in doc 0
                2: [0],          # 1 occurrence in doc 2
            },
            'python': {
                1: [1, 2, 3, 4, 5],  # 5 occurrences in doc 1
            }
        }
        self.doc_lengths = {
            0: 10,
            1: 20,
            2: 5,
        }
        self.id_to_url = {
            0: 'https://example.com/a',
            1: 'https://example.com/b',
            2: 'https://example.com/c',
        }
        self.engine = SearchEngine(self.index, self.doc_lengths, self.id_to_url)

    # --- find: basic behaviour ---

    def test_single_term_returns_matching_urls(self):
        """Single term query returns all pages containing that word"""
        results = self.engine.find(['foo'])
        urls = [url for url, _ in results]
        self.assertIn('https://example.com/a', urls)
        self.assertIn('https://example.com/b', urls)
        self.assertNotIn('https://example.com/c', urls)

    def test_multi_term_intersection(self):
        """Multi-term query only returns pages containing ALL terms"""
        results = self.engine.find(['foo', 'bar'])
        urls = [url for url, _ in results]
        # only /a has both foo and bar
        self.assertEqual(urls, ['https://example.com/a'])

    def test_no_results_if_term_missing(self):
        """Query with a term not in the index returns empty list"""
        results = self.engine.find(['nonexistent'])
        self.assertEqual(results, [])

    def test_no_results_if_intersection_empty(self):
        """Query where no single page contains all terms returns empty list"""
        # 'bar' is in /a and /c, 'python' is only in /b — no overlap
        results = self.engine.find(['bar', 'python'])
        self.assertEqual(results, [])

    def test_empty_query_returns_empty(self):
        """Empty query returns empty list without crashing"""
        self.assertEqual(self.engine.find([]), [])

    def test_case_insensitive_query(self):
        """Query terms are lowercased before lookup"""
        lower = self.engine.find(['foo'])
        upper = self.engine.find(['FOO'])
        self.assertEqual(lower, upper)

    # --- find: ranking ---

    def test_results_sorted_by_score_descending(self):
        """Results are returned highest score first"""
        results = self.engine.find(['foo'])
        scores = [score for _, score in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_higher_frequency_scores_higher(self):
        """Page with more occurrences of a term ranks above one with fewer"""
        # /a has foo 3 times in 10 words (tf=0.3)
        # /b has foo 1 time in 20 words (tf=0.05)
        results = self.engine.find(['foo'])
        urls = [url for url, _ in results]
        self.assertEqual(urls[0], 'https://example.com/a')

    def test_scores_are_rounded_to_4dp(self):
        """Scores are rounded to 4 decimal places"""
        results = self.engine.find(['foo'])
        for _, score in results:
            self.assertEqual(score, round(score, 4))

    def test_tfidf_score_correct(self):
        """TF-IDF score matches manual calculation"""
        results = self.engine.find(['python'])
        self.assertEqual(len(results), 1)

        _, score = results[0]
        tf = 5 / 20                              # count / doc_length
        idf = math.log(3 / (1 + 1))             # total_docs / (1 + docs_with_term)
        expected = round(tf * idf, 4)
        self.assertEqual(score, expected)

    # find edge cases
    def test_single_document_index(self):
        """Works correctly when index contains only one document"""
        engine = SearchEngine(
            {'word': {0: [0]}},
            {0: 5},
            {0: 'https://example.com/only'}
        )
        results = engine.find(['word'])
        self.assertEqual(len(results), 1)

    def test_total_docs_is_correct(self):
        """total_docs reflects number of documents in doc_lengths"""
        self.assertEqual(self.engine.total_docs, 3)