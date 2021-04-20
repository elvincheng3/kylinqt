from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import selenium
import logging
import time
import json

class DashboardDriver:

    # Initialize the Selenium WebDriver
    def __init__(self):
        logging.info("Initializing Driver")
        self.proper_initialize = False
        self.opts = Options()
        self.opts.add_argument(
            "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36"
        )
        self.opts.add_argument("user-data-dir=selenium")
        self.opts.add_argument("--disable-blink-features")
        self.opts.add_argument("--disable-blink-features=AutomationControlled")
        self.opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.opts.add_experimental_option('useAutomationExtension', False)
        try:
            self.driver = webdriver.Chrome(options=self.opts)
            self.driver.set_window_size(1920, 1080)
            self.wait = WebDriverWait(self.driver, 10)
            self.proper_initialize = True
        except selenium.common.exceptions.InvalidArgumentException:
            logging.info("Unable to start driver because another instance is currently open")
    
    # Set a new driver
    def newDriver(self):
        logging.info("Driver connection was refused, restarting driver")
        try:
            self.driver.close()
        except Exception as e:
            logging.info("While trying to close old driver, error was raised")
        self.driver = webdriver.Chrome(options=self.opts)
        self.driver.set_window_size(1920, 1080)
        self.wait = WebDriverWait(self.driver, 10)
        time.sleep(.5)
    
    # Close the driver
    def close(self):
        self.driver.close()

    # Navigate to specified path
    def navigate(self, path):
        try:
            time.sleep(2)
            self.driver.get(path)
            return True
        except ConnectionRefusedError:
            self.newDriver()
            return False

    # Click an element based on its XPath
    def click(self, xpath):
        try:
            time.sleep(2)
            button = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            button.click()
        except ConnectionRefusedError:
            self.newDriver()
            return False

    # Fill a field with text based on its XPath
    def fill_text(self, xpath, text):
        try:
            time.sleep(2)
            field = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            field.send_keys(text)
        except ConnectionRefusedError:
            self.newDriver()
            return False

    def find(self, xpath):
        try:
            self.driver.find_element_by_xpath(xpath)
            logging.info("Found OAuth")
            return True
        except selenium.common.exceptions.NoSuchElementException as e:
            logging.info(e)
            return False

    # Login to Dashboard
    def login(self, login_state, user, pw):
        login_url = "https://dashboard.kylinbot.io/"
        if login_state:
            if self.navigate(path=login_url):
                logging.info("Already Logged In")
                return True
            logging.info("Error Navigating to Dashboard")
            return False
            
        login_success = False
        attempt_counter = 0
        while not login_success and attempt_counter < 3:
            # TODO login error handling needs to be fixed
            try:
                self.navigate(path=login_url)
                logging.info("Navigated to dashboard, Signing In")
                self.click(xpath='//*[@id="app"]/div/div/div/div/div[2]/button') # login to discord
                # TODO Need to change xpath to more specific for other login scenario
                # if not self.find('//*[@id="app-mount"]'):
                self.fill_text(xpath='//*[@id="app-mount"]/div[2]/div/div[2]/div/div/form/div/div/div[1]/div[3]/div[1]/div/div[2]/input', text=user) # username
                self.fill_text(xpath='//*[@id="app-mount"]/div[2]/div/div[2]/div/div/form/div/div/div[1]/div[3]/div[2]/div/input', text=pw) # password
                self.click(xpath='//*[@id="app-mount"]/div[2]/div/div[2]/div/div/form/div/div/div[1]/div[3]/button[2]') # login button
                self.click(xpath='//*[@id="app-mount"]/div[2]/div/div[2]/div/div/div[2]/button[2]') # accept button
                login_success = True
            except Exception as e:
                logging.info("Login error, retrying...")
                logging.info(e.msg)
                attempt_counter += 1
                time.sleep(2)
        if not login_success:
            return False
        with open('login.json', 'w') as outfile:
            json.dump({"logged_in":True}, outfile)
        return True

    # Stop all QT
    def stop_all_tasks(self, sku, site):
        stop_url = "https://dashboard.kylinbot.io/quick-task/kylin-bot/stop"
        logging.info("Stopping tasks with SKU {} on {}".format(sku, site))
        return self.navigate(path=stop_url)

    # Delete all QT
    def delete_all_tasks(self):
        delete_url = "https://dashboard.kylinbot.io/quick-task/kylin-bot/delete"
        logging.info("Deleting All Tasks")
        return self.navigate(path=delete_url)

    # Create QT
    def create_task(self, sku, site):
        query = "https://dashboard.kylinbot.io/quick-task/kylin-bot/create?input=https://www." + str(site) + ".com/product/~/" + str(sku) + ".html&sku=" + str(sku)
        logging.info("SKU {} Found on {}, Starting Tasks".format(sku, site))
        return self.navigate(path=query)