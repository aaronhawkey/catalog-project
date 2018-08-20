from sqlalchemy import Column,Integer,String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context


Base = declarative_base()


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(32), unique=True, index=True)



class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    title = Column(String(32))
    description = Column(String)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(32), index=True)
    email = Column(String, index=True)
    password_hash = Column(String(64))


    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    
    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)


engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)