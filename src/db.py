import os
from sqlalchemy import create_engine, Column, BigInteger, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

db_path = os.path.join(os.path.dirname(__file__), 'bot.db')
engine = create_engine(f"sqlite:///{db_path}")

factory = sessionmaker(bind=engine)
session = factory()
base = declarative_base()


class User(base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    date = Column(BigInteger, nullable=False)


base.metadata.create_all(engine)
