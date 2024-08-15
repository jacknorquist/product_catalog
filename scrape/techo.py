import requests
from bs4 import BeautifulSoup
from imageuploader import upload_image_stream_to_s3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
import time
import sys
import os

# Add the root directory of your project to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from db.insert_product import insert_product

s3_bucket_name='productscatalog'



# Base URL for the product catalog
BASE_URL = 'https://www.techo-bloc.com/all-products'  # Replace with actual catalog URL

def get_product_links(catalog_url):
    chrome_options = Options()
    service = Service('./chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(catalog_url)
    html = driver.page_source
    # response = requests.get(catalog_url)
    soup = BeautifulSoup(html, 'html.parser');
    product_links = [urljoin(catalog_url, a['href']) for a in soup.select('.techobloc-product-card__link') if 'href' in a.attrs]
    # product_links = [a['href'] for a in soup.select('.techobloc-product-card__link')]
    return product_links

def get_product_details(product_url):

    chrome_options = Options()
    service = Service('./chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(product_url)

    # Use WebDriverWait to wait for the page to fully load
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.roc-pdp-title__product-name')))

    # Get the initial page source
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    base_url = 'https://www.techo-bloc.com'

    product_details = {}
    product_name = soup.select_one('.roc-pdp-title__product-name').text.strip()
    product_details['name'] = product_name
    product_details['category'] = soup.select_one('.roc-pdp-title__product-category-text').text.strip()
    size_entries = []
    colors = []
    textures = []
    main_images=[]







    if product_details['category'] != 'Accessories':
        # Use Selenium to interact with elements
        # color_list = driver.find_element(By.CSS_SELECTOR, '.roc-pdp-selections__colors-list')  # First instance for colors
        color_list = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.roc-pdp-selections__colors-list'))
        )
        color_items = color_list[0].find_elements(By.CSS_SELECTOR, '.roc-pdp-selections__colors-item')

        popup_close = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '.onetrust-close-btn-handler.onetrust-close-btn-ui.banner-close-button.ot-close-icon'))
        )
        popup_close.click();

        for color_item in color_items:
            color_name = color_item.find_element(By.CSS_SELECTOR, '.roc-pdp-selections__colors-name').text.strip()
            thumbnail_img = color_item.find_element(By.CSS_SELECTOR, '.roc-pdp-selections__colors-asset').get_attribute('src')
            absolute_thumbnail_img_url = urljoin(base_url, thumbnail_img)

            # Click the color label to show more images
            try:
                color_label = color_item.find_element(By.CSS_SELECTOR, '.roc-pdp-selections__colors-label')
                if color_label:
                    wait.until(EC.element_to_be_clickable(color_label))
                    driver.execute_script("arguments[0].click();", color_label)
                    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.roc-pdp-asset-scroller__item')))
                    time.sleep(5)  # Allow time for the images to load

                    # Collect main images
                    main_images = []
                    img_items = driver.find_elements(By.CSS_SELECTOR, '.roc-pdp-asset-scroller__button')
                    for img_item in img_items:
                        is_active = 'active' in img_item.get_attribute('class')
                        if not is_active:
                            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(img_item))
                            img_item.click()
                        try:
                            main_image_element = WebDriverWait(driver, 10).until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, '.roc-pdp-main-image__image.roc-lazy-image--loaded'))
                            )
                            img_url = main_image_element.get_attribute('src')
                            main_images.append(urljoin(base_url, img_url))
                        except Exception as e:
                            print(f"Error processing image item: {e}")

                    # Upload thumbnail and main images
                    s3_thumbnail_img_url = upload_image_stream_to_s3(absolute_thumbnail_img_url, s3_bucket_name, f"techo/{product_name}/colors/{color_name}_thumbnail.jpg")
                    s3_main_images = [upload_image_stream_to_s3(img_url, s3_bucket_name, f"techo/{product_name}/colors/{color_name}_main_{i}.jpg") for i, img_url in enumerate(main_images)]

                    colors.append({
                        'name': color_name,
                        'thumbnail_image_url': s3_thumbnail_img_url,
                        'main_images': s3_main_images
                    })
                else:
                    print(f"Color label for {color_name} not found.")
            except Exception as e:
                print(f"Error processing color {color_name}: {e}")


        # texture_list = driver.find_element(By.CSS_SELECTOR, '.roc-pdp-selections__colors-list')  # Second instance for textures
        texture_list = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.roc-pdp-selections__colors-list'))
        )
        texture_items = texture_list[1].find_elements(By.CSS_SELECTOR, '.roc-pdp-selections__colors-item')

        for texture_item in texture_items:
            texture_name = texture_item.find_element(By.CSS_SELECTOR, '.roc-pdp-selections__colors-name').text.strip()
            thumbnail_img = texture_item.find_element(By.CSS_SELECTOR, '.roc-pdp-selections__colors-asset').get_attribute('src')
            absolute_thumbnail_img_url = urljoin(base_url, thumbnail_img)

            # Click the texture label to show more images
            try:
                texture_label = texture_item.find_element(By.CSS_SELECTOR, '.roc-pdp-selections__colors-label')
                if texture_label:
                    wait.until(EC.element_to_be_clickable(texture_label))
                    driver.execute_script("arguments[0].click();", texture_label)
                    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.roc-pdp-asset-scroller__item')))
                    time.sleep(4)  # Allow time for the images to load

                    # Collect main images
                    main_images = []
                    img_items = driver.find_elements(By.CSS_SELECTOR, '.roc-pdp-asset-scroller__button roc-pdp-asset-scroller__button--active')
                    for img_item in img_items:
                        img_item.click()
                        try:
                            main_image_element = WebDriverWait(driver, 10).until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, '.roc-pdp-main-image__image.roc-lazy-image--loaded'))
                            )
                            img_url = main_image_element.get_attribute('src')
                            main_images.append(urljoin(base_url, img_url))
                        except Exception as e:
                            print(f"Error processing image item: {e}")

                    # Upload thumbnail and main images
                    s3_thumbnail_img_url = upload_image_stream_to_s3(absolute_thumbnail_img_url, s3_bucket_name, f"techo/{product_name}/textures/{texture_name}_thumbnail.jpg")
                    s3_main_images = [upload_image_stream_to_s3(img_url, s3_bucket_name, f"techo/{product_name}/textures/{texture_name}_main_{i}.jpg") for i, img_url in enumerate(main_images)]

                    textures.append({
                        'name': texture_name,
                        'thumbnail_image_url': s3_thumbnail_img_url,
                        'main_images': s3_main_images
                    })
                else:
                    print(f"Texture label for {texture_name} not found.")
            except Exception as e:
                print(f"Error processing texture {texture_name}: {e}")

        # Find the container with the sizes list
        sizes_list_container = driver.find_element(By.CLASS_NAME, 'roc-pdp-selections__sizes-list')

        # Find all size items within the container
        size_items = sizes_list_container.find_elements(By.CLASS_NAME, 'roc-pdp-selections__sizes-item')

        # Initialize a list to store the size entries

        # Loop through each size item to extract information
        for size_item in size_items:
            size_img = size_item.find_element(By.CSS_SELECTOR, '.roc-pdp-selections__sizes-asset').get_attribute('src')
            absolute_size_img_url = urljoin(base_url, size_img)

            name = size_item.find_element(By.CSS_SELECTOR,'.roc-pdp-selections__sizes-product').text.strip()
            # Find and extract all DIMENSIONS
            dimension_elements = size_item.find_elements(By.CLASS_NAME, 'roc-pdp-selections__sizes-size')
            if dimension_elements:
                dimensions = [dim.text.strip() for dim in dimension_elements]
            s3_size_img_url = upload_image_stream_to_s3(absolute_size_img_url, s3_bucket_name, f"techo/{product_name}/sizes/{name}.png")

            # Construct the size entry dictionary
            size_entry = {
                'name': name,
                'image': s3_size_img_url,
                'dimensions': dimensions
            }

            # Add the size entry to the list
            size_entries.append(size_entry)

        iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe#hubspot-conversations-iframe'))
        )
        driver.switch_to.frame(iframe)
        assist_close = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '.VizExIconButton__AbstractVizExIconButton-rat7tt-0'))
        )
        assist_close.click();

        driver.switch_to.default_content()

        spec_button = driver.find_element(By.CSS_SELECTOR, '#tab-toggle-65e9a191-5747-4a63-09d6-08dc9f5470cb')
        spec_button.click()

        spec_sheet_url=driver.find_element(By.CSS_SELECTOR, '.roc-pdp-technical-documents__download').get_attribute('href')
        absolute_spec_sheet_url = urljoin(base_url, spec_sheet_url)
        s3_spec_sheet_url = upload_image_stream_to_s3(absolute_spec_sheet_url, s3_bucket_name, f"techo/{product_name}/spec_sheet.pdf", 'application/pdf')


    else:
        images = []
        img_items = driver.find_elements(By.CSS_SELECTOR, '.roc-pdp-asset-scroller__button')
        for img_item in img_items:
            is_active = 'active' in img_item.get_attribute('class')
            if not is_active:
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(img_item))
                img_item.click()
            try:
                main_image_element = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, '.roc-pdp-main-image__image.roc-lazy-image--loaded'))
                )
                img_url = main_image_element.get_attribute('src')
                images.append(urljoin(base_url, img_url))
            except Exception as e:
                print(f"Error processing image item: {e}")

                    # Upload thumbnail and main images
            main_images = [upload_image_stream_to_s3(img_url, s3_bucket_name, f"techo/{product_name}/images/main_{i}.jpg") for i, img_url in enumerate(images)]

    descriptionDiv = driver.find_element(By.CSS_SELECTOR, '#tab-description-description')
    descriptionButton = descriptionDiv.find_element(By.CSS_SELECTOR, '.roc-pdp-sections__accordion-button')
    driver.execute_script("arguments[0].click();", descriptionButton)
    description = descriptionDiv.find_element(By.CSS_SELECTOR, '.roc-pdp-sections__accordion-body').text.strip()
##dont need main images right now
    # for img in driver.find_elements(By.CSS_SELECTOR, '.roc-pdp-asset-scroller__image'):
    #     img_url = img.get_attribute('src')
    #     absolute_image_url = urljoin(base_url, img_url)
    #     s3_image_url = upload_image_stream_to_s3(absolute_image_url, s3_bucket_name, f"products/{img_url.split('/')[-1]}")
    #     images.append(s3_image_url)

    product_details['colors'] = colors
    product_details['textures'] = textures
    product_details['images'] = main_images
    product_details['description'] = description
    product_details['sizes'] = size_entries
    product_details['spec_sheet'] = s3_spec_sheet_url

    driver.quit()
    return product_details

def scrape_catalog(catalog_url = BASE_URL):
    product_links = get_product_links(catalog_url)
    all_products = []
    product_details = get_product_details(product_links[0])
    insert_product(product_details, 'Techo Bloc')
    # for link in product_links:
    #     product_details = get_product_details(link)
    #     all_products.append(product_details)
    return all_products

if __name__ == '__main__':
    catalog_url = BASE_URL
    products = scrape_catalog(catalog_url)
    print(products)