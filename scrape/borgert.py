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
BASE_URL = 'https://www.borgertproducts.com/'  # Replace with actual catalog URL


def get_product_links(catalog_url):
    chrome_options = Options()
    service = Service('./chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(catalog_url)

    # Use WebDriverWait to wait for the page to fully load
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.sub-menu')))

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # List to store product links with their associated categories
    product_info = []

    # Iterate over each .sub-menu element
    for sub_menu in soup.select('.sub-menu'):
        # Find the sibling <a> element that contains the category
        category_element = sub_menu.find_previous_sibling('a')
        if category_element:
            category_text = category_element.get_text(strip=True)
        else:
            category_text = 'Unknown'

        # Iterate over each .menu-item.menu-item-type-post_type within this sub-menu
        for item in sub_menu.select('.menu-item.menu-item-type-post_type'):
            link_element = item.find('a', href=True)
            if link_element:
                product_link = link_element['href']
                if product_link = 'https://www.borgertproducts.com/fireplaces-ovens-fire-rings/':
                    return
                else:
                    product_info.append((product_link, category_text))

    driver.quit()
    return product_info


def get_product_details(product_url, category):

    chrome_options = Options()
    service = Service('./chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(product_url)

    # Use WebDriverWait to wait for the page to fully load
    wait = WebDriverWait(driver, 10)


    # Get the initial page source
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    product_details = {}
    ## Category, name, description

    textWrapper=driver.find_element(By.CSS_SELECTOR,'.wpb_text_column')
    product_details['name'] = textWrapper.find_element(By.TAG_NAME, 'h1').text.strip()
    product_details['description'] = textWrapper.find_element(By.CSS_SELECTOR, '.content').text.strip()
    product_details['category'] = category


        # List to store image URLs
    image_urls = []

    ##images
    vc_items = soup.find_all(class_='vc_item')
    for item in vc_items:
    # Find the image within this vc_item
    img_tag = item.find('img')
    if img_tag and 'src' in img_tag.attrs:
        img_url = img_tag['src']
        # Join the URL with the base URL
        image_urls.append(img_url)

    s3_main_images = [upload_image_stream_to_s3(img_url, s3_bucket_name, f"borgert/{product_details['name']}/images/main_{i}.jpg") for i, img_url in enumerate(image_urls)]
    product_details['images'] = s3_main_images


    ##size
    size_entries=[]
    size_items = driver.find_elements(By.CSS_SELECTOR,'.vc_clearfix')
        for size in size_item:
            h4_text = size.find_element(By.TAG_NAME, 'h4').text.strip()
            lines = h4_text.split('\n')
            name = lines[0]
            dimensions = lines[1]
            image_url = size.find_element(By.CSS_SELECTOR, '.vc_gitem-zone-img').get_attribute('src')
            s3_size_image_url = upload_image_stream_to_s3(img_url, s3_bucket_name, f"borgert/{product_details['name']}/sizes/{name}.png")

            size_entry = {
                'name': name,
                'image': s3_size_img_url,
                'dimensions': dimensions
            }
            size_entries.append(size_entry)

    product_details['sizes']=size_entries


    ##Spec sheet
    s3_spec_sheet_url  = None

    wait = WebDriverWait(driver, 10)
    spec_sheet_url = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[rel="noopener"]'))).get_attribute('href')
    s3_spec_sheet_url = upload_image_stream_to_s3(spec_sheet_url, s3_bucket_name, f"borgert/{product_details['name']}/spec_sheet.pdf", 'application/pdf')

    product_details['spec_sheet']=s3_spec_sheet_url
    product_details['colors'] = []
    product_details['textures'] = []





    driver.quit()
    return product_details

def scrape_catalog(catalog_url = BASE_URL):
    product_links = get_product_links(catalog_url)
    print(product_links)

    all_products = []
    for link, category in product_links:
        product_details = get_product_details(link, category)
        all_products.append(product_details)

    for product in all_products:
        insert_product(product, 'Borgert')

    return all_products

if __name__ == '__main__':
    catalog_url = BASE_URL
    products = scrape_catalog(catalog_url)
    print(products)