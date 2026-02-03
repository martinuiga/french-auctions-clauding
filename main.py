#!/usr/bin/env python3
import argparse

from config.logging import logger
from src.scheduler import start_scheduler
from src.scraping import run_scrape


def main():
    parser = argparse.ArgumentParser(description="EEX French Auction Data Scraper")
    parser.add_argument("--once", action="store_true", help="Run scraper once and exit")
    args = parser.parse_args()

    if args.once:
        logger.info("Running single scrape...")
        run_scrape()
    else:
        logger.info("Starting scheduler service...")
        start_scheduler()


if __name__ == "__main__":
    main()