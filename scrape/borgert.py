import requests
from bs4 import BeautifulSoup
from imageuploader import upload_image_stream_to_s3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import urljoin
import time
import sys
import os

# Add the root directory of your project to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from db.insert_product import insert_product

s3_bucket_name='productscatalog'

normalized_category = {
    'Slabs': 'Pavers & Slabs',
    'Pavers': 'Pavers & Slabs',
    'Tumbled Pavers': 'Pavers & Slabs'
    'Permeable Pavements': 'Permeable Pavements',
    'Walls & Step Units': 'Walls',
    'Accents': 'Accessories'.
}



# Base URL for the product catalog
BASE_URL = 'https://www.borgertproducts.com/'  # Replace with actual catalog URL


def get_product_links(catalog_url):
    chrome_options = Options()
    service = Service('./chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(catalog_url)
    driver.maximize_window()


    # Use WebDriverWait to wait for the page to fully load
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.menu-item-type-custom')))
    time.sleep(3)

    products_header = driver.find_element(By.CSS_SELECTOR, '.b-products')
    product_menu = products_header.find_element(By.CSS_SELECTOR, '#menu-products')


    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # List to store product links with their associated categories
    product_info = []

    menu_items = product_menu.find_elements(By.CSS_SELECTOR, '.menu-item-type-custom')

    # Iterate over each .sub-menu element
    for product_item in menu_items:
        actions = ActionChains(driver)
        actions.move_to_element(product_item).perform()
        # Find the sibling <a> element that contains the category
        category_text = product_item.find_element(By.TAG_NAME, 'a').text.strip()
        for link_div in product_item.find_elements(By.CSS_SELECTOR, '.menu-item-type-post_type'):
            product_link = link_div.find_element(By.TAG_NAME, 'a').get_attribute('href')
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
    product_details['name'] = product_details['name'].replace(' (Tumbled)', '').strip()
    product_details['name'] = product_details['name'].replace(' – Untumbled', '').strip()
    product_details['name'] = product_details['name'].replace(' – Curved & Straight Face', '').strip()
    product_details['name'] = product_details['name'].replace(' | Textured & Smooth', '').strip()

    clean_product_name = product_details['name'].replace(' ', '-')

    if product_details['name'] == 'Fireplaces, Ovens & Fire Rings':
        return
    print(product_details['name'])
    content = textWrapper.find_element(By.CSS_SELECTOR, '.content')
    try:
        product_details['description'] = content.find_element(By.TAG_NAME, 'p').text.strip()
    except Exception as e:
        product_details['description'] = "Description Coming Soon"

    product_details['normalized_category_name'] = normalized_category[category]


    if 'Step' in product_details['name']:
        product_details['normalized_category_name'] = 'Steps'

    if 'Cap' in product_details['name']:
        product_details['normalized_category_name'] = 'Caps'
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

    s3_main_images = [upload_image_stream_to_s3(img_url, s3_bucket_name, f"borgert/{clean_product_name}/images/main_{i}.jpg") for i, img_url in enumerate(image_urls)]
    product_details['images'] = s3_main_images


    ##size
    wrapper_divs = driver.find_elements(By.CSS_SELECTOR, '.vc_row.wpb_row.vc_row-fluid')
    # container_div = wrapper_divs[3].find_element(By.CSS_SELECTOR, 'vc_grid-container')
    size_entries=[]
    size_div = wrapper_divs[3].find_element(By.CSS_SELECTOR, '.vc_grid')
    size_items = size_div.find_elements(By.CSS_SELECTOR,'.vc_grid-item')
    for size in size_items:
        h4_text = size.find_element(By.TAG_NAME, 'h4').text.strip()
        lines = h4_text.split('\n')
        name = lines[0]
        clean_size_name = .replace(' ', '-')
        if len(lines)>1:
            dimensions = lines[1]
        else:
            dimensions = ""
        image_url = size.find_element(By.CSS_SELECTOR, '.vc-prettyphoto-link').get_attribute('href')
        s3_size_image_url = upload_image_stream_to_s3(image_url, s3_bucket_name, f"borgert/{clean_product_name}/sizes/{clean_size_name}.png")

        size_entry = {
            'name': name,
            'image': s3_size_image_url,
            'dimensions': dimensions
        }
        size_entries.append(size_entry)

    product_details['sizes']=size_entries


    ##Spec sheet
    s3_spec_sheet_url  = None

    wait = WebDriverWait(driver, 10)
    pdf_links = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")
    s3_spec_sheet_url = upload_image_stream_to_s3(pdf_links[0].get_attribute('href'), s3_bucket_name, f"borgert/{clean_product_name}/spec_sheet.pdf", 'application/pdf')
    print('spect_shee url', s3_spec_sheet_url)



    product_details['spec_sheet']=s3_spec_sheet_url
    product_details['colors'] = []
    product_details['textures'] = []





    driver.quit()
    return product_details

def scrape_catalog(catalog_url = BASE_URL):
    product_links = get_product_links(catalog_url)

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