from datetime import datetime
from typing import List, Optional

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.database.models import Auction, ScrapeLog


class AuctionRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_all_auctions(self) -> List[Auction]:
        return (
            self.session.query(Auction)
            .order_by(Auction.auction_date.desc(), Auction.region, Auction.technology)
            .all()
        )

    def upsert_auctions(self, auctions: List[dict]) -> int:
        if not auctions:
            return 0

        inserted_count = 0

        for auction_data in auctions:
            if not self._validate_auction(auction_data):
                continue

            stmt = insert(Auction).values(**auction_data)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=['auction_date', 'region', 'technology']
            )
            result = self.session.execute(stmt)
            if result.rowcount > 0:
                inserted_count += 1

        self.session.commit()
        return inserted_count

    def get_processed_files(self) -> set:
        results = self.session.query(Auction.source_file).distinct().all()
        return {r[0] for r in results if r[0]}

    def _validate_auction(self, auction_data: dict) -> bool:
        required_fields = ['auction_date', 'region', 'technology']
        for field in required_fields:
            if field not in auction_data or auction_data[field] is None:
                return False
        return True


class ScrapeLogRepository:

    def __init__(self, session: Session):
        self.session = session

    def log_scrape(
        self,
        status: str,
        records_added: int = 0,
        error_message: Optional[str] = None
    ) -> ScrapeLog:
        if status not in ('success', 'failure'):
            raise ValueError("Status must be 'success' or 'failure'")

        log = ScrapeLog(
            run_at=datetime.utcnow(),
            status=status,
            records_added=records_added,
            error_message=error_message
        )
        self.session.add(log)
        self.session.commit()
        return log
