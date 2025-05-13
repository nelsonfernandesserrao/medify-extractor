import re
import os
import time
import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
		service=Service(ChromeDriverManager().install()),
		options=chrome_options
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
		WebDriverWait(driver, 10).until(
			EC.url_changes(url)
		)

		print("Login successful")
		return True

	except Exception as e:
		print(f"Login failed: {str(e)}")
		return False


def scrape_data(driver, target_url):
	"""Navigate to the target URL and scrape data."""
	try:
		# Navigate to the page containing the data
		driver.get(target_url)
		print(f"Navigated to: {target_url}")

		# Wait for the data to load (identified by the presence of a specific text: "Pay for students")
		WebDriverWait(driver, 10).until(
			EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Pay for students")
		)

		# Get all data items
		data_elements = driver.find_elements(By.TAG_NAME, "a")

		# Extract data
		student_urls = []
		pattern = r"/group_managers/cohorts/\d+/members/\d+"

		for element in data_elements:
			href = element.get_attribute("href")
			if href and re.search(pattern, href):
				student_urls.append(href)

		print(f"Scraped {len(student_urls)} items")

		student_info = []

		for i, url in enumerate(student_urls):
			driver.get(url)

			print(f"Scraping {i + 1}/{len(student_urls)}: {url}")
			WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.TAG_NAME, "body"))
			)

			body_text = driver.find_element(By.TAG_NAME, "body").text

			student_name = get_name_student(driver)
			student_email = get_email_element(body_text)

			permission_flag = True

			if "has not given you permission" in body_text:
				print(f"{student_name} has not given permission.")
				permission_flag = False

			student_info.append(
				{
					"Name": student_name,
					"Email": student_email,
					"Permission given": permission_flag,
				}
			)

		return student_info

	except Exception as e:
		print(f"Scraping failed: {str(e)}")
		return []


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
		email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', body_text)
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
	load_dotenv()
	try:
		username = os.getenv("USERNAME")
		password = os.getenv("PASSWORD")

		if not username or not password:
			raise ValueError("Username or password not found in environment variables.")

		return username, password

	except Exception as e:
		print(f"Error loading credentials: {str(e)}")
		return None, None


def main():
	# Configuration
	LOGIN_URL = "https://app.medify.co/group_manager/sign_in"
	TARGET_URL = "https://app.medify.co/groups"
	OUTPUT_FILE = "scraped_data.csv"

	# Load credentials
	USERNAME, PASSWORD = get_credentials()

	# Setup webdriver
	driver = setup_driver()

	try:
		# Login to the website
		if login_to_website(driver, LOGIN_URL, USERNAME, PASSWORD):
			# Delay to ensure the page is fully loaded
			time.sleep(2)

			# Scrape data
			data = scrape_data(driver, TARGET_URL)
			df = pd.DataFrame(data)

			# Check if DataFrame is not empty before saving
			if not df.empty:
				df.to_csv(OUTPUT_FILE, index=False)
				print(f"Data saved to {OUTPUT_FILE}")
			else:
				print("No data to save.")

		else:
			print("Could not login. Scraping aborted.")

	except Exception as e:
		print(f"An error occurred: {str(e)}")

	finally:
		# Clean up
		driver.quit()
		print("Browser closed.")


if __name__ == "__main__":
	main()
