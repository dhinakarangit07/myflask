import os
import atexit
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException

_driver = None

def initialize_driver():
    """Initialize the WebDriver once when the application starts."""
    global _driver
    if _driver is None:
        try:
            # Configure Chrome options for performance and headless mode
            options = Options()
            options.add_argument('--headless=new')  # Headless mode
            options.add_argument('--disable-gpu')  # Disable GPU for headless
            options.add_argument('--no-sandbox')  # Required for containerized environments
            options.add_argument('--disable-dev-shm-usage')  # Avoid /dev/shm issues
            options.add_argument('--disable-extensions')  # Disable extensions to reduce overhead
            options.add_argument('--disable-infobars')  # Disable info bars
            options.add_argument('--disable-notifications')  # Disable notifications
            options.add_argument('--disable-background-networking')  # Disable background network activity
            options.add_argument('--disable-sync')  # Disable sync to reduce network calls
            options.add_argument('--disable-translate')  # Disable translation prompts
            options.add_argument('--no-first-run')  # Skip first-run setup
            options.add_argument('--window-size=1920,1080')  # Set window size for consistent rendering
            options.add_argument('--log-level=3')  # Minimize logging
            options.add_experimental_option("excludeSwitches", ["enable-logging"])

            # Set cache directory to /tmp for container compatibility
            os.environ['WDM_LOCAL'] = '1'
            os.environ['WDM_CACHE_DIR'] = '/tmp'

            # Initialize ChromeDriver with optimized service
            chrome_service = Service(ChromeDriverManager().install())
            _driver = webdriver.Chrome(service=chrome_service, options=options)

            # Set high timeouts for slow networks or CAPTCHA solving
            _driver.set_page_load_timeout(60)  # Increased to 60 seconds as requested
            _driver.set_script_timeout(30)  # Timeout for JavaScript execution
            _driver.implicitly_wait(10)  # Implicit wait for element loading

            print("WebDriver initialized successfully and ready for use")
            
            # Register cleanup function to run when app shuts down
            atexit.register(quit_driver)
            
        except WebDriverException as e:
            print(f"Failed to initialize WebDriver: {str(e)}")
            quit_driver()  # Clean up if initialization fails
            raise

def get_driver():
    """Get the existing WebDriver instance."""
    global _driver
    if _driver is None:
        raise Exception("WebDriver not initialized. Call initialize_driver() first.")
    
    # Check if driver is still alive
    try:
        _driver.current_url  # This will raise an exception if driver is dead
        return _driver
    except Exception:
        print("WebDriver seems to be dead, reinitializing...")
        _driver = None
        initialize_driver()
        return _driver

def quit_driver():
    """Quit the WebDriver and clean up resources."""
    global _driver
    if _driver is not None:
        try:
            _driver.quit()
            print("WebDriver closed successfully")
        except Exception as e:
            print(f"Error quitting WebDriver: {str(e)}")
        finally:
            _driver = None

def restart_driver():
    """Restart the WebDriver (useful for recovery from errors)."""
    print("Restarting WebDriver...")
    quit_driver()
    initialize_driver()
    return get_driver()