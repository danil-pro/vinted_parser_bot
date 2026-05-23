from sqlalchemy import create_engine, Column, BigInteger, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://postgres:babyb00m@localhost:8080/dbname")

factory = sessionmaker(bind=engine)
session = factory()
base = declarative_base()


class User(base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    date = Column(BigInteger, nullable=False)



base.metadata.create_all(engine)
