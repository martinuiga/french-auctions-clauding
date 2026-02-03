from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config.settings import settings
from src.database.models import Base


class DatabaseConnection:

    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.DATABASE_URL
        self.engine = create_engine(self.database_url, echo=False)
        self._session: Session = None

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        if self._session is None:
            session_factory = sessionmaker(bind=self.engine)
            self._session = session_factory()
        return self._session

    def connect(self) -> Session:
        self.create_tables()
        return self.get_session()

    def close(self):
        if self._session:
            self._session.close()
            self._session = None
