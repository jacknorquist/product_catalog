import sys
import os

# Add the root directory of your project to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from db.models import Session, Product, Color, Texture, ProductImage


def insert_product(product_details):
    # Create a new session
    session = Session()

    # Create a new Product instance
    product = Product(
        name=product_details['name'],
        category=product_details['category']
    )

    # Add the Product to the session
    session.add(product)
    session.commit()  # Commit to get the product ID

    # Add Colors
    for color in product_details['colors']:
        color_entry = Color(
            product_id=product.id,
            name=color['name'],
            image_url=color['image_url']
        )
        session.add(color_entry)

    # Add Textures
    for texture in product_details['textures']:
        texture_entry = Texture(
            product_id=product.id,
            name=texture['name'],
            image_url=texture['image_url']
        )
        session.add(texture_entry)

    # Add Product Images
    for image_url in product_details['images']:
        image_entry = ProductImage(
            product_id=product.id,
            image_url=image_url
        )
        session.add(image_entry)

    # Commit all changes
    session.commit()
    session.close()