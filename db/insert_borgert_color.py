import sys
import os

# Add the root directory of your project to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from db.models import Session, Product, Color, Texture, ProductImage, Manufacturer, Size




def insert_borgert_color(colors):
    # Create a new session
    session = Session()
    # Get the manufacturer

    # Create a new Product instance

    # Add Colors
    for color in colors:
        product = session.query(Product).filter_by(name=color['product_name']).one()
        color_entry = Color(
            product_id=product.id,
            name=color['name'],
            image_url=color['thumbnail_image_url'],
            accent_color = color['accent_color']
        )
        session.add(color_entry)
        session.commit()
    # Commit all changes
    session.commit()
    session.close()
