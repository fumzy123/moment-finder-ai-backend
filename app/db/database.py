from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# This create_engine function is the core of SQLAlchemy.
# It takes our connection string (postgresql://postgres:password123...) 
# and establishes a pool of active connections to the database server.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True  # This tells SQLAlchemy to constantly verify the connection is still alive before sending a query
)

# A SessionLocal instance is what we actually use to write data (like adding a new Video).
# We set autoflush=False so we have granular control over exactly when data is saved to the database.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    A dependency function we will inject into our FastAPI endpoints.
    It guarantees that every time an endpoint needs to talk to the database, 
    it opens a shiny new session, and when the endpoint finishes, it safely closes the session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
