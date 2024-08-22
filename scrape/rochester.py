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



# Base URL for the product catalog
PRODUCTS_URL = 'https://rochestercp.com/products'
BASE_URL = 'https://rochestercp.com/'
base_url = 'https://rochestercp.com/'

  # Replace with actual catalog URL


def get_product_links(catalog_url):
    chrome_options = Options()
    service = Service('./chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(catalog_url)
    driver.maximize_window()


    # Use WebDriverWait to wait for the page to fully load
    wait = WebDriverWait(driver, 10)
    time.sleep(3)




    html = driver.page_source


    # List to store product links with their associated categories
    product_info = []

    category_divs = driver.find_elements(By.CSS_SELECTOR, '.container-fluid.category-header')

    # Iterate over each .sub-menu element
    for category_div in category_divs:
        actions = ActionChains(driver)
        actions.move_to_element(category_div).perform()

        category_text = category_div.find_element(By.TAG_NAME, 'h1').text.strip()
        closest_container = category_div.find_element(By.XPATH, 'following-sibling::*[@class="container"]')
        product_divs = closest_container.find_elements(By.CSS_SELECTOR, '.item')
        for product_div in product_divs:
            product_link = product_div.find_element(By.TAG_NAME, 'a').get_attribute('href')
            absolute_product_link = urljoin(base_url, product_link)
            product_info.append((product_link, category_text))

    driver.quit()
    return product_info


def get_product_details(product_url, category):

    chrome_options = Options()
    service = Service('./chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(product_url)
    driver.maximize_window()

    # Use WebDriverWait to wait for the page to fully load
    wait = WebDriverWait(driver, 10)


    # Get the initial page source
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    product_details = {}
    ## Category, name, description

    try:
        name=driver.find_element(By.CSS_SELECTOR, 'h1').text.strip()
        name = name.replace('\n', ' ')
        name = ' '.join(name.split())
        product_details['name'] = name
    except Exception as e:
        print('didnt get name')
        product_details['name'] = "Name Coming Soon"
    print(product_details['name'])


    clean_product_name = product_details['name'].replace(' ', '-')

    try:
        product_details['description'] = driver.find_element(By.CSS_SELECTOR, '.lead').text.strip()
    except Exception as e:
        print('didnt get details')
        product_details['description'] = "Description Coming Soon"

    print(category)
    product_details['category'] = category
    print(product_details['category'])


        # List to store image URLs
    ##images
    image_urls = []
    base_url = 'https://rochestercp.com/'
    ##titan does not have the main images tab
    if product_details['name'] == 'Titan Slabs':
        image_url = driver.find_element(By.XPATH, '//img[@title="Titan Profile"]').get_attribute('src')
        absolute_image_url = urljoin(base_url, image_url)
        s3_image_url = upload_image_stream_to_s3(absolute_image_url, s3_bucket_name, f"rochester/{clean_product_name}/images/main.jpg")
        product_details['images'] = [s3_image_url]

    else:
    ##try for image carousel, just grab the one image if not
        try:
            carousel_div = driver.find_element(By.CSS_SELECTOR, '#carousel-example-generic')
            circle_navigators_div = carousel_div.find_element(By.CSS_SELECTOR, '.carousel-indicators')
            circle_navigators = circle_navigators_div.find_elements(By.TAG_NAME, 'li')
            for circle in circle_navigators:
            # Find the image within this vc_item
                circle.click()
                image_div = carousel_div.find_element(By.CSS_SELECTOR, '.item.active')
                image_url = image_div.find_element(By.TAG_NAME, 'img').get_attribute('src')
                absolute_image_url = urljoin(base_url, image_url)
                image_urls.append(absolute_image_url)
        except Exception as e:
            carousel_div = driver.find_element(By.CSS_SELECTOR, '#carousel-example-generic')
            image_url = carousel_div.find_element(By.TAG_NAME, 'img').get_attribute('src')
            absolute_image_url = urljoin(base_url, image_url)
            image_urls.append(absolute_image_url)

        s3_main_images = [upload_image_stream_to_s3(img_url, s3_bucket_name, f"rochester/{clean_product_name}/images/main_{i}.jpg") for i, img_url in enumerate(image_urls)]
        product_details['images'] = s3_main_images



    ## if category is Outdoor Living Kits, most dont have color and size. Just get the pdf and colors
    if product_details['category'] == 'Outdoor Living Kits':
        literature_tab_btn = driver.find_element(By.XPATH, '//a[@aria-controls="literature"]')
        literature_tab_btn.click()
        tab_div = driver.find_element(By.CSS_SELECTOR, '.tab-pane.active')
        images_divs = tab_div.find_elements(By.TAG_NAME, 'img')
        for img in images_divs:
            img_url = img.get_attribute('src')
            if 'dimentions' in img_url:
                parent_element = img.find_element(By.XPATH, 'ancestor::figure[1]')
                pdf_url = parent_element.find_element(By.TAG_NAME, 'a').get_attribute('href')
                absolute_image_url = urljoin(base_url, pdf_url)
                s3_spec_sheet_url = upload_image_stream_to_s3(absolute_image_url, s3_bucket_name, f"rochester/{clean_product_name}/spec_sheet.pdf", 'application/pdf')
                product_details['spec_sheet'] = s3_spec_sheet_url
                break
            else:
                spec_sheet_url = None

        ##colors
        colors = []
        color_tab_btn = driver.find_element(By.XPATH, '//a[@aria-controls="colors"]')
        color_tab_btn.click()
        tab_div = driver.find_element(By.CSS_SELECTOR, '.tab-pane.active')
        rows = tab_div.find_elements(By.CSS_SELECTOR, '.row')
        if len(rows)>1:
            for row in rows:
                colors_divs = row.find_elements(By.TAG_NAME, 'img')
                try:
                    texture=row.find_element(By.XPATH, 'preceding-sibling::h3[1]').text.strip()
                except Exception as e:
                    texture = None
                for color in colors_divs:
                    ## try for when h3 is not following sibling
                    try:
                        name = color.find_element(By.XPATH, 'following-sibling::h2').text.strip()
                    except Exception as e:
                        thumbnail_div = color.find_element(By.XPATH, 'parent::*[@class="thumbnail"]')
                        name = thumbnail_div.find_element(By.XPATH, 'following-sibling::h2').text.strip()
                    image_url = color.get_attribute('src')
                    absolute_image_url = urljoin(base_url, image_url)
                    s3_image_url = upload_image_stream_to_s3(absolute_image_url, s3_bucket_name, f"rochester/{clean_product_name}/colors/{name}_.jpg")

                    color_entry={
                        'name':name,
                        'thumbnail_image_url':s3_image_url,
                        'texture':texture
                    }
                    colors.append(color_entry)
        else:
            colors_divs = tab_div.find_elements(By.TAG_NAME, 'img')
            for color in colors_divs:
                    ## try for when h3 is not following sibling
                    try:
                        name = color.find_element(By.XPATH, 'following-sibling::h2').text.strip()
                    except Exception as e:
                        thumbnail_div = color.find_element(By.XPATH, 'parent::*[@class="thumbnail"]')
                        name = thumbnail_div.find_element(By.XPATH, 'following-sibling::h2').text.strip()
                    image_url = color.get_attribute('src')
                    clean_color_name = name.replace(' ', '-')
                    absolute_image_url = urljoin(base_url, image_url)
                    s3_image_url = upload_image_stream_to_s3(absolute_image_url, s3_bucket_name, f"rochester/{clean_product_name}/colors/{clean_color_name}_.jpg")
                    color_entry={
                        'name':name,
                        'thumbnail_image_url':s3_image_url,
                        'texture':None
                    }
                    colors.append(color_entry)


            product_details['colors'] = colors
            product_details['sizes'] = []
    ##if category is not outdoor living kits
    else:
        ##sizes
        size_entries=[]
        tab_div = driver.find_element(By.CSS_SELECTOR, '.tab-pane.active')
        tables = tab_div.find_elements(By.TAG_NAME, 'table')
        for table in tables:
            rows = table.find_elements(By.XPATH, './/tr')[1:]
            for row in rows:
                tds = row.find_elements(By.CSS_SELECTOR, 'td')
                for i, td in enumerate(tds[:2]):
                    if i==0:
                        name = td.text.strip()
                    else:
                        dimensions = td.text.strip()
                        dimensions = dimensions.replace('\n', ' ').replace('\r', ' ')
                        dimensions = ' '.join(dimensions.split())
                        print(dimensions)
                size_entry = {
                    'name': name,
                    'image': None,
                    'dimensions': [dimensions]
                }
                size_entries.append(size_entry)

        product_details['sizes']=size_entries


        #colors
        colors = []
        color_tab_btn = driver.find_element(By.XPATH, '//a[@aria-controls="colors"]')
        color_tab_btn.click()
        tab_div = driver.find_element(By.CSS_SELECTOR, '.tab-pane.active')
        rows = tab_div.find_elements(By.CSS_SELECTOR, '.row')
        if len(rows)>1:
            for row in rows:
                colors_divs = row.find_elements(By.TAG_NAME, 'img')
                try:
                    texture=row.find_element(By.XPATH, 'preceding-sibling::h3[1]').text.strip()
                except Exception as e:
                    texture = None
                for color in colors_divs:
                    ## try for when h3 is not following sibling
                    try:
                        name = color.find_element(By.XPATH, 'following-sibling::h2').text.strip()
                    except Exception as e:
                        thumbnail_div = color.find_element(By.XPATH, 'parent::*[@class="thumbnail"]')
                        name = thumbnail_div.find_element(By.XPATH, 'following-sibling::h2').text.strip()
                    clean_color_name = name.replace(' ', '-')
                    image_url = color.get_attribute('src')
                    absolute_image_url = urljoin(base_url, image_url)
                    s3_image_url = upload_image_stream_to_s3(absolute_image_url, s3_bucket_name, f"rochester/{product_details['name']}/colors/{clean_color_name}_.jpg")

                    color_entry={
                        'name':name,
                        'thumbnail_image_url':s3_image_url,
                        'texture':texture
                    }
                    colors.append(color_entry)
        else:
            colors_divs = tab_div.find_elements(By.TAG_NAME, 'img')
            for color in colors_divs:
                    ## try for when h3 is not following sibling
                    try:
                        name = color.find_element(By.XPATH, 'following-sibling::h2').text.strip()
                    except Exception as e:
                        thumbnail_div = color.find_element(By.XPATH, 'parent::*[@class="thumbnail"]')
                        name = thumbnail_div.find_element(By.XPATH, 'following-sibling::h2').text.strip()
                    clean_color_name = name.replace(' ', '-')
                    image_url = color.get_attribute('src')
                    absolute_image_url = urljoin(base_url, image_url)
                    s3_image_url = upload_image_stream_to_s3(absolute_image_url, s3_bucket_name, f"rochester/{product_details['name']}/colors/{clean_color_name}_.jpg")
                    color_entry={
                        'name':name,
                        'thumbnail_image_url':s3_image_url,
                        'texture':None
                    }
                    colors.append(color_entry)
        product_details['colors'] = colors



        ##Spec sheet
        literature_tab_btn = driver.find_element(By.XPATH, '//a[@aria-controls="literature"]')
        literature_tab_btn.click()
        tab_div = driver.find_element(By.CSS_SELECTOR, '.tab-pane.active')
        images_divs = tab_div.find_elements(By.TAG_NAME, 'img')
        for img in images_divs:
            img_url = img.get_attribute('src')
            if 'cut-sheet' in img_url and img.get_attribute('title') != 'Super Stik':
                parent_element = img.find_element(By.XPATH, 'ancestor::figure[1]')
                pdf_url = parent_element.find_element(By.TAG_NAME, 'a').get_attribute('href')
                absolute_image_url = urljoin(base_url, pdf_url)
                s3_spec_sheet_url = upload_image_stream_to_s3(absolute_image_url, s3_bucket_name, f"rochester/{clean_product_name}/spec_sheet.pdf", 'application/pdf')
                product_details['spec_sheet'] = s3_spec_sheet_url
                break
            else:
                spec_sheet_url = None




    product_details['textures'] = []





    driver.quit()
    return product_details

def scrape_catalog(products_url = PRODUCTS_URL):

    product_links = get_product_links(products_url)
    all_products = []
    for link, category in product_links:
        product_details = get_product_details(link, category)
        all_products.append(product_details)

    for product in all_products:
        insert_product(product, 'Rochester Concrete Products')

    return all_products

if __name__ == '__main__':
    catalog_url = BASE_URL
    products = scrape_catalog(catalog_url)
    print(products)