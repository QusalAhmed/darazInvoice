import time
import winsound
import requests
import gspread
import random
from gspread.exceptions import APIError
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (NoSuchElementException, TimeoutException, StaleElementReferenceException)
from oauth2client.service_account import ServiceAccountCredentials
from selenium.webdriver.common.keys import Keys

# Variable
triumph = 0
help_image = 'https://static-01.daraz.com.bd/p/e8d488047d7e712047be7e885d00e5b3.png'

# Define the scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# Add the path to the downloaded JSON key file
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
# Authorize the client
client = gspread.authorize(creds)
# Open the Google Sheet
spreadsheet = client.open('Daraz Product')
sheet = spreadsheet.worksheet('Phone Case')
sheet_row = len(sheet.get_all_values()) + 1

service = ChromeService(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--start-maximized')
options.add_argument("--mute-audio")
driver = webdriver.Chrome(options=options, service=service)
wait = WebDriverWait(driver, 20)
mouse = webdriver.ActionChains(driver)

def check_connection():
    while True:
        try:
            if requests.get('https://daraz.com.bd/').status_code == 200:
                break
        except requests.ConnectionError:
            pass
        time.sleep(10)


def send_sheet(color_family, img_link, review_count, title, price, highlight, description, video_url, rgb):
    sheet.batch_update([{
        'range': 'Q{}'.format(sheet_row),
        'values': [[color_family]],
    }, {
        'range': 'S{}'.format(sheet_row),
        'values': [[img_link]],
    }, {
        'range': 'W{}'.format(sheet_row),
        'values': [[f'{product_serial}/{page_number}']],
    }, {
        'range': 'V{}'.format(sheet_row),
        'values': [[review_count]],
    }, {
        'range': 'A{}'.format(sheet_row),
        'values': [[title]],
    }, {
        'range': 'T{}'.format(sheet_row),
        'values': [[price]],
    }, {
        'range': 'L{}'.format(sheet_row),
        'values': [[highlight]],
    }, {
        'range': 'M{}'.format(sheet_row),
        'values': [[description]],
    }, {
        'range': 'O{}'.format(sheet_row),  # Weight
        'values': [['0.1']],
    }, {
        'range': 'P{}'.format(sheet_row),  # Dimension
        'values': [['15.5x11x5']],
    },{
        'range': 'U{}'.format(sheet_row),  # Youtube video url
        'values': [[video_url]],
    }])

    # Format the sku
    sheet.format(f'A{sheet_row}:W{sheet_row}', {
        "backgroundColor": {
            "red": rgb[0],
            "green": rgb[1],
            "blue": rgb[2]
        }
    })

def send_main_image(image_element):
    main_image_cell = 'C'
    for image in image_element:
        if main_image_cell == 'D':
            sheet.update(range_name=main_image_cell + str(sheet_row), values=[[help_image]])
        elif main_image_cell > 'J':
            sheet.update(range_name='N' + str(sheet_row), values=[[image.get_attribute('src')]])
            break
        else:
            sheet.update(range_name=main_image_cell + str(sheet_row), values=[[image.get_attribute('src')]])
        main_image_cell = chr(ord(main_image_cell) + 1)

def scrap_product():
    global sheet_row
    # Scroll to end
    mouse.send_keys(Keys.PAGE_DOWN).perform()
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")

    title = wait.until(ec.presence_of_element_located((By.CLASS_NAME, 'pdp-mod-product-badge-title'))).text
    review_count = wait.until(ec.presence_of_element_located((
        By.CSS_SELECTOR, '.pdp-review-summary a'))).text.replace('Ratings', '').strip()
    # Main images
    image_element = wait.until(ec.presence_of_all_elements_located((
        By.CSS_SELECTOR, '.next-slick-track .next-slick-slide .item-gallery__image-wrapper img')))
    first_image = image_element[0].get_attribute('src')
    video_url = ''
    if 'https://img.lazcdn.com/g/tps/tfs' in first_image:
        image_element.pop(0).click() # click on YouTube thumbnail
        first_image = image_element[1].get_attribute('src')
        # Get video url
        try:
            video_url = wait.until(ec.presence_of_element_located((
                By.CSS_SELECTOR, '.item-gallery__video-player iframe'))).get_attribute('src')
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
            video_url = wait.until(ec.presence_of_element_located((
                By.CSS_SELECTOR, '.item-gallery__video-player video'))).get_attribute('src')
        # Close video dialogue
        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '.item-gallery__video-dialog > a .next-icon'))).click()
    # scroll to highlight element using mouse
    mouse.move_to_element_with_offset(driver.find_element(
        By.CSS_SELECTOR,'#module_product_detail .pdp-mod-section-title.outer-title'), 0, 0).perform()
    time.sleep(1)
    highlight = ''
    try:
        for highlight_line in wait.until(
                ec.presence_of_all_elements_located((By.CSS_SELECTOR, '.pdp-product-highlights li'))):
            highlight += highlight_line.text + '\n'
        # sheet.update(range_name='L{}'.format(sheet_row), values=[[highlight]])
    except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
        print('Error in highlight found')
    # Product description
    mouse.move_to_element(driver.find_element(By.CLASS_NAME, 'html-content.detail-content')).perform()
    try:
        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '.expand-button.expand-cursor button'))).click()
    except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
        pass
    description = ''
    try:
        description = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '.detail-content'))).text
        # sheet.update(range_name='M{}'.format(sheet_row), values=[[description]])
    except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
        print('Error in description found')

    # SKU variation
    rgb = (random.random(), random.random(), random.random())
    sku_elements = wait.until(ec.presence_of_all_elements_located((
        By.CSS_SELECTOR, '.sku-selector .sku-prop:nth-child(1) .sku-prop-content > span')))
    delay = 5 if len(sku_elements) > 5 else 0
    for sku_element in sku_elements:
        price = (wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '.pdp-product-price .pdp-price_type_normal'))).
            text.replace('৳ ', '').strip())
        send_main_image(image_element)

        mouse.move_to_element(
            driver.find_element(By.CLASS_NAME, 'pdp-mod-product-info-section.sku-prop-selection')).perform()
        if not (sku_element.get_attribute('class') == 'sku-variable-img-wrap-selected' or
                sku_element.get_attribute('class') == 'sku-variable-name-selected'):
            sku_element.click()
        variation = wait.until(ec.presence_of_element_located((By.CLASS_NAME, 'sku-prop-content-header'))).text
        try:
            img_link = sku_element.find_element(By.CSS_SELECTOR, '.sku-variable-img img').get_attribute('src')
        except NoSuchElementException:
            img_link = None
        send_sheet(variation, img_link, review_count, title, price, highlight, description, video_url, rgb)
        time.sleep(delay)
        sheet_row += 1
    for extra_variation in ['Multicolor', 'Multi']:
        send_main_image(image_element)
        send_sheet(extra_variation, first_image, review_count, title, '300', highlight, description, video_url, rgb)
        sheet_row += 1

