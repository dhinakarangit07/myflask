import time
import re
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver import get_driver, restart_driver

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

import time
import re
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver import get_driver, restart_driver
import os
from datetime import datetime

def solve_captcha_and_search_with_status(cnr_number):
    """Enhanced function that yields status updates during processing"""
    driver = get_driver()
    max_retries = 2
    retry_count = 0
    
    try:
        # Initial status
        yield {
            'status': 'processing',
            'message': 'Initializing case details extraction...',
            'progress': 5
        }
        
        # Navigate to the target page (only if not already there)
        if "services.ecourts.gov.in" not in driver.current_url:
            yield {
                'status': 'processing',
                'message': 'Navigating to eCourts website...',
                'progress': 10
            }
            #driver.get("https://services.ecourts.gov.in/")
            driver.get("https://services.ecourts.gov.in/ecourtindia_v6/")
            
            yield {
                'status': 'processing',
                'message': 'Website loaded successfully',
                'progress': 15
            }
        
        while retry_count < max_retries:
            try:
                # Update status for current attempt
                yield {
                    'status': 'processing',
                    'message': f'Entering CNR number (attempt {retry_count + 1}/{max_retries})...',
                    'progress': 20 + (retry_count * 5)
                }
                
                # Clear and enter CNR number
                cnr_input = driver.find_element(By.ID, "cino")
                cnr_input.clear()
                cnr_input.send_keys(cnr_number)

                yield {
                    'status': 'processing',
                    'message': f'Reading CAPTCHA image (attempt {retry_count + 1}/{max_retries})...',
                    'progress': 25 + (retry_count * 5)
                }

                # Read and enter CAPTCHA
                captcha_text = read_captcha(driver)
                if not captcha_text or len(captcha_text.strip()) < 4:
                    yield {
                        'status': 'processing',
                        'message': f'CAPTCHA reading failed, retrying... (attempt {retry_count + 1}/{max_retries})',
                        'progress': 30 + (retry_count * 5)
                    }
                    driver.refresh()
                    retry_count += 1
                    continue

                yield {
                    'status': 'processing',
                    'message': f'CAPTCHA text extracted: "{captcha_text.upper()}", submitting...',
                    'progress': 35 + (retry_count * 5)
                }

                captcha_input = driver.find_element(By.ID, "fcaptcha_code")
                captcha_input.clear()
                captcha_input.send_keys(captcha_text)
                
                # Click search button
                driver.find_element(By.ID, "searchbtn").click()

                yield {
                    'status': 'processing',
                    'message': 'Waiting for server response...',
                    'progress': 40 + (retry_count * 5)
                }

                # Wait for validation response
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "validateError"))
                )
                
                error_style = driver.find_element(By.ID, "validateError").get_attribute("style")
                if "display: none" in error_style:
                    # CAPTCHA verified successfully
                    yield {
                        'status': 'processing',
                        'message': 'CAPTCHA solved successfully!',
                        'progress': 50
                    }
                    break
                else:
                    # CAPTCHA failed, retry
                    yield {
                        'status': 'processing',
                        'message': f'CAPTCHA validation failed, retrying... (attempt {retry_count + 1}/{max_retries})',
                        'progress': 45 + (retry_count * 5)
                    }
                    driver.refresh()
                    retry_count += 1
                    continue
                    
            except Exception as e:
                yield {
                    'status': 'processing',
                    'message': f'Error in attempt {retry_count + 1}: {str(e)}',
                    'progress': 30 + (retry_count * 5)
                }
                print(f"Error in attempt {retry_count + 1}: {str(e)}")
                if retry_count < max_retries - 1:
                    try:
                        yield {
                            'status': 'processing',
                            'message': 'Refreshing page and retrying...',
                            'progress': 35 + (retry_count * 5)
                        }
                        driver.refresh()
                        retry_count += 1
                        continue
                    except:
                        # If refresh fails, restart driver
                        yield {
                            'status': 'processing',
                            'message': 'Restarting WebDriver due to connection issues...',
                            'progress': 25 + (retry_count * 5)
                        }
                        print("Refresh failed, restarting driver...")
                        driver = restart_driver()
                        retry_count += 1
                        continue
                else:
                    raise e

        if retry_count >= max_retries:
            yield {
                'status': 'error',
                'message': f'Max retries ({max_retries}) exceeded for CAPTCHA solving',
                'progress': 0
            }
            raise Exception("Max retries exceeded for CAPTCHA solving")

        # Extract all case information with status updates
        yield {
            'status': 'processing',
            'message': 'Extracting case details...',
            'progress': 60
        }
        case_details = extract_case_details_table(driver.page_source)
        
        yield {
            'status': 'processing',
            'message': 'Extracting case status...',
            'progress': 65
        }
        case_status = extract_case_status_table(driver.page_source)
        
        yield {
            'status': 'processing',
            'message': 'Extracting petitioner advocate details...',
            'progress': 70
        }
        petitioner_advocate = extract_petitioner_advocate_table(driver.page_source)
        
        yield {
            'status': 'processing',
            'message': 'Extracting respondent advocate details...',
            'progress': 75
        }
        respondent_advocate = extract_respondent_advocate_table(driver.page_source)
        
        yield {
            'status': 'processing',
            'message': 'Extracting acts information...',
            'progress': 80
        }
        acts = extract_acts_table(driver)
        
        yield {
            'status': 'processing',
            'message': 'Extracting case history...',
            'progress': 85
        }
        case_history = extract_history_table(driver.page_source)
        
        yield {
            'status': 'processing',
            'message': 'Extracting order details...',
            'progress': 90
        }
        order = extract_order_table(driver.page_source)
        
        yield {
            'status': 'processing',
            'message': 'Compiling final results...',
            'progress': 95
        }
        
        # Final result
        result = {
            'case_details': case_details,
            'case_status': case_status,
            'petitioner_advocate': petitioner_advocate,
            'respondent_advocate': respondent_advocate,
            'acts': acts,
            'case_history': case_history,
            'order': order,
        }
        
        # Close the current tab/window after successful extraction
        yield {
            'status': 'processing',
            'message': 'Closing browser tab...',
            'progress': 98
        }
        
        try:
            # Close current tab
            driver.close()
            
            # If there are other tabs, switch to the last one
            if len(driver.window_handles) > 0:
                driver.switch_to.window(driver.window_handles[-1])
            else:
                # If no tabs left, create a new blank tab
                driver.execute_script("window.open('', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])
        except Exception as e:
            print(f"Error closing tab: {str(e)}")
            # Continue anyway as data extraction was successful
        
        yield {
            'status': 'success',
            'message': 'Case details extracted successfully and tab closed!',
            'progress': 100,
            'data': result
        }
        
    except Exception as e:
        print(f"Error in solve_captcha_and_search_with_status: {str(e)}")
        
        # Try to close tab even on error
        try:
            driver.close()
            if len(driver.window_handles) > 0:
                driver.switch_to.window(driver.window_handles[-1])
            else:
                driver.execute_script("window.open('', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])
        except:
            pass
        
        # Try to restart driver on critical errors
        if "WebDriver" in str(e) or "chrome" in str(e).lower():
            print("WebDriver error detected, restarting driver...")
            yield {
                'status': 'processing',
                'message': 'WebDriver error detected, restarting...',
                'progress': 15
            }
            try:
                driver = restart_driver()
                yield {
                    'status': 'processing',
                    'message': 'WebDriver restarted, please try again',
                    'progress': 20
                }
            except:
                pass
        
        yield {
            'status': 'error',
            'message': f'Failed to extract case details: {str(e)}',
            'progress': 0
        }
        raise e

# 🧩 TABLE PARSERS
import re
from bs4 import BeautifulSoup
from datetime import datetime
import os

# 🧩 TABLE PARSERS
def extract_case_details_table(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.select_one(".table.case_details_table.table-bordered")
        if not table:
            print("Case details table not found")
            return []
        rows = table.find_all("tr")
        extracted_data = []
        for row in rows:
            columns = row.find_all("td")
            extracted_data.append([col.get_text(strip=True) for col in columns])
        return extracted_data
    except Exception as e:
        print(f"Error extracting case details: {str(e)}")
        return []

def extract_case_status_table(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.select_one(".table.case_status_table.table-bordered")
        if not table:
            print("Case status table not found")
            return []
        rows = table.find_all("tr")
        extracted_data = []
        for row in rows:
            columns = row.find_all("td")
            extracted_data.append([col.get_text(strip=True) for col in columns])
        return extracted_data
    except Exception as e:
        print(f"Error extracting case status: {str(e)}")
        return []

def extract_petitioner_advocate_table(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.select_one(".table.table-bordered.Petitioner_Advocate_table")
        if not table:
            print("Petitioner advocate table not found")
            return []
        rows = table.find_all("tr")
        extracted_data = []
        for row in rows:
            columns = row.find_all("td")
            extracted_data.append([col.get_text(strip=True) for col in columns])
        return extracted_data
    except Exception as e:
        print(f"Error extracting petitioner advocate: {str(e)}")
        return []

def extract_respondent_advocate_table(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.select_one(".table.table-bordered.Respondent_Advocate_table")
        if not table:
            print("Respondent advocate table not found")
            return []
        rows = table.find_all("tr")
        extracted_data = []
        for row in rows:
            columns = row.find_all("td")
            extracted_data.append([col.get_text(strip=True) for col in columns])
        return extracted_data
    except Exception as e:
        print(f"Error extracting respondent advocate: {str(e)}")
        return []

def extract_acts_table(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.select_one(".table.acts_table.table-bordered")
        if not table:
            print("Acts table not found")
            return []
        rows = table.find_all("tr")
        extracted_data = []
        for row in rows:
            columns = row.find_all("td")
            extracted_data.append([col.get_text(strip=True) for col in columns])
        return extracted_data
    except Exception as e:
        print(f"Error extracting acts: {str(e)}")
        return []

def extract_history_table(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.select_one(".table.history_table")
        if not table:
            print("History table not found")
            return []
        rows = table.find_all("tr")
        extracted_data = []
        for row in rows:
            columns = row.find_all("td")
            extracted_data.append([col.get_text(strip=True) for col in columns])
        return extracted_data
    except Exception as e:
        print(f"Error extracting history: {str(e)}")
        return []

def extract_order_table(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.select_one(".table.order_table.table")
        if not table:
            print("Order table not found")
            return []
        rows = table.find_all("tr")
        extracted_data = []
        for row in rows:
            columns = row.find_all("td")
            extracted_data.append([col.get_text(strip=True) for col in columns])
        return extracted_data
    except Exception as e:
        print(f"Error extracting order: {str(e)}")
        return []