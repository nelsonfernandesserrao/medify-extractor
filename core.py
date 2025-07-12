import os
import re

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def setup_driver():
	"""Set up and return a Chrome webdriver with appropriate options."""
	# Set up Chrome options
	chrome_options = Options()
	chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
	chrome_options.add_argument("--no-sandbox")
	chrome_options.add_argument("--disable-dev-shm-usage")

	# Initialize Chrome driver
	driver = webdriver.Chrome(
		service=Service(ChromeDriverManager().install()), options=chrome_options
	)

	return driver


def login_to_website(driver, url, username, password):
	"""Login to the specified website using the provided credentials."""
	try:
		# Navigate to the login page
		driver.get(url)
		print(f"Navigated to: {url}")

		# Wait for the login form to load
		username_field = WebDriverWait(driver, 10).until(
			EC.presence_of_element_located((By.ID, "group_manager_email"))
		)
		password_field = driver.find_element(By.ID, "group_manager_password")

		# Enter credentials
		username_field.send_keys(username)
		password_field.send_keys(password)

		# Click login button
		login_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
		login_button.click()

		# Wait for the login to complete
		WebDriverWait(driver, 10).until(EC.url_changes(url))

		print("Login successful")
		return True

	except Exception as e:
		print(f"Login failed: {str(e)}")
		return False


def get_name_student(driver):
	"""Extract student name from the page."""
	try:
		name_element = driver.find_element(By.CSS_SELECTOR, "h1")
		name = name_element.text
		return name
	except Exception as e:
		print(f"Error extracting name: {str(e)}")
		return None


def get_email_element(body_text):
	"""Extract email from the body text using regex."""
	try:
		email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", body_text)
		if email_match:
			email = email_match.group(0)
			return email
		else:
			print("Email not found in the body text.")
			return None

	except Exception as e:
		print(f"Error extracting email: {str(e)}")
		return None


def get_credentials():
	"""Load credentials from environment variables."""
	load_dotenv('.env')
	try:
		username = os.getenv("MEDIFY_USERNAME")
		password = os.getenv("MEDIFY_PASSWORD")

		if not username or not password:
			raise ValueError("Username or password not found in environment variables.")

		return username, password

	except Exception as e:
		print(f"Error loading credentials: {str(e)}")
		return None, None
