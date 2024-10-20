import sys
import os

# Add the root directory of your project to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from sqlalchemy.orm import sessionmaker
from db.models import Manufacturer, NormalizedCategory, Session  # Adjust the import according to your structure

# Create a new database session
session = Session()

# Data to insert into manufacturers
manufacturers_data = [
    "Techo Bloc",
    "County Materials",
    "Borgert",
    "Rochester Concrete Products".
    "Belgard",
]

# Data to insert into normalized_categories
categories_data = [
    "Pavers & Slabs",
    "Permeable Pavements",
    "Walls",
    "Accessories",
    "Outdoor & Fireplace Kits",
    "Edgers",
    "Caps",
    "Steps"
]

# Insert manufacturers
for name in manufacturers_data:
    manufacturer = Manufacturer(name=name)
    session.add(manufacturer)

# Insert categories
for name in categories_data:
    category = NormalizedCategory(name=name)
    session.add(category)

# Commit the session to save the changes
session.commit()

# Close the session
session.close()

print("Database initialized and data added successfully!")