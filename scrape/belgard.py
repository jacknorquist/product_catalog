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
    'fire-features': 'Outdoor & Fireplace Kits',
    'water-features': 'Outdoor & Fireplace Kits',
    'permeable-pavers': 'Permeable Pavements',
    'pavers': 'Pavers & Slabs',
    'outdoor-kitchens-and-fireplaces': '',
    'pergola-panels': 'Accessories',
    'lighting': 'Accessories',
    'outdoor-kitchens': 'Outdoor & Fireplace Kits',
    'outdoor-kitchens-and-fireplaces': 'Outdoor & Fireplace Kits',
    'fire-pit-kits': 'Outdoor & Fireplace Kits',
    'element-accessories': 'Accessories',
    'outdoor-cooking': 'Accessories',
    'bar-sink': 'Accessories',
    'gas-inserts': 'Outdoor & Fireplace Kits',
    'accessories':'Accessories',
    'porcelain-pavers': 'Pavers & Slabs',
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

def get_product_links(driver, page_link):

    driver.get(page_link)
    # Retrieve the current page source
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    product_links = []

    prodcut_container = driver.find_element(By.CSS_SELECTOR, '.grid-component-container')
    product_divs = prodcut_container.find_elements(By.CSS_SELECTOR, '.type--belgard_products')


    for product in product_divs:
        try:
            # Find the closest parent link (anchor tag)
            link = product.find_element(By.XPATH, './a').get_attribute('href')
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
    wait = WebDriverWait(driver, 2)




    # Get the initial page source
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    s3_spec_sheet_url = None
    product_details = {}
    product_details['textures'] = []

    product_wrapper = driver.find_element(By.CSS_SELECTOR, '.product-section-wrap')
    product_name = product_wrapper.find_element(By.CSS_SELECTOR, '.details__title').text.strip()
    product_details['name'] = product_name
    clean_product_name = product_details['name'].replace(' ', '-')

    ##name

    ##category
    product_details['category'] = driver.current_url.split('/')[4]

    product_details['normalized_category_name'] = normalized_category[product_details['category']]

    if 'EDGER' in product_details['name']:
        product_details['normalized_category_name'] = 'Edgers'
    if 'CAPS' in product_details['name']:
        product_details['normalized_category_name'] = 'Caps'
    if 'COPING' in product_details['name']:
        product_details['normalized_category_name'] = 'Caps'
    if 'STEP' in product_details['name']:
        product_details['normalized_category_name'] = 'Steps'






    ##description
    description_text_div = product_wrapper.find_element(By.CSS_SELECTOR, '.details__text')
    description = description_text_div.find_elements(By.TAG_NAME, 'p')[0].text.strip()
    product_details['description'] = description


    ##colors
    colors = []
    # try:
    colors_div = product_wrapper.find_element(By.CSS_SELECTOR, '.details__section.details__section--colors')
    colors = colors_div.find_elements(By.CSS_SELECTOR, '.details__color')

    for color in colors:
        name = color.find_element(By.CSS_SELECTOR, '.details__color__title').text.strip()
        clean_color_name = name.replace(' ', '-')
        thumbnail_image_url = color.find_element(By.TAG_NAME, 'img').get_attribute('src')
        s3_img_url = upload_image_stream_to_s3(thumbnail_image_url, s3_bucket_name, f"belgard/{clean_product_name}/colors/{clean_color_name}_.jpg")

        color_entry ={
            'name': name,
            'thumbnail_image_url':s3_img_url
        }
        colors.append(color_entry)


    product_details['colors'] = colors
    # except:
    #     product_details['colors'] = []



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
                'name': name,
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
    thumbnails = thumbnails_divs.find_elements(By.CSS_SELECTOR, '.gallery__thumbnail')

    for thumbnail in thumbnails:
        driver.execute_script("arguments[0].click();", thumbnail)
        image_div = gallery.find_element(By.CSS_SELECTOR, '.gallery__mainimage.zoom')
        image_url = image_div.find_element(By.TAG_NAME, 'img').get_attribute('src')
        s3_image_url = upload_image_stream_to_s3(image_url, s3_bucket_name, f"belgard/{clean_product_name}/images/{name}_.jpg")
        main_images.append(s3_image_url)

    product_details['images'] = main_images


    try:
        product_tab_div = driver.find_element(By.CSS_SELECTOR, '.product-tabs')
        product_tab = product_tab_div.find_elements(By.CSS_SELECTOR, '.product-tabs__tabs-tab')[1]
        driver.execute_script("arguments[0].click();", product_tab)
        content_2=  product_tab_div.find_element(By.CSS_SELECTOR, '.tab-content-2 ')
        pdf_div = content_div.find_element(By.CSS_SELECTOR, '.tab-content__ti__downloads__download__title')
        pdf_link = pdf_div.find_element(By.TAG_NAME, 'a').get_attribute('href')
        s3_spec_sheet_url = upload_image_stream_to_s3(absolute_image_url, s3_bucket_name, f"rochester/{clean_product_name}/spec_sheet.pdf", 'application/pdf')
        product_details['spec_sheet'] = s3_spec_sheet_url
    except:
        product_details['spec_sheet'] = None







    driver.quit()
    return product_details

def scrape_catalog(catalog_url=BASE_URL):

    links = [
                    'https://www.belgard.com/products/',
                    'https://www.belgard.com/products/?_paged=2',
                    'https://www.belgard.com/products/?_paged=3',
                    'https://www.belgard.com/products/?_paged=4',
                    'https://www.belgard.com/products/?_paged=5',
                    'https://www.belgard.com/products/?_paged=6',
                    'https://www.belgard.com/products/?_paged=7',
                    'https://www.belgard.com/products/?_paged=8',
                    'https://www.belgard.com/products/?_paged=9',
                    'https://www.belgard.com/products/?_paged=10' ]
    # Setup WebDriver
    chrome_options = Options()
    service = Service('./chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)

    product_links = []
    for link in links:
        group =  get_product_links(driver, link)
        product_links.extend(group)


    # Start at the catalog URL
    # driver.get(catalog_url)

    driver.quit()





    all_products = []
    # product_details = get_product_details(product_links[0])
    # insert_product(product_details, 'Techo Bloc')
    for link in product_links:
        product_details = get_product_details(link)
        # all_products.append(product_details)
        insert_product(product_details, 'Belgard')


    return all_products

if __name__ == '__main__':
    catalog_url = BASE_URL
    products = scrape_catalog(catalog_url)
