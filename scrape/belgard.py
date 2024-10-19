import requests
from bs4 import BeautifulSoup
from imageuploader import upload_image_stream_to_s3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin, urlparse
import time
import sys
import os

normalized_category = {
    'retaining-walls': 'Walls',
    'Landscape Tiles': 'Pavers & Slabs',
    'Permeable Pavements': 'Permeable Pavements',
    'Walls': 'Walls',
    'Outdoor Living Kits': 'Outdoor & Fireplace Kits',
    'Accents': 'Accessories',
    'Edgers': 'Edgers',
    'Caps & Tops': 'Caps',
    'Accessories': 'Accessories',
    'Finishing Touches': 'Accessories',
}

# Add the root directory of your project to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from db.insert_product import insert_product

s3_bucket_name='productscatalog'



# Base URL for the product catalog
BASE_URL = 'https://www.belgard.com/products/'  # Replace with actual catalog URL

def get_product_links(driver):
    # Retrieve the current page source
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    product_links = []

    product_divs = driver.find_elements(By.CSS_SELECTOR, '.grid-item-figure')


    for product in product_divs:
        try:
            # Find the closest parent link (anchor tag)
            picture= product.find_element(By.TAG_NAME, 'picture')
            link = picture.find_element(By.TAG_NAME, '').get_attribute('href')
            product_links.append(link)
        except Exception as e:
            print(f"Error finding link for product: {e}")

    return product_links

