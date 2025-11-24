from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
        Creates all tables and the associated database view.
        TODO use migration tools to manage schema changes
    """
    # SQLAlchemy will trigger the DDL for the view automatically
    # because of the event listener defined in orm_models.py
    Base.metadata.create_all(engine)
    print("Database schema created (including view).")