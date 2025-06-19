# app/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import DATABASE_URL  # import from config

# DATABASE_URL = os.getenv("DATABASE_URL")
# DATABASE_URL = "postgresql://postgres:postgresql@localhost/your_dbname"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()




#? start(this is not for production, only for dev/local)
from sqlalchemy_utils import database_exists, create_database

# Check and create DB if needed (only do this in dev/local)
if not database_exists(engine.url):
    create_database(engine.url)
    print("Database created successfully.")
else:
    print("Database already exists.")
    
#? end

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