def scrap_handler():
    global sheet_row, triumph
    sku_row_start = sheet_row
    try:
        scrap_product()
        winsound.Beep(2000, 100)
        print('Product scrapped', f'{product_serial}/{page_number}', time.strftime("%H:%M:%S %d-%m-%Y"))
        triumph = 0
    except APIError:
        time.sleep(30)
        sheet_row = sku_row_start
        scrap_handler()
    except Exception as e:
        print(e)
        print('Failed to scrap product', f'{product_serial}/{page_number}')
        for selected_row in range(sku_row_start, sheet_row):
            sheet.update([['' for _ in range(22)]], f'A{selected_row}:V{selected_row}')
        sheet_row = sku_row_start
        winsound.Beep(2000, 1000)
        check_connection()
        if triumph >= 3:
            triumph = 0
            sheet.update([[driver.current_url]], 'X' + str(sheet_row))
            return
        triumph += 1
        scrap_handler()
driver.get('https://www.daraz.com.bd/mobile-cases-covers/?from=sorting_h5&page=19&sort=order')
product_serial = None
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    mouse.move_to_element((driver.find_element(By.CSS_SELECTOR, '.b7FXJ'))).perform()
    try:
        page_number = wait.until(ec.presence_of_element_located((
            By.CSS_SELECTOR, '.ant-pagination-item.ant-pagination-item-active'))).text
    except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
        url = driver.current_url
        page_number = url[url.rfind('=') + 1:]
    if int(page_number) > 102:
        break
    for index, product in enumerate(
            wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, '.Bm3ON .qmXQo .ICdUp a')))):
        product_serial = index + 1
        if product_serial <= 30 and int(page_number) <= 19:
            print(f'Skipping {product_serial}/{page_number}')
            product_serial = index + 1
            continue
        print(f'Scraping {product_serial}/{page_number}', time.strftime("%H:%M:%S %d-%m-%Y"))
        driver.execute_script("window.open('{}')".format(product.get_attribute('href')))
        driver.switch_to.window(driver.window_handles[1])
        driver.execute_script("document.querySelector('#New_LzdSiteNav').remove()")
        scrap_handler()
        # Close the tab
        driver.close()
        # Switch to the main tab
        driver.switch_to.window(driver.window_handles[0])
    driver.get('https://www.daraz.com.bd/mobile-cases-covers/?from=sorting_h5&page={}&sort=order'.format(int(page_number) + 1))
    product_serial = 1
