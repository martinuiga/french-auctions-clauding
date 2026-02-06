import pytest
from unittest.mock import patch, MagicMock
from src.scraping.scraper import EEXScraper


class TestEEXScraper:

    def test_find_excel_links_xlsx(self):
        scraper = EEXScraper()
        html = '''
        <html>
            <a href="/files/results_2024.xlsx">Download Results</a>
            <a href="/files/data.pdf">PDF File</a>
        </html>
        '''
        links = scraper.find_excel_links(html)
        assert len(links) == 1
        assert links[0][1] == "results_2024.xlsx"

    def test_find_excel_links_xls(self):
        scraper = EEXScraper()
        html = '''
        <html>
            <a href="/files/old_data.xls">Old Data</a>
        </html>
        '''
        links = scraper.find_excel_links(html)
        assert len(links) == 1
        assert links[0][1] == "old_data.xls"

    def test_find_excel_links_multiple(self):
        scraper = EEXScraper()
        html = '''
        <html>
            <a href="/files/q1.xlsx">Q1</a>
            <a href="/files/q2.xlsx">Q2</a>
            <a href="/files/q3.xls">Q3</a>
        </html>
        '''
        links = scraper.find_excel_links(html)
        assert len(links) == 3

    def test_find_excel_links_empty_html(self):
        scraper = EEXScraper()
        html = '<html><body>No links here</body></html>'
        links = scraper.find_excel_links(html)
        assert len(links) == 0

    def test_find_excel_links_ignores_non_excel(self):
        scraper = EEXScraper()
        html = '''
        <html>
            <a href="/files/doc.pdf">PDF</a>
            <a href="/files/image.png">Image</a>
            <a href="/page.html">Page</a>
        </html>
        '''
        links = scraper.find_excel_links(html)
        assert len(links) == 0

    def test_find_excel_links_full_url(self):
        scraper = EEXScraper()
        html = '<a href="https://example.com/data.xlsx">Data</a>'
        links = scraper.find_excel_links(html)
        assert len(links) == 1
        assert "data.xlsx" in links[0][0]

    def test_find_excel_links_case_insensitive(self):
        scraper = EEXScraper()
        html = '<a href="/files/DATA.XLSX">Data</a>'
        links = scraper.find_excel_links(html)
        assert len(links) == 1

    @patch("src.scraping.scraper.requests.Session.get")
    def test_fetch_page_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html>content</html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        scraper = EEXScraper()
        result = scraper.fetch_page()

        assert result == "<html>content</html>"

    @patch("src.scraping.scraper.requests.Session.get")
    def test_fetch_page_failure(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("Connection error")

        scraper = EEXScraper()
        result = scraper.fetch_page()

        assert result is None

    @patch("src.scraping.scraper.requests.Session.get")
    @patch("src.scraping.scraper.time.sleep")
    def test_download_file_success(self, mock_sleep, mock_get):
        mock_response = MagicMock()
        mock_response.content = b"file content"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        scraper = EEXScraper()
        result = scraper.download_file("https://example.com/file.xlsx")

        assert result == b"file content"
        mock_sleep.assert_called_once()

    @patch("src.scraping.scraper.requests.Session.get")
    @patch("src.scraping.scraper.time.sleep")
    def test_download_file_failure(self, mock_sleep, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("Download failed")

        scraper = EEXScraper()
        result = scraper.download_file("https://example.com/file.xlsx")

        assert result is None