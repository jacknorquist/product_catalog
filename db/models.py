from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    category = Column(String)
    colors = relationship('Color', back_populates='product')
    textures = relationship('Texture', back_populates='product')
    images = relationship('ProductImage', back_populates='product')

class Color(Base):
    __tablename__ = 'colors'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    name = Column(String)
    image_url = Column(String)
    product = relationship('Product', back_populates='colors')

class Texture(Base):
    __tablename__ = 'textures'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    name = Column(String)
    image_url = Column(String)
    product = relationship('Product', back_populates='textures')

class ProductImage(Base):
    __tablename__ = 'product_images'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    image_url = Column(String)
    product = relationship('Product', back_populates='images')


DATABASE_URL=os.getenv('DATABASE_URL')


# Create the engine
engine = create_engine(DATABASE_URL, echo=True)

# Create tables
Base.metadata.create_all(engine)

# Create a session factory
Session = sessionmaker(bind=engine)