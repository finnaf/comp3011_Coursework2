import unittest
from unittest.mock import patch, MagicMock
from src.crawler import Crawler
import requests

class TestCrawler(unittest.TestCase):
    '''
    python -m unittest discover tests -b
    '''
    def setUp(self):
        # fake base url
        self.crawler = Crawler("https://example.com/")

        # defaults for all tests
        self.crawler.robot_parser = MagicMock()
        self.crawler.robot_parser.can_fetch.return_value = True # every page allowed
        self.crawler.politeness_timer.wait = MagicMock() # skip stall func

    @patch('src.crawler.requests.get')
    def test_robots_exclusion(self, mock_get):
        """Verify the crawler respects Disallow rules from robots.txt"""

        self.crawler.robot_parser.can_fetch.return_value = False  # everything disallowed

        self.crawler._visit_page("https://example.com/private")

        self.assertNotIn("https://example.com/private", self.crawler.visited)
        self.assertEqual(len(self.crawler.pages_data), 0)
        mock_get.assert_not_called()

    @patch('src.crawler.requests.get')
    def test_link_extraction(self, mock_get):
        """Verify that crawler finds and joins relative links correctly"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<a href="/page1">Next</a>'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        self.crawler._visit_page("https://example.com")
        self.assertIn("https://example.com/page1", self.crawler.visited)

    @patch('src.crawler.requests.get')
    def test_duplicate_prevention(self, mock_get):
        """Verify a URL is only fetched once even if visited multiple times"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<p>No links here</p>'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        self.crawler._visit_page("https://example.com/page1")
        self.crawler._visit_page("https://example.com/page1")
        self.crawler._visit_page("https://example.com/page1")

        mock_get.assert_called_once()
        self.assertEqual(list(self.crawler.visited).count("https://example.com/page1"), 1)
        self.assertEqual(len(self.crawler.pages_data), 1)

    @patch('src.crawler.requests.get')
    def test_domain_boundary(self, mock_get):
        """Verify crawler does not follow links to external domains"""
        page_with_links = MagicMock()
        page_with_links.status_code = 200
        page_with_links.raise_for_status = MagicMock()
        page_with_links.text = '''
            <a href="/internal">Internal</a>
            <a href="https://other.com/page">External</a>
            <a href="https://evil.com/steal">Another External</a>
            <a href="https://example.com.evil.com">Spoofed</a>
        '''

        no_links = MagicMock()
        no_links.status_code = 200
        no_links.raise_for_status = MagicMock()
        no_links.text = '<p>dead end</p>'

        mock_get.side_effect = [page_with_links, no_links]

        self.crawler._visit_page("https://example.com")

        visited = self.crawler.visited
        self.assertIn("https://example.com/", visited)
        self.assertIn("https://example.com/internal", visited)
        self.assertNotIn("https://other.com/page", visited)
        self.assertNotIn("https://evil.com/steal", visited)
        self.assertNotIn("https://example.com.evil.com/", visited)

    @patch('src.crawler.requests.get')
    def test_failed_request_handling(self, mock_get):
        """Verify a failed request stays in visited but not in pages_data"""
        mock_success = MagicMock()
        mock_success.status_code = 200
        mock_success.text = '<a href="/broken">Broken Link</a>'
        mock_success.raise_for_status = MagicMock()

        # / gets sucess, /broken gets the error
        mock_get.side_effect = [
            mock_success,
            requests.exceptions.RequestException("Connection failed")
        ]

        self.crawler._visit_page("https://example.com")

        self.assertIn("https://example.com/", self.crawler.visited)
        self.assertIn("https://example.com/broken", self.crawler.visited)
        self.assertEqual(len(self.crawler.pages_data), 1)
        self.assertEqual(self.crawler.pages_data[0]["url"], "https://example.com/")


    @patch('src.crawler.requests.get')
    def test_pages_data_content(self, mock_get):
        """Verify pages_data stores correct url and extracted text content"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<html><body><h1>Hello</h1><p>Some content</p></body></html>'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        self.crawler._visit_page("https://example.com")

        self.assertEqual(len(self.crawler.pages_data), 1)

        entry = self.crawler.pages_data[0]
        self.assertIn("url", entry)
        self.assertIn("content", entry)
        self.assertEqual(entry["url"], "https://example.com/")
        self.assertIn("Hello", entry["content"])
        self.assertIn("Some", entry["content"])
        self.assertIn("content", entry["content"])

    @patch('src.crawler.requests.get')
    def test_url_normalisation(self, mock_get):
        """Verify that equivalent URLs are not crawled twice"""
        no_links = MagicMock()
        no_links.status_code = 200
        no_links.raise_for_status = MagicMock()
        no_links.text = '<p>no links</p>'
        mock_get.return_value = no_links

        self.crawler._visit_page("https://example.com/tag/books/")
        self.crawler._visit_page("https://example.com/tag/books/page/1/")
        self.crawler._visit_page("https://example.com/tag/books")
        self.crawler._visit_page("https://example.com/tag/books?")

        # all four should be treated as the same page
        mock_get.assert_called_once()
        self.assertEqual(len(self.crawler.pages_data), 1)