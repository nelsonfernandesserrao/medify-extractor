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

from core import get_name_student, get_email_element, setup_driver, login_to_website, get_credentials

DATE_TO_CHECK = "11 July"
MOCK_TITLE = "2025 UCAT Mock 19 - Revised"




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

            # Extract student name and email
            student_name = get_name_student(driver)
            student_email = get_email_element(body_text)

            # Extract number of questions answered
            number_of_questions_answered = 0

            try:
                heatmap_element = driver.find_element(By.CSS_SELECTOR, f'div[data-original-title*="{DATE_TO_CHECK}"]')
                heatmap_tooltip = heatmap_element.get_attribute("data-original-title")
                heatmap_match = re.search(r'(\d+)\s+questions\s+completed', heatmap_tooltip)
                if heatmap_match:
                    number_of_questions_answered = int(heatmap_match.group(1))
                else:
                    print(f"No questions answered found for {student_name} on {DATE_TO_CHECK}.")
                    permissions = False
                    continue
            except Exception as e:
                print(f"Could not find heatmap element for {student_name} on {DATE_TO_CHECK}: {str(e)}")
                student_info.append(
                    {
                        "Name": student_name,
                        "Email": student_email,
                        "Number of questions answered": 'No permissions',
                        'Mock': False
                    }
                )
                continue

            # Extract the mock link
            mock_link_elements = driver.find_elements(By.XPATH,
                                                      f'//div[@class="media-title" and contains(text(), "{MOCK_TITLE}")]/ancestor::a')
            if not mock_link_elements:
                print(f"No mock link found for {student_name}.")
                mock_link_element = None
            else:
                mock_link_element = mock_link_elements[0]

            if not mock_link_element:
                print(f"No mock link found for {student_name}.")
                student_info.append(
                    {
                        "Name": student_name,
                        "Email": student_email,
                        "Number of questions answered": number_of_questions_answered,
                        'Mock': False
                    }
                )
            else:
                mock_link = mock_link_element.get_attribute("href")
                if mock_link.startswith('/'):
                    mock_link = "https://app.medify.co" + mock_link

                driver.get(mock_link)

                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                rows = driver.find_elements(By.CSS_SELECTOR, "table.table tbody tr")[1:]
                flat_data = {}
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    subtest = cells[0].text.strip().replace(" ", "_")  # Safe key names
                    flat_data[f"{subtest}_Questions"] = int(cells[1].text.strip())
                    flat_data[f"{subtest}_Correct"] = int(cells[2].text.strip())
                    flat_data[f"{subtest}_Incorrect"] = int(cells[3].text.strip())
                    flat_data[f"{subtest}_Score"] = cells[4].text.strip()

                student_info.append(
                    {
                        "Name": student_name,
                        "Email": student_email,
                        "Number of questions answered": number_of_questions_answered,
                        'Mock': True
                    } | flat_data
                )
        return student_info

    except Exception as e:
        print(f"Scraping failed: {str(e)}")
        return []





def main():
    # Configuration
    LOGIN_URL = "https://app.medify.co/group_manager/sign_in"
    TARGET_URL = "https://app.medify.co/groups?cohort_year=2025"
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
