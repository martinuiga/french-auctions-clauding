import time
from typing import List, Tuple, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config.settings import settings
from config.logging import logger
from src.database import DatabaseConnection, AuctionRepository, ScrapeLogRepository
from src.scraping.parser import AuctionParser


class EEXScraper:

    def __init__(self):
        self.base_url = settings.EEX_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; EEXAuctionBot/1.0)"
        })

    def fetch_page(self) -> Optional[str]:
        try:
            response = self.session.get(
                self.base_url,
                timeout=settings.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching page: {e}")
            return None

    def find_excel_links(self, html: str) -> List[Tuple[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        excel_links = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            link_text = link.get_text(strip=True)

            if any(ext in href.lower() for ext in [".xlsx", ".xls"]):
                full_url = urljoin(self.base_url, href)
                filename = href.split("/")[-1]
                excel_links.append((full_url, filename))

            elif "download" in link_text.lower() or "result" in link_text.lower():
                if href.endswith((".xlsx", ".xls", ".zip")):
                    full_url = urljoin(self.base_url, href)
                    filename = href.split("/")[-1]
                    excel_links.append((full_url, filename))

        return excel_links

    def download_file(self, url: str) -> Optional[bytes]:
        try:
            time.sleep(settings.REQUEST_DELAY)
            response = self.session.get(url, timeout=settings.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            logger.error(f"Error downloading {url}: {e}")
            return None


def run_scrape():
    logger.info(f"Starting scrape at {time.strftime('%Y-%m-%d %H:%M:%S')}")

    db = DatabaseConnection()
    scraper = EEXScraper()

    try:
        session = db.connect()
        auction_repo = AuctionRepository(session)
        log_repo = ScrapeLogRepository(session)

        processed_files = auction_repo.get_processed_files()

        html = scraper.fetch_page()
        if not html:
            log_repo.log_scrape(status="failure", error_message="Failed to fetch main page")
            return

        excel_links = scraper.find_excel_links(html)
        logger.info(f"Found {len(excel_links)} Excel file links")

        total_records = 0

        for url, filename in excel_links:
            if filename in processed_files:
                logger.debug(f"Skipping already processed: {filename}")
                continue

            logger.info(f"Downloading: {filename}")
            content = scraper.download_file(url)

            if not content:
                continue

            parser = AuctionParser(source_file=filename)
            records = parser.parse_excel(content)
            logger.info(f"Parsed {len(records)} records from {filename}")

            if records:
                inserted = auction_repo.upsert_auctions(records)
                total_records += inserted
                logger.info(f"Inserted {inserted} new records")

        log_repo.log_scrape(status="success", records_added=total_records)
        logger.info(f"Scrape completed. Total new records: {total_records}")

    except Exception as e:
        logger.exception(f"Scrape failed with error: {e}")
        try:
            log_repo.log_scrape(status="failure", error_message=str(e))
        except Exception:
            pass
        raise

    finally:
        db.close()


if __name__ == "__main__":
    run_scrape()