def get_product_details(product_url):

    chrome_options = Options()
    service = Service('./chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(product_url)

    # Use WebDriverWait to wait for the page to fully load
    wait = WebDriverWait(driver, 10)


    # Get the initial page source
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    s3_spec_sheet_url = None
    product_details = {}
    product_details['textures'] = []

    product_wrapper = driver.find_element(By.CSS_SELECTOR, '.product-section-wrap')
    product_name = product_wrapper.find_element(By.CSS_SELECTOR, 'details__title').text.strip()
    product_details['name'] = product_name
    clean_product_name = product_details['name'].replace(' ', '-')

    ##name

    ##category
    product_details['category'] = driver.current_url.split('/')[5]

    product_details['normalized_category_name'] = normalized_category[product_details['category']]





    ##description
    description_text_div = product_wrapper.find_element(By.CSS_SELECTOR, '.details__text')
    description = description_text_div.find_elements(By.TAG_NAME, 'p')[0].text.strip()
    product_details['description'] = description


    ##colors
    colors = []
    try:
        colors_div = product_wrapper.find_element(By.CSS_SELECTOR, '.details__section details__section--colors')
        colors = colors_div.find_elements(By.CSS_SELECTOR, '.details__color')

        for color in colors:
            name = color.find_element(By.CSS_SELECTOR, '.details__color__title').text.strip()
            clean_color_name = name.replace(' ', '-')
            thumbnail_image_url = color.find_element(By.TAG_NAME, 'img').get_attribute('src')
            s3_img_url = upload_image_stream_to_s3(thumbnail_image_url, s3_bucket_name, f"belgard/{clean_product_name}/colors/{clean_color_name}_.jpg")

            color_entry ={
                'name': name,
                'thumbnail_image_url':s3_image_url
            }
            colors.append(color_entry)


        product_details['colors'] = colors
    except:
        product_details['colors'] = []



    size_entries = []

    try:
        product_tab = driver.find_element(By.CSS_SELECTOR, '.product-tabs')
        spec_div_container= product_tab.find_element(By.CSS_SELECTOR, '.tab-content__specs')
        spec_divs = spec_div_container.find_elements(By.CSS_SELECTOR, '.tab-content__specs__details')

        for size in spec_divs:
            name = size.find_element(By.CSS_SELECTOR, '.tab-content__specs__details__title').text.strip()
            clean_size_name = name.replace(' ', '-')
            img_div = size.find_element(By.CSS_SELECTOR, '.tab-content__specs__details__image')
            img_url; - image_div.find_element(By.TAG_NAME, 'img').get_attribute('src')
            s3_img_url = upload_image_stream_to_s3(thumbnail_image_url, s3_bucket_name, f"belgard/{clean_product_name}/sizes/{clean_size_name}_.jpg")
            size = [size.find_element(By.CSS_SELECTOR, '.tab-content__specs__details__subtitle').text.strip()]

            size_entry = {
                'name' = name,
                'image': image,
                'dimensions': size

            }
            size_entries.append(size_entry)

        product_details['sizes'] = size_entries
    except:
        product_details['sizes'] = size_entries







    main_images=[]

    gallery = product_wrapper.find_element(By.CSS_SELECTOR, '.gallery')
    thumbnails_divs = gallery.find_element(By.CSS_SELECTOR, '.gallery__thumbnails')
    thumbnials = thumbnails_divs.find_elements(By.CSS_SELECTOR, '.gallery__thumbnail')

    for thumnail in thumbnails_divs:
        thumbnail.click()
        driver.sleep(2)
        image_div = gallery.find_element(By.CSS_SELECTOR, '.gallery__mainimage zoom')
        image_url = image_div.find_element(By.TAG_NAME, 'img').get_attribute('src')
        s3_image_url = upload_image_stream_to_s3(image_url, s3_bucket_name, f"belgard/{clean_product_name}/images/{name}_.jpg")
        main_images.append(s3_image_url)

    product_details['images'] = main_images


    try:
        product_tab_div = driver.find_element(By.CSS_SELECTOR, '.product-tabs')
        product_tab = product_tab_div.find_elements(By.CSS_SELECTOR, '.product-tabs__tabs-tab')[1]
        product_tab.click()
        driver.sleep(2)
        content_2= = product_tab_div.find_element(By.CSS_SELECTOR, '.tab-content-2 ')
        pdf_div = content_div.find_element(By.CSS_SELECTOR, '.tab-content__ti__downloads__download__title')
        pdf_link = pdf_div.find_element(By.TAG_NAME, 'a').get_attribute('href')
        s3_spec_sheet_url = upload_image_stream_to_s3(absolute_image_url, s3_bucket_name, f"rochester/{clean_product_name}/spec_sheet.pdf", 'application/pdf')
        product_details['spec_sheet'] = s3_spec_sheet_url
    except:
        product_details['spec_sheet'] = None







    driver.quit()
    return product_details

def scrape_catalog(catalog_url=BASE_URL):

    category_links = ['https://www.belgard.com/products/pavers/', 'https://www.belgard.com/products/permeable-pavers/', 'https://www.belgard.com/products/porcelain-pavers/', 'https://www.belgard.com/products/retaining-walls/', 'https://www.belgard.com/products/accessories/', 'https://www.belgard.com/products/outdoor-kitchens-and-fireplaces/', 'https://www.belgard.com/products/fire-pit-kits/' ]
    # Setup WebDriver
    chrome_options = Options()
    service = Service('./chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)

    # Start at the catalog URL
    driver.get(catalog_url)

    product_links = []
    page_number = 1
    max_pages = 10


    while page_number <= max_pages:
        # Extract product links from the current page
        page_links = get_product_links(driver)
        product_links.extend(page_links)

        # Check for the "Next" button and handle pagination
        try:
            next_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.facetwp-page arrow-next'))  # Adjust selector as needed
            )
            next_button.click()
            time.sleep(2)  # Wait for the page to load and new URL to be set
            page_number += 1
        except Exception as e:
            print(f"No more pages or error: {e}")
            break

    driver.quit()





    all_products = []
    # product_details = get_product_details(product_links[0])
    # insert_product(product_details, 'Techo Bloc')
    for link in product_links:
        product_details = get_product_details(link)
        all_products.append(product_details)

    for product in all_products:
        insert_product(product, 'Techo Bloc')

    return all_products

if __name__ == '__main__':
    catalog_url = BASE_URL
    products = scrape_catalog(catalog_url)
