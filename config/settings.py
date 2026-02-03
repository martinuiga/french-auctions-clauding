import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/eex_auctions"
    )

    EEX_BASE_URL: str = os.getenv(
        "EEX_BASE_URL",
        "https://www.eex.com/en/markets/energy-certificates/french-auctions-power"
    )

    SCRAPE_HOUR: int = int(os.getenv("SCRAPE_HOUR", "8"))
    SCRAPE_MINUTE: int = int(os.getenv("SCRAPE_MINUTE", "0"))

    REQUEST_TIMEOUT: int = 30
    REQUEST_DELAY: float = 1.0


settings = Settings()
