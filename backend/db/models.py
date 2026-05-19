from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import declarative_base

from db.session import engine

Base = declarative_base()


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(7), nullable=False)
    department = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    budget = Column(Float, nullable=False, default=0.0)
    actual = Column(Float, nullable=False, default=0.0)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
