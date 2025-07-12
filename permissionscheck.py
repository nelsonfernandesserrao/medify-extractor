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


from core import setup_driver, login_to_website, get_credentials, get_name_student, get_email_element

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
