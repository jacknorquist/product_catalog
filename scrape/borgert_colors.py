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


s3_bucket_name='productscatalog'
def get_colors():

    chrome_options = Options()
    service = Service('./chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get('https://www.borgertproducts.com/color-selection-guide/')

    # Use WebDriverWait to wait for the page to fully load
    wait = WebDriverWait(driver, 10)


    # Get the initial page source
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')



    colors = []

    color_divs = driver.find_elements(By.CSS_SELECTOR, '.item')

    for color in color_divs:
        name_div=colr.find_element(By.CSS_SELECTOR, '.item-title')
        name = name_div.find_element(By.TAG_NAME, 'a').text.strip()
        image_url = color.find_element(By.TAG_NAME, 'img').get_attribute('src')
        product_name = color.find_element(By.TAG_NAME, 'strong').text.strip()
        description = color.find_element(By.CSS_SELECTOR, 'item-meta').text.strip()
        if "Accent Color" in description:
            accent_color = True
        else:
            accent_color = False

        s3_img_url = upload_image_stream_to_s3(image_url, s3_bucket_name, f"borgert/{product_name}/colors/{name}_.jpg")

        color_entry = {
            name = name,
            image_url = s3_image_url,
            product_name = product_name,
            accent_color = accent_color
        }
        colors.append(color_entry)


    driver.quit()

    for color in colors:
        insert_borgert_color(color)
    return