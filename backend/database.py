from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = (
    "mysql+pymysql://root:%40BHAVI%408706@localhost/transaction_validator"
)

engine = create_engine(
    DATABASE_URL
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()