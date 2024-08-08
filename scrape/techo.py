import requests
from bs4 import BeautifulSoup
from imageuploader import upload_image_stream_to_s3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
s3_bucket_name='productscatalog'



# Base URL for the product catalog
BASE_URL = 'https://www.techo-bloc.com/all-products'  # Replace with actual catalog URL

def get_product_links(catalog_url):
    chrome_options = Options()
    service = Service('scrape/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver = webdriver.Chrome()
    driver.get(catalog_url)
    html = driver.page_source
    # response = requests.get(catalog_url)
    soup = BeautifulSoup(html, 'html.parser');
    print(soup)
    product_links = soup.find_all(class_='techobloc-product-card__link')
    # product_links = [a['href'] for a in soup.select('.techobloc-product-card__link')]
    return product_links

def get_product_details(product_url):
    response = requests.get(product_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    product_details = {}
    product_details['name'] = soup.select_one('.product-page-product-name').text.strip()
    product_details['category'] = soup.select_one('.roc-pdp-title__product-category-text').text.strip()

    colors = []
    color_list = soup.select('.roc-pdp-selections__colors-list')[0]  # First instance for colors
    for color_item in color_list.select('.roc-pdp-selections__colors-item'):
        color_name = color_item.select_one('.roc-pdp-selections__colors-name').text.strip()
        color_image_url = color_item.select_one('.roc-pdp-selections__colors-asset')['href']
        s3_color_image_url = upload_image_stream_to_s3(color_image_url, s3_bucket_name, f"colors/{color_name}.jpg")
        colors.append({'name': color_name, 'image_url': s3_color_image_url})

    textures = []
    texture_list = soup.select('.roc-pdp-selections__colors-list')[1]  # Second instance for textures
    for texture_item in texture_list.select('.roc-pdp-selections__colors-item'):
        texture_name = texture_item.select_one('.roc-pdp-selections__colors-name').text.strip()
        texture_image_url = texture_item.select_one('.roc-pdp-selections__colors-asset')['href']
        s3_texture_image_url = upload_image_stream_to_s3(texture_image_url, s3_bucket_name, f"textures/{texture_name}.jpg")
        textures.append({'name': texture_name, 'image_url': s3_texture_image_url})

    images = []
    for img in soup.select('.roc-pdp-asset-scroller__image'):
        img_url = img['href']
        s3_image_url = upload_image_stream_to_s3(img_url, s3_bucket_name, f"products/{img_url.split('/')[-1]}")
        images.append(s3_image_url)

    product_details['colors'] = colors
    product_details['textures'] = textures
    product_details['images'] = images

    return product_details

def scrape_catalog(catalog_url = BASE_URL):
    product_links = get_product_links(catalog_url)
    all_products = []
    for link in product_links:
        product_details = get_product_details(link)
        all_products.append(product_details)
    return all_products

if __name__ == '__main__':
    catalog_url = BASE_URL
    products = scrape_catalog(catalog_url)
    print(products)