from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.session import engine

def init_db(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But for initial development/testing, we can use create_all
    Base.metadata.create_all(bind=engine)
