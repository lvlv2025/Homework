from sqlalchemy.orm import declarative_base
from sqlalchemy import Column
import sqlalchemy
import yaml
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
class Users_info(Base):
    __tablename__ = 'Users_info'
    id = Column(sqlalchemy.Integer, primary_key=True)
    name = Column(sqlalchemy.String(100), nullable=False)
    password = Column(sqlalchemy.String(300), nullable=False)
    email = Column(sqlalchemy.String(100), nullable=False)
    address = Column(sqlalchemy.String(100), nullable=True)