import sys
import os

# Add the root directory of your project to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from db.models import Session, Product, Color, Texture, ProductImage, Manufacturer, Size




def insert_borgert_color(color):
    # Create a new session
    session = Session()
    # Get the manufacturer
    product = session.query(Product).filter_by(name=color['product_name']).one()

    # Create a new Product instance


    # Add Colors
    color_entry = Color(
        product_id=product.id,
        name=color['name'],
        image_url=color['thumbnail_image_url']
        accent_color = color['accent_color']
    )
    session.add(color_entry)
    session.commit()

          # Commit to get the color ID
        for image_url in color.get('main_images', []):
            image_record = ProductImage(product_id=product.id, color_id=color_entry.id, image_url=image_url)
            session.add(image_record)
        # Add Color Images
        # for color_image_url in color.get('main_images', []):
        #     color_image_entry = ColorImage(
        #         color_id=color_entry.id,
        #         image_url=color_image_url
        #     )
        #     session.add(color_image_entry)
            session.commit()

    # Add Textures
    for texture in product_details['textures']:
        texture_entry = Texture(
            product_id=product.id,
            name=texture['name'],
            image_url=texture['thumbnail_image_url']  # Thumbnail URL
        )
        session.add(texture_entry)
        session.commit()

    for image_url in product_details['images']:
        image_record = ProductImage(product_id=product.id, image_url=image_url)
        session.add(image_record)
        session.commit()


        # Add Texture Images
        # for texture_image_url in texture.get('main_images', []):
        #     texture_image_entry = TextureImage(
        #         texture_id=texture_entry.id,
        #         image_url=texture_image_url
        #     )
        #     session.add(texture_image_entry)

    # Add Product Images
    # for image_url in product_details['images']:
    #     image_entry = ProductImage(
    #         product_id=product.id,
    #         image_url=image_url
    #     )
    #     session.add(image_entry)

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