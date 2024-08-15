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
                product_link = urljoin(catalog_url, link_element['href'])
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
    base_url = 'https://www.techo-bloc.com'

    product_details = {}
    ## Category, name, description

    textWrapper=driver.find_element(By.CSS_SELECTOR,'.wpb_text_column')
    product_details['name'] = textWrapper.find_element(By.TAG_NAME, 'H1').text.strip()
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



    # Use Selenium to interact with elements
    colors = []
    # color_list = driver.find_element(By.CSS_SELECTOR, '.roc-pdp-selections__colors-list')  # First instance for colors
    color_list = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.roc-pdp-selections__colors-list'))
    )
    color_items = color_list[0].find_elements(By.CSS_SELECTOR, '.roc-pdp-selections__colors-item')

    for color_item in color_items:
        color_name = color_item.find_element(By.CSS_SELECTOR, '.roc-pdp-selections__colors-name').text.strip()
        thumbnail_img = color_item.find_element(By.CSS_SELECTOR, '.roc-pdp-selections__colors-asset').get_attribute('src')
        absolute_thumbnail_img_url = urljoin(base_url, thumbnail_img)

        # Click the color label to show more images
        try:
            color_label = color_item.find_element(By.CSS_SELECTOR, '.roc-pdp-selections__colors-label')
            print('in the try for colors')
            if color_label:
                wait.until(EC.element_to_be_clickable(color_label))
                driver.execute_script("arguments[0].click();", color_label)
                wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.roc-pdp-asset-scroller__item')))
                time.sleep(1)  # Allow time for the images to load

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
                s3_thumbnail_img_url = upload_image_stream_to_s3(absolute_thumbnail_img_url, s3_bucket_name, f"colors/{color_name}_thumbnail.jpg")
                s3_main_images = [upload_image_stream_to_s3(img_url, s3_bucket_name, f"colors/{color_name}_main_{i}.jpg") for i, img_url in enumerate(main_images)]

                colors.append({
                    'name': color_name,
                    'thumbnail_image_url': s3_thumbnail_img_url,
                    'main_images': s3_main_images
                })
            else:
                print(f"Color label for {color_name} not found.")
        except Exception as e:
            print(f"Error processing color {color_name}: {e}")

    textures = []
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
                time.sleep(1)  # Allow time for the images to load

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
                s3_thumbnail_img_url = upload_image_stream_to_s3(absolute_thumbnail_img_url, s3_bucket_name, f"textures/{texture_name}_thumbnail.jpg")
                s3_main_images = [upload_image_stream_to_s3(img_url, s3_bucket_name, f"textures/{texture_name}_main_{i}.jpg") for i, img_url in enumerate(main_images)]

                textures.append({
                    'name': texture_name,
                    'thumbnail_image_url': s3_thumbnail_img_url,
                    'main_images': s3_main_images
                })
            else:
                print(f"Texture label for {texture_name} not found.")
        except Exception as e:
            print(f"Error processing texture {texture_name}: {e}")


    descriptionDiv = driver.find_element(By.CSS_SELECTOR, '.content)
    description = descriptionDiv.find_element(By.TAG_NAME, 'p').text.strip()


    images = []

##dont need main images right now
    # for img in driver.find_elements(By.CSS_SELECTOR, '.roc-pdp-asset-scroller__image'):
    #     img_url = img.get_attribute('src')
    #     absolute_image_url = urljoin(base_url, img_url)
    #     s3_image_url = upload_image_stream_to_s3(absolute_image_url, s3_bucket_name, f"products/{img_url.split('/')[-1]}")
    #     images.append(s3_image_url)

    product_details['colors'] = colors
    product_details['textures'] = textures
    product_details['images'] = images

    driver.quit()
    return product_details

def scrape_catalog(catalog_url = BASE_URL):
    product_links = get_product_links(catalog_url)

    all_products = []
    for link, category in product_links:
        product_details = get_product_details(link, category)
        all_products.append(product_details)

    for product in all_products:
        insert_product(product)

    return all_products

if __name__ == '__main__':
    catalog_url = BASE_URL
    products = scrape_catalog(catalog_url)
    print(products)