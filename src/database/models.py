from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Numeric, Text,
    UniqueConstraint
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    auction_date = Column(Date, nullable=False)
    region = Column(String(100), nullable=False)
    technology = Column(String(50), nullable=False)
    volume_offered_mwh = Column(Numeric(15, 2))
    volume_allocated_mwh = Column(Numeric(15, 2))
    weighted_avg_price_eur = Column(Numeric(10, 4))
    created_at = Column(DateTime, default=datetime.utcnow)
    source_file = Column(String(255))

    __table_args__ = (
        UniqueConstraint(
            'auction_date', 'region', 'technology',
            name='uq_auction_date_region_technology'
        ),
    )

    def __repr__(self):
        return (
            f"<Auction(date={self.auction_date}, region={self.region}, "
            f"tech={self.technology}, allocated={self.volume_allocated_mwh} MWh)>"
        )


class ScrapeLog(Base):
    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(20), nullable=False)
    records_added = Column(Integer, default=0)
    error_message = Column(Text)

    def __repr__(self):
        return f"<ScrapeLog(run_at={self.run_at}, status={self.status})>"
