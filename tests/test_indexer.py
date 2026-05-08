import unittest
import tempfile
import os
import json
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
        uid = self.indexer.url_vocab['https://example.com/a']
        self.assertEqual(len(self.indexer.index['hello'][uid]), 2)
        self.assertEqual(len(self.indexer.index['world'][uid]), 1)

    def test_case_insensitive(self):
        """Indexing is case insensitive"""
        self.indexer.build_index([
            {'url': 'https://example.com/a', 'content': 'Hello HELLO hello'}
        ])
        uid = self.indexer.url_vocab['https://example.com/a']
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
        uid_a = self.indexer.url_vocab['https://example.com/a']
        uid_b = self.indexer.url_vocab['https://example.com/b']
        self.assertIn(uid_a, self.indexer.index['cat'])
        self.assertIn(uid_b, self.indexer.index['cat'])
        self.assertNotIn(uid_b, self.indexer.index['sat'])

    def test_doc_lengths_recorded(self):
        """doc_lengths stores total word count per URL"""
        self.indexer.build_index([
            {'url': 'https://example.com/a', 'content': 'one two three'}
        ])
        uid = self.indexer.url_vocab['https://example.com/a']
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