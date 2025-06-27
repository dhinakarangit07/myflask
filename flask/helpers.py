import time
import re
import requests
from selenium.webdriver.common.by import By
from webdriver import *

def read_captcha(driver):
    time.sleep(2)  # Ensure page is loaded
    
    captcha_element = driver.find_element(By.ID, "captcha_image")
    
    # Get the CAPTCHA image as PNG bytes
    image_bytes = captcha_element.screenshot_as_png
    
    # Send the image bytes directly to OCR.Space API
    response = requests.post(
        'https://api.ocr.space/parse/image',
        files={'filename': ('captcha.png', image_bytes, 'image/png')},
        data={'apikey': 'K83085402488957', 'OCREngine': '2'}
    )

    result = response.json()
    try:
        raw_text = result['ParsedResults'][0]['ParsedText'].strip()
        filtered_text = re.sub(r'[^a-z0-9]', '', raw_text.lower())
        return filtered_text
    except:
        return ""

def solve_captcha_and_search(cnr_number):
    driver = get_driver()
    max_retries = 5
    retry_count = 0

    driver.get("https://services.ecourts.gov.in/")
    while retry_count < max_retries:
        cnr_input = driver.find_element(By.ID, "cino")
        cnr_input.clear()
        cnr_input.send_keys(cnr_number)

        captcha_text = read_captcha(driver)
        if not captcha_text or len(captcha_text.strip()) < 4:
            driver.refresh()
            retry_count += 1
            continue

        captcha_input = driver.find_element(By.ID, "fcaptcha_code")
        captcha_input.clear()
        captcha_input.send_keys(captcha_text)
        driver.find_element(By.ID, "searchbtn").click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "validateError"))
        )
        error_style = driver.find_element(By.ID, "validateError").get_attribute("style")
        if "display: none" in error_style:
            break
        else:
            driver.refresh()
            retry_count += 1
            continue

    if retry_count >= max_retries:
        raise Exception("Max retries exceeded for CAPTCHA solving")

    return {
        'case_details': extract_case_details_table(driver),
        'case_status': extract_case_status_table(driver),
        'petitioner_advocate': extract_petitioner_advocate_table(driver),
        'respondent_advocate': extract_respondent_advocate_table(driver),
        'acts': extract_acts_table(driver),
        'case_history': extract_history_table(driver),
        'order': extract_order_table(driver),
    }

# 🧩 TABLE PARSERS
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extract_case_details_table(driver):
    try:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".table.case_details_table.table-bordered"))
        )
        rows = table.find_elements(By.TAG_NAME, "tr")
        extracted_data = []
        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            extracted_data.append([col.text.strip() for col in columns])
        return extracted_data
    except:
        return []

def extract_case_status_table(driver):
    try:
        table = driver.find_element(By.CSS_SELECTOR, ".table.case_status_table.table-bordered")
        rows = table.find_elements(By.TAG_NAME, "tr")
        extracted_data = []

        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            extracted_data.append([col.text.strip() for col in columns])

        return extracted_data
    except:
        return []

def extract_petitioner_advocate_table(driver):
    try:
        table = driver.find_element(By.CSS_SELECTOR, ".table.table-bordered.Petitioner_Advocate_table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        extracted_data = []

        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            extracted_data.append([col.text.strip() for col in columns])

        return extracted_data
    except:
        return []

def extract_respondent_advocate_table(driver):
    try:
        table = driver.find_element(By.CSS_SELECTOR, ".table.table-bordered.Respondent_Advocate_table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        extracted_data = []

        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            extracted_data.append([col.text.strip() for col in columns])

        return extracted_data
    except:
        return []

def extract_acts_table(driver):
    try:
        table = driver.find_element(By.CSS_SELECTOR, ".table.acts_table.table-bordered")
        rows = table.find_elements(By.TAG_NAME, "tr")
        extracted_data = []

        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            extracted_data.append([col.text.strip() for col in columns])

        return extracted_data
    except:
        return []

def extract_history_table(driver):
    try:
        table = driver.find_element(By.CLASS_NAME, "history_table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        extracted_data = []

        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            extracted_data.append([col.text.strip() for col in columns])

        return extracted_data
    except:
        return []

def extract_order_table(driver):
    try:
        table = driver.find_element(By.CSS_SELECTOR, ".table.order_table.table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        extracted_data = []

        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            extracted_data.append([col.text.strip() for col in columns])

        return extracted_data
    except:
        return []