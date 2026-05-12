import unittest
import math
from src.search import SearchEngine

class TestSearchEngine(unittest.TestCase):

    def setUp(self):
        # positioned index so phrase adjacency is easy to reason about
        self.index = {
            'hello': {0: [0, 5], 1: [3], 2: [2]},
            'world': {0: [1, 8], 1: [7], 2: [3]},
            'foo':   {0: [9]},
            'quick': {3: [0, 4], 4: [2]},
            'brown': {3: [1, 7], 4: [4]},
            'fox':   {3: [2],    4: [6]},
        }
        self.doc_lengths = {0: 15, 1: 15, 2: 10, 3: 12, 4: 10}
        self.id_to_url = {
            0: 'https://example.com/a',
            1: 'https://example.com/b',
            2: 'https://example.com/c',
            3: 'https://example.com/d',
            4: 'https://example.com/e',
        }
        self.engine = SearchEngine(self.index, self.doc_lengths, self.id_to_url)


    # core phrase matchigng

    def test_connected_excludes_non_adjacent_docs(self):
        """is_connected=True must exclude docs where the terms are present but not adjacent."""
        results = self.engine.find(['hello', 'world'], True, False)
        urls = [url for url, _ in results]
        # doc 1 has both terms but with a gap of 4 — must not appear
        self.assertNotIn('https://example.com/b', urls)
 
    def test_connected_includes_adjacent_docs(self):
        """is_connected=True must include docs where the terms appear consecutively."""
        results = self.engine.find(['hello', 'world'], True, False)
        urls = [url for url, _ in results]
        self.assertIn('https://example.com/a', urls)
        self.assertIn('https://example.com/c', urls)
 
    def test_not_connected_includes_all_intersection_docs(self):
        """is_connected=False returns every doc containing ALL terms, regardless of position."""
        results = self.engine.find(['hello', 'world'], False, False)
        urls = [url for url, _ in results]

        # All three docs have both 'hello' and 'world'
        self.assertIn('https://example.com/a', urls)
        self.assertIn('https://example.com/b', urls)
        self.assertIn('https://example.com/c', urls)
 
    def test_connected_returns_empty_when_no_phrase_match(self):
        """is_connected=True returns [] when terms share docs but are never adjacent."""

        # Build a dedicated engine where 'cat' and 'dog' share a doc but are never adjacent
        engine = SearchEngine(
            {'cat': {0: [0, 5]}, 'dog': {0: [3, 9]}},
            {0: 12},
            {0: 'https://example.com/x'}
        )
        results = engine.find(['cat', 'dog'], True, False)
        self.assertEqual(results, [])

    # single-term query
    def test_single_term_connected_same_as_not_connected(self):
        """For a single-term query the phrase flag has no effect on which docs are returned."""
        connected = self.engine.find(['hello'], True,  False)
        not_connected = self.engine.find(['hello'], False, False)
        self.assertEqual(
            sorted(url for url, _ in connected),
            sorted(url for url, _ in not_connected),
        )

    # three-term consecutive phrase

    def test_three_term_connected_phrase_match(self):
        """Three consecutive terms are matched correctly when all offsets align."""
        results = self.engine.find(['quick', 'brown', 'fox'], True, False)
        urls = [url for url, _ in results]

        # doc 3: quick→0, brown→1, fox→2  — full chain exists
        self.assertIn('https://example.com/d', urls)
 
    def test_three_term_connected_phrase_no_match(self):
        """Three terms present but spread apart do not constitute a phrase."""
        results = self.engine.find(['quick', 'brown', 'fox'], True, False)
        urls = [url for url, _ in results]

        # doc 4: quick=2, brown=4, fox=6 — no consecutive chain of length 3
        self.assertNotIn('https://example.com/e', urls)
 
    def test_three_term_not_connected_includes_all_intersection_docs(self):
        """is_connected=False on a three-term query still returns the full intersection."""

        results = self.engine.find(['quick', 'brown', 'fox'], False, False)
        urls = [url for url, _ in results]
        self.assertIn('https://example.com/d', urls)
        self.assertIn('https://example.com/e', urls)

    # multiple candidate starts
    def test_term_with_multiple_positions_only_needs_one_valid_start(self):
        """A doc qualifies as long as at least one starting position forms a phrase."""
        # doc 0: hello at [0, 5], world at [1, 8]
        # 0 to 1 is valid, but 5 to 8 or another configuration is not
        results = self.engine.find(['hello', 'world'], True, False)
        urls = [url for url, _ in results]
        self.assertIn('https://example.com/a', urls)

    # case insenitivity
    def test_connected_phrase_is_case_insensitive(self):
        """Uppercase query terms are lowercased before phrase matching."""
        lower = self.engine.find(['hello', 'world'], True, False)
        upper = self.engine.find(['HELLO', 'WORLD'], True, False)
        self.assertEqual(
            sorted(url for url, _ in lower),
            sorted(url for url, _ in upper),
        )

    # reversing filters scores correctly
    def test_connected_results_sorted_descending_by_default(self):
        """After phrase filtering, results remain sorted highest score first."""
        results = self.engine.find(['hello', 'world'], True, False)
        scores = [score for _, score in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
 
    def test_connected_results_sorted_ascending_when_requested(self):
        """is_ascending=True returns lowest score first even with phrase filtering."""
        results = self.engine.find(['hello', 'world'], True, True)
        scores = [score for _, score in results]
        self.assertEqual(scores, sorted(scores))

    # ranking

    def test_scores_are_rounded_to_4dp(self):
        """Scores are rounded to 4 decimal places"""
        results = self.engine.find(['foo'])
        for _, score in results:
            self.assertEqual(score, round(score, 4))

    def test_tfidf_score_correct(self):
        """TF-IDF score matches manual calculation"""

        results = self.engine.find(['foo'])
        _, score = results[0]
        tf = 1 / 15  # foo appears once, doc 0 has 15 words
        idf = math.log((1 + 5) / (1 + 1)) + 1  # total_docs=5, docs_with_foo=1
        expected = round(tf * idf, 4)

        self.assertEqual(score, expected)

    # edge cases

    def test_connected_empty_query_returns_empty(self):
        """Empty query with is_connected=True still returns [] without crashing."""
        self.assertEqual(self.engine.find([], True, False), [])
 
    def test_connected_unknown_term_returns_empty(self):
        """Query with an unknown term returns [] regardless of is_connected."""
        self.assertEqual(self.engine.find(['hello', 'zzz'], True, False), [])
 
    def test_connected_phrase_at_position_zero(self):
        """Phrase that starts at position 0 in a doc is detected correctly."""
        engine = SearchEngine(
            {'first': {0: [0]}, 'second': {0: [1]}},
            {0: 5},
            {0: 'https://example.com/start'}
        )
        results = engine.find(['first', 'second'], True, False)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 'https://example.com/start')

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
        self.assertEqual(self.engine.total_docs, 5)

    def test_score_non_negative_for_common_term(self):
        """Terms appearing in all documents should not produce negative scores.
        
        With idf = log(N / (1 + df)), when a term appears in every document,
        N / (1 + df) < 1 and log returns a negative value, corrupting the score.
        The fix is smoothed IDF: log(1 + N / (1 + df)).
        """
        engine = SearchEngine(
            {'common': {0: [0], 1: [0], 2: [0]}},  # term in all 3 docs
            {0: 10, 1: 10, 2: 10},
            {0: 'https://example.com/a',
            1: 'https://example.com/b',
            2: 'https://example.com/c'}
        )
        results = engine.find(['common'])
        self.assertTrue(len(results) > 0)
        for _, score in results:
            self.assertGreaterEqual(score, 0, 
                f"Score {score} is negative, IDF penalising a universally common term")