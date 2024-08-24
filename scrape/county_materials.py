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
from read_svg import upload_svg_as_png_to_s3
import time
import sys
import os

# Add the root directory of your project to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from db.insert_product import insert_product

s3_bucket_name='productscatalog'



# Base URL for the product catalog
BASE_URL = 'https://www.countymaterials.com/'  # Replace with actual catalog URL


def get_product_links(link, category):
    chrome_options = Options()
    service = Service('./chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(link)

    # Use WebDriverWait to wait for the page to fully load
    wait = WebDriverWait(driver, 10)
    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.sub-menu')))

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    products = driver.find_elements(By.CSS_SELECTOR, '.teaser-item')
    product_links = []


    # List to store product links with their associated categories
    for product in products:
        try:
            a_parent = product.find_element(By.CSS_SELECTOR, '.pos-media.media-right')
            a_tag = a_parent.find_element(By.CSS_SELECTOR, 'a')
            href = a_tag.get_attribute('href')
            if href:
                absolute_url = urljoin(BASE_URL, href)
                product_links.append((absolute_url, category))
        except Exception as e:
            print(f"Error extracting product link: {e}")


    driver.quit()
    return product_links


def get_product_details(product_url, category):

    chrome_options = Options()
    service = Service('./chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(product_url)

    # Use WebDriverWait to wait for the page to fully load
    wait = WebDriverWait(driver, 10)

    driver.maximize_window()


    # Get the initial page source
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    base_url = 'https://www.countymaterials.com'

    product_details = {}



    ## Category, name, description

    main_wrapper = driver.find_element(By.CSS_SELECTOR, '#g-container-main')
    main_div = main_wrapper.find_element(By.TAG_NAME, 'main')
    item = main_div.find_element(By.CSS_SELECTOR, '.item')
    textWrapper = item.find_element(By.CSS_SELECTOR, '#product-details')
    product_details['name'] = textWrapper.find_element(By.CSS_SELECTOR, '#details-title').text.strip()
    product_details['description'] = textWrapper.find_element(By.CSS_SELECTOR, '#details-desc').text.strip()
    product_details['category'] = category

    print(product_details['name'])

    ##images
    image_urls = []
    g_divs = textWrapper.find_elements(By.CSS_SELECTOR, '.g-grid')
    right_div = g_divs[2].find_element(By.CSS_SELECTOR, '#details-right')
    img_div = right_div.find_element(By.CSS_SELECTOR, '#details-image')
    img_urls = img_div.find_elements(By.TAG_NAME, 'img')
    for img_url in img_urls:
        image_urls.append(img_url.get_attribute('src'))

    s3_main_images = [upload_image_stream_to_s3(img_url, s3_bucket_name, f"county_materials/{product_details['name']}/images/main_img_{i}.jpg") for i, img_url in enumerate(image_urls)]

    product_details['images'] = s3_main_images


    #colors and textures
    colors = []
    try:
        colors_div = driver.find_element(By.CSS_SELECTOR, '.koowa_media')
        color_elements = colors_div.find_elements(By.CSS_SELECTOR, '.koowa_media__item')
        for color_element in color_elements:
            content_holder = color_element.find_element(By.CSS_SELECTOR, '.koowa_media__item__content-holder')
            label_holder =content_holder.find_element(By.CSS_SELECTOR, '.koowa_header.koowa_media__item__label')
            color_name = label_holder.find_element(By.CSS_SELECTOR, '.overflow_container').text.strip()
            thumbnail_div = content_holder.find_element(By.CSS_SELECTOR, '.koowa_media__item__thumbnail')
            image_url = thumbnail_div.find_element(By.TAG_NAME, 'img').get_attribute('src')
            s3_image_url = upload_image_stream_to_s3(image_url, s3_bucket_name, f"county_materials/{product_details['name']}/colors/{color_name}_thumbnail_img.jpg")
            color_entry = {
                'name':color_name,
                'thumbnail_image_url':s3_image_url,
                'product_name':product_details['name']
            }
            colors.append(color_entry)
    except Exception as e:
        print(e)
        product_details['colors'] = colors

    product_details['colors'] = colors


    ##spec sheet
    # details_lit_div = driver.find_element(By.CSS_SELECTOR, '#details-literature')
    # literature_elements = details_lit_div.find_elements(By.CSS_SELECTOR, '.module_document')
    # spec_sheet_url = literature_elements[0].find_element(By.TAG_NAME, 'a').get_attribute('href')
    # spec_sheet_url += "/file"
    # absolute_spec_sheet_url = urljoin(base_url, spec_sheet_url)
    # s3_spec_sheet_url = upload_image_stream_to_s3(absolute_spec_sheet_url, s3_bucket_name, f"county_materials/{product_details['name']}/spec_sheet.pdf", 'application/pdf')

    product_details['spec_sheet'] = ""

    ##size
    size_entries = []
    left_container = driver.find_element(By.CSS_SELECTOR, '#details-left')
    description = left_container.find_element(By.CSS_SELECTOR, '#details-desc')
    images = description.find_elements(By.TAG_NAME, 'img')
    for img in images:
        img_url = img.get_attribute('src')
        if img_url and ("Sizes" in img_url or "sizes" in img_url):
            size_image_url = img_url
            break

    absolute_size_image_url = urljoin(base_url, size_image_url)

    if '.jpg' in absolute_size_image_url:
        s3_size_image_url = upload_image_stream_to_s3(absolute_size_image_url, s3_bucket_name, f"county_materials/{product_details['name']}/sizes/{product_details['name']}.jpg"),
    else:
        s3_size_image_url = upload_svg_as_png_to_s3(absolute_size_image_url, s3_bucket_name, f"county_materials/{product_details['name']}/sizes/{product_details['name']}.png"),

    size_entry = {
        'name': product_details['name'],
        'image': s3_size_image_url,
        'dimensions': ""
    }
    product_details['sizes'] = size_entries

    ##for safely inserting product
    product_details['textures'] = []



    driver.quit()
    return product_details

def scrape_catalog():

    category_links = [('https://www.countymaterials.com/en/products/landscaping/retaining-walls', 'Walls and '),
                        ('https://www.countymaterials.com/en/products/landscaping/pavers', 'Pavers & Slabs'),
                        ('https://www.countymaterials.com/en/products/landscaping/outdoor-fireplaces-fire-rings-patio-living-products/step-units', 'Steps'),
                        ('https://www.countymaterials.com/en/products/landscaping/outdoor-fireplaces-fire-rings-patio-living-products/fire-pit-kits-circle-square', 'Fire Pits')]
    product_links = []

    for link, category in category_links:
        product_details = get_product_links(link, category)
        product_links += product_details


    all_products = []
    for link, category in product_links:
        product_details = get_product_details(link, category)
        all_products.append(product_details)

    for product in all_products:
        insert_product(product, 'County Materials')

    return all_products

if __name__ == '__main__':
    catalog_url = BASE_URL
    products = scrape_catalog(catalog_url)
    print(products)