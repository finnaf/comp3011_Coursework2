import unittest
from unittest.mock import patch, MagicMock
from src.crawler import Crawler, PoliteTimer
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
        self.crawler.robot_parser.crawl_delay.return_value = None
        self.crawler.politeness_timer.wait = MagicMock() # skip stall func

    # robots
    @patch('src.crawler.requests.get')
    def test_robots_exclusion(self, mock_get):
        """Verify the crawler respects Disallow rules from robots.txt"""

        self.crawler.robot_parser.can_fetch.return_value = False  # everything disallowed

        self.crawler._visit_page("https://example.com/private")

        self.assertNotIn("https://example.com/private", self.crawler.visited)
        self.assertEqual(len(self.crawler.pages_data), 0)
        mock_get.assert_not_called()

    def test_parse_robots_applies_delay_above_threshold(self):
        """Verify _parse_robots() raises the politeness delay when robots.txt specifies > 6 s"""
        self.crawler.robot_parser.crawl_delay.return_value = 10
 
        self.crawler._parse_robots()
 
        self.assertEqual(self.crawler.politeness_timer.delay, 10)

    def test_parse_robots_keeps_default_delay_when_below_threshold(self):
        """Verify _parse_robots() leaves the delay unchanged when robots.txt value <= 6"""
        self.crawler.robot_parser.crawl_delay.return_value = 3
 
        self.crawler._parse_robots()
 
        self.assertEqual(self.crawler.politeness_timer.delay, 6)

    def test_parse_robots_handles_read_exception_gracefully(self):
        """Verify _parse_robots() logs but does not propagate a robots.txt fetch error"""
        self.crawler.robot_parser.read.side_effect = Exception("Network error")
 
        with patch('builtins.print') as mock_print:
            self.crawler._parse_robots()   # must not raise
 
        mock_print.assert_called_once()
        self.assertIn('robots.txt', mock_print.call_args[0][0])



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

    def _no_links_response(self):
        r = MagicMock()
        r.status_code = 200
        r.text = '<p>no links</p>'
        r.raise_for_status = MagicMock()
        return r
    
    # resetting logic

    @patch('src.crawler.requests.get')
    def test_crawl_resets_state_on_each_call(self, mock_get):
        """Verify crawl() discards stale visited/pages_data from a previous run"""
        mock_get.return_value = self._no_links_response()
 
        # Inject stale state
        self.crawler.visited = {'https://stale.com/'}
        self.crawler.pages_data = [{'url': 'https://stale.com/', 'content': 'old'}]
 
        self.crawler.crawl(0)
 
        self.assertNotIn('https://stale.com/', self.crawler.visited)
        self.assertEqual(len(self.crawler.pages_data), 1)
        self.assertEqual(self.crawler.pages_data[0]['url'], 'https://example.com/')

    
    def test_crawl_handles_keyboard_interrupt_gracefully(self):
        """Verify a KeyboardInterrupt during crawl is caught and partial results returned"""
        self.crawler._visit_page = MagicMock(side_effect=KeyboardInterrupt)
 
        with patch('builtins.print'):
            result = self.crawler.crawl(0)
 
        # Must return a list (even if empty) rather than propagating the exception
        self.assertIsInstance(result, list)

    # verbosity checks

    @patch('src.crawler.requests.get')
    def test_crawl_verbosity_zero_produces_no_output(self, mock_get):
        """Verify verbosity=0 suppresses all print statements"""
        mock_get.return_value = self._no_links_response()
 
        with patch('builtins.print') as mock_print:
            self.crawler.crawl(0)
            mock_print.assert_not_called()
 
    @patch('src.crawler.requests.get')
    def test_crawl_verbosity_one_prints_base_url(self, mock_get):
        """Verify verbosity=1 prints a header line containing the base URL"""
        mock_get.return_value = self._no_links_response()
 
        with patch('builtins.print') as mock_print:
            self.crawler.crawl(1)
 
        all_output = ' '.join(str(c) for c in mock_print.call_args_list)
        self.assertIn('example.com', all_output)
 
    @patch('src.crawler.requests.get')
    def test_crawl_verbosity_two_enables_timer_printing(self, mock_get):
        """Verify verbosity=2 sets do_print on the politeness timer"""
        mock_get.return_value = self._no_links_response()
 
        self.crawler.crawl(2)
 
        self.assertTrue(self.crawler.politeness_timer.do_print)
 
    @patch('src.crawler.requests.get')
    def test_crawl_verbosity_one_disables_timer_printing(self, mock_get):
        """Verify verbosity=1 does not enable timer stall messages"""
        mock_get.return_value = self._no_links_response()
 
        self.crawler.crawl(1)
 
        self.assertFalse(self.crawler.politeness_timer.do_print)



class TestPoliteTimer(unittest.TestCase):
    @patch('src.crawler.time.sleep')
    @patch('src.crawler.time.time')
    def test_wait_sleeps_for_remaining_window(self, mock_time, mock_sleep):
        """Verify wait() sleeps for the time remaining in the delay window"""
        timer = PoliteTimer(6)
        timer.last_request_time = 100.0
        # First call returns current time (2 s elapsed), second records new last_request_time
        mock_time.side_effect = [102.0, 102.0]
 
        timer.wait()
 
        mock_sleep.assert_called_once()
        self.assertAlmostEqual(mock_sleep.call_args[0][0], 4.0, places=5)
 
    @patch('src.crawler.time.sleep')
    @patch('src.crawler.time.time')
    def test_wait_skips_sleep_after_delay_elapsed(self, mock_time, mock_sleep):
        """Verify wait() does not sleep when the full delay has already passed"""
        timer = PoliteTimer(6)
        timer.last_request_time = 100.0
        mock_time.return_value = 110.0  # 10 s elapsed > 6 s delay
 
        timer.wait()
 
        mock_sleep.assert_not_called()
 
    @patch('src.crawler.time.sleep')
    @patch('src.crawler.time.time')
    def test_wait_prints_stall_message_when_verbose(self, mock_time, mock_sleep):
        """Verify wait() prints a stalling notice when do_print is True"""
        timer = PoliteTimer(6)
        timer.do_print = True
        timer.last_request_time = 100.0
        mock_time.side_effect = [102.0, 102.0]
 
        with patch('builtins.print') as mock_print:
            timer.wait()
            mock_print.assert_called_once()
            self.assertIn("Stalling", mock_print.call_args[0][0])
 
    @patch('src.crawler.time.sleep')
    @patch('src.crawler.time.time')
    def test_wait_does_not_print_when_not_verbose(self, mock_time, mock_sleep):
        """Verify wait() stays silent when do_print is False"""
        timer = PoliteTimer(6)
        timer.do_print = False
        timer.last_request_time = 100.0
        mock_time.side_effect = [102.0, 102.0]
 
        with patch('builtins.print') as mock_print:
            timer.wait()
            mock_print.assert_not_called()
