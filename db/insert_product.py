import sys
import os

# Add the root directory of your project to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from db.models import Session, Product, Color, Texture, ProductImage, ColorImage, TextureImage, Manufacturer, Size




def insert_product(product_details, manufacturer_name):
    # Create a new session
    session = Session()
    # Get the manufacturer
    manufacturer = session.query(Manufacturer).filter_by(name=manufacturer_name).one()

    # Create a new Product instance
    product = Product(
        name=product_details['name'],
        category=product_details['category'],
        description = product_details['description'],
        manufacturer = manufacturer,
        spec_sheet = product_details['spec_sheet']
    )

    # Add the Product to the session
    session.add(product)
    session.commit()  # Commit to get the product ID

    # Add Colors
    for color in product_details['colors']:
        color_entry = Color(
            product_id=product.id,
            name=color['name'],
            image_url=color['thumbnail_image_url']
        )
        session.add(color_entry)
        session.commit()  # Commit to get the color ID

        # Add Color Images
        for color_image_url in color.get('main_images', []):
            color_image_entry = ColorImage(
                color_id=color_entry.id,
                image_url=color_image_url
            )
            session.add(color_image_entry)

    # Add Textures
    for texture in product_details['textures']:
        texture_entry = Texture(
            product_id=product.id,
            name=texture['name'],
            image_url=texture['thumbnail_image_url']  # Thumbnail URL
        )
        session.add(texture_entry)
        session.commit()  # Commit to get the texture ID

        # Add Texture Images
        for texture_image_url in texture.get('main_images', []):
            texture_image_entry = TextureImage(
                texture_id=texture_entry.id,
                image_url=texture_image_url
            )
            session.add(texture_image_entry)

    # Add Product Images
    for image_url in product_details['images']:
        image_entry = ProductImage(
            product_id=product.id,
            image_url=image_url
        )
        session.add(image_entry)

    for size in product_details['sizes']:
        size_entry = Size(
            product_id=product.id,
            name=size['name'],
            image_url=size['image'],
            dimensions=size['dimensions']
        )
        session.add(size_entry)



    # Commit all changes
    session.commit()
    session.close()