from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the base class for declarative models
Base = declarative_base()

class Manufacturer(Base):
    __tablename__ = 'manufacturers'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    products = relationship('Product', back_populates='manufacturer', cascade="all, delete-orphan")

# Define the Product model
class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    manufacturer_id = Column(Integer, ForeignKey('manufacturers.id'), nullable=False)
    manufacturer = relationship('Manufacturer', back_populates='products')
    colors = relationship('Color', back_populates='product', cascade="all, delete-orphan")
    textures = relationship('Texture', back_populates='product', cascade="all, delete-orphan")
    images = relationship('ProductImage', back_populates='product', cascade="all, delete-orphan")

# Define the Color model
class Color(Base):
    __tablename__ = 'colors'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    name = Column(String, nullable=False)
    image_url = Column(String, nullable=False)  # Thumbnail URL
    product = relationship('Product', back_populates='colors')
    color_images = relationship('ColorImage', back_populates='color', cascade="all, delete-orphan")

# Define the Texture model
class Texture(Base):
    __tablename__ = 'textures'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    name = Column(String, nullable=False)
    image_url = Column(String, nullable=False)  # Thumbnail URL
    product = relationship('Product', back_populates='textures')
    texture_images = relationship('TextureImage', back_populates='texture', cascade="all, delete-orphan")

# Define the ProductImage model
class ProductImage(Base):
    __tablename__ = 'product_images'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    image_url = Column(String, nullable=False)
    product = relationship('Product', back_populates='images')

# Define the ColorImage model
class ColorImage(Base):
    __tablename__ = 'color_images'

    id = Column(Integer, primary_key=True)
    color_id = Column(Integer, ForeignKey('colors.id'), nullable=False)
    image_url = Column(String, nullable=False)
    color = relationship('Color', back_populates='color_images')

# Define the TextureImage model
class TextureImage(Base):
    __tablename__ = 'texture_images'

    id = Column(Integer, primary_key=True)
    texture_id = Column(Integer, ForeignKey('textures.id'), nullable=False)
    image_url = Column(String, nullable=False)
    texture = relationship('Texture', back_populates='texture_images')



Index('ix_product_manufacturer_id', Product.manufacturer_id)

# Retrieve the database URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in environment variables")

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Create the tables in the database
Base.metadata.create_all(engine)

# Create a session factory
Session = sessionmaker(bind=engine)