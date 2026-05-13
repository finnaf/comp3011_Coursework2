import unittest
import tempfile
import os
from src.indexer import Indexer

class TestIndexer(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        self.tmp.close()
        self.indexer = Indexer(storage_path=self.tmp.name)

    def tearDown(self):
        os.unlink(self.tmp.name)

    # build_index testing

    def test_word_frequency_count(self):
        """Words are counted correctly per URL"""
        self.indexer.build_index([
            {'url': 'https://example.com/a', 'content': 'hello hello world'}
        ])
        uid = self.indexer.url_to_id['https://example.com/a']
        self.assertEqual(len(self.indexer.index['hello'][uid]), 2)
        self.assertEqual(len(self.indexer.index['world'][uid]), 1)

    def test_case_insensitive(self):
        """Indexing is case insensitive"""
        self.indexer.build_index([
            {'url': 'https://example.com/a', 'content': 'Hello HELLO hello'}
        ])
        uid = self.indexer.url_to_id['https://example.com/a']
        self.assertEqual(len(self.indexer.index['hello'][uid]), 3)

    def test_punctuation_stripped(self):
        """Punctuation does not create separate index entries"""
        self.indexer.build_index([
            {'url': 'https://example.com/a', 'content': 'hello, hello. hello!'}
        ])
        self.assertIn('hello', self.indexer.index)
        self.assertNotIn('hello,', self.indexer.index)

    def test_multiple_pages(self):
        """Words spanning multiple pages are indexed under each URL"""
        self.indexer.build_index([
            {'url': 'https://example.com/a', 'content': 'cat sat'},
            {'url': 'https://example.com/b', 'content': 'cat slept'},
        ])
        uid_a = self.indexer.url_to_id['https://example.com/a']
        uid_b = self.indexer.url_to_id['https://example.com/b']
        self.assertIn(uid_a, self.indexer.index['cat'])
        self.assertIn(uid_b, self.indexer.index['cat'])
        self.assertNotIn(uid_b, self.indexer.index['sat'])

    def test_doc_lengths_recorded(self):
        """doc_lengths stores total word count per URL"""
        self.indexer.build_index([
            {'url': 'https://example.com/a', 'content': 'one two three'}
        ])
        uid = self.indexer.url_to_id['https://example.com/a']
        self.assertEqual(self.indexer.doc_lengths[uid], 3)

    def test_build_clears_previous_index(self):
        """Calling build_index twice does not accumulate stale data"""
        self.indexer.build_index([
            {'url': 'https://example.com/a', 'content': 'hello'}
        ])
        self.indexer.build_index([
            {'url': 'https://example.com/b', 'content': 'world'}
        ])
        self.assertNotIn('hello', self.indexer.index)
        self.assertIn('world', self.indexer.index)

    def test_empty_input(self):
        """Empty pages_data produces empty index"""
        self.indexer.build_index([])
        self.assertEqual(self.indexer.index, {})
        self.assertEqual(self.indexer.doc_lengths, {})

    # saving/loading

    def test_save_load_roundtrip(self):
        """Index survives a save/load cycle unchanged"""
        self.indexer.build_index([
            {'url': 'https://example.com/a', 'content': 'hello world'}
        ])
        original_index = dict(self.indexer.index)
        original_lengths = dict(self.indexer.doc_lengths)

        fresh = Indexer(storage_path=self.tmp.name)
        fresh.load()

        self.assertEqual(fresh.index, original_index)
        self.assertEqual(fresh.doc_lengths, original_lengths)

    def test_load_returns_false_if_missing(self):
        """load() returns False and doesn't crash when file doesn't exist"""
        os.unlink(self.tmp.name)
        result = self.indexer.load()
        self.assertFalse(result)
        # recreate so tearDown doesn't fail on unlink
        open(self.tmp.name, 'w').close()


    # get_word_stats testing

    def test_get_word_stats_returns_none_for_unknown_word(self):
        """Returns None when the word has never been indexed"""
        self.indexer.build_index([
            {'url': 'https://example.com/a', 'content': 'hello world'}
        ])
        self.assertIsNone(self.indexer.get_word_stats('banana'))

    def test_get_word_stats_frequency_and_url(self):
        """Returns correct (url, frequency) pairs"""
        self.indexer.build_index([
            {'url': 'https://example.com/a', 'content': 'cat cat cat'},
            {'url': 'https://example.com/b', 'content': 'cat'},
        ])
        stats = self.indexer.get_word_stats('cat')
        url_to_freq = dict(stats)
        self.assertEqual(url_to_freq['https://example.com/a'], 3)
        self.assertEqual(url_to_freq['https://example.com/b'], 1)

    def test_get_word_stats_default_sort_is_descending(self):
        """Default sort puts highest frequency first"""
        self.indexer.build_index([
            {'url': 'https://example.com/a', 'content': 'cat'},
            {'url': 'https://example.com/b', 'content': 'cat cat cat'},
        ])
        stats = self.indexer.get_word_stats('cat')
        self.assertEqual(stats[0], ('https://example.com/b', 3))
        self.assertEqual(stats[1], ('https://example.com/a', 1))

    def test_get_word_stats_ascending(self):
        """ascending=True puts lowest frequency first"""
        self.indexer.build_index([
            {'url': 'https://example.com/a', 'content': 'cat'},
            {'url': 'https://example.com/b', 'content': 'cat cat cat'},
        ])
        stats = self.indexer.get_word_stats('cat', ascending=True)
        self.assertEqual(stats[0], ('https://example.com/a', 1))

    def test_get_word_stats_top_limits_results(self):
        """top=N returns at most N results"""
        self.indexer.build_index([
            {'url': f'https://example.com/{i}', 'content': 'cat ' * (i + 1)}
            for i in range(5)
        ])
        stats = self.indexer.get_word_stats('cat', top=2)
        self.assertEqual(len(stats), 2)

    def test_get_word_stats_single_url(self):
        """Works correctly with only one URL in the index"""
        self.indexer.build_index([
            {'url': 'https://example.com/a', 'content': 'dog dog'}
        ])
        stats = self.indexer.get_word_stats('dog')
        self.assertEqual(stats, [('https://example.com/a', 2)])

    # for full test coverage
    def test_default_storage_path_is_set(self):
        """Indexer sets a default storage path when none is provided"""
        indexer = Indexer()
        self.assertTrue(indexer.storage_path.endswith('index.json'))