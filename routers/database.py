from sqlmodel import create_engine
import os

database_url = os.getenv("DATABASE_URL", "sqlite:///./ops_center.db")
engine = create_engine(database_url, echo=True)
