from sqlalchemy import Column,Integer,String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context
import datetime


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(32), index=True)
    email = Column(String, index=True)
    password_hash = Column(String(64))
    date_created = Column(DateTime, default=datetime.datetime.now())


    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    
    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)



class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(32), unique=True, index=True)
    date_created = Column(DateTime, default=datetime.datetime.now())
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return{
            'id': self.id,
            'name': self.name,
            'username': self.user.username
        }



class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    title = Column(String(32))
    description = Column(String)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    date_created = Column(DateTime, default=datetime.datetime.now())

    @property
    def serialize(self):
        return{
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category_id': self.category_id,
            'user_id': self.user_id,
            'username': self.user.username
        }



engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)