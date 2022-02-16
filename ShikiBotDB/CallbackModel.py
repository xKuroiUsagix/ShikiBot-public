from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


BaseModel = declarative_base()


class Callback(BaseModel):
    __tablename__ = 'callbacks'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    title_name = Column(String(100))
    title_score = Column(Float)
    title_synopsis = Column(Text(1000))
    title_genres = Column(Text(250))
    message_datetime = Column(DateTime)

    def __init__(self, chat_id, title_name, title_score, title_synopsis, title_genres):
        self.chat_id = chat_id
        self.title_name = title_name
        self.title_score = title_score
        self.title_synopsis = title_synopsis
        self.title_genres = title_genres
        self.message_datetime = datetime.now()

    def __str__(self):
        return f'{self.chat_id}: {self.title_name}'


ENGINE = create_engine('sqlite:///callbacks')
BaseModel.metadata.create_all(bind=ENGINE)
