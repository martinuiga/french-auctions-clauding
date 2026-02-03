from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config.settings import settings
from config.logging import logger
from src.scraping import run_scrape


def start_scheduler():
    scheduler = BlockingScheduler()

    scheduler.add_job(
        run_scrape,
        CronTrigger(hour=settings.SCRAPE_HOUR, minute=settings.SCRAPE_MINUTE),
        id="daily_scrape",
        name="Daily EEX Auction Scrape",
        misfire_grace_time=3600,
    )

    scheduler.add_job(
        run_scrape,
        "date",
        id="startup_scrape",
        name="Startup Scrape"
    )

    logger.info("Scheduler started")
    logger.info(f"Scheduled daily scrape at {settings.SCRAPE_HOUR:02d}:{settings.SCRAPE_MINUTE:02d} UTC")
    logger.info("Running initial scrape...")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")
        scheduler.shutdown()


if __name__ == "__main__":
    start_scheduler()
