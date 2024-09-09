from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import openai
import json
from openai import OpenAI


client = OpenAI()
# Function to capture the HTML content of the team page
def get_html_content(team_url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    driver = webdriver.Chrome(options=options)  # Ensure chromedriver is in PATH

    try:
        # Navigate to the team page URL
        driver.get(team_url)

        # Wait until the page is fully loaded
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )

        # Get the page source (HTML content)
        html_content = driver.page_source

        return html_content

    finally:
        driver.quit()

# Function to get CSS selectors from OpenAI based on the HTML content
def get_selectors_from_openai(html_content):
    prompt = f"""
    You are given the following HTML content. Identify the CSS selectors to extract:
    1. Name
    2. Title
    3. Bio
    4. Social links

    Here is the HTML content:
    {html_content}

    Return the CSS selectors as a JSON object with the following format:
    {{
        "name": "CSS_SELECTOR",
        "title": "CSS_SELECTOR",
        "bio": "CSS_SELECTOR",
        "links": "CSS_SELECTOR"
    }}
    """

    completion = client.chat.completions.create(
        model="gpt-4o-mini",  # or "gpt-4" if you have access
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    return completion.choices[0].message

# Function to scrape the team page using dynamically determined selectors
def scrape_team_page_with_auto_selectors(team_url):
    # Get the HTML content of the team page
    html_content = get_html_content(team_url)

    # Ask OpenAI to generate CSS selectors for name, title, bio, and links
    selectors_message = get_selectors_from_openai(html_content)

    # Extract the content from the ChatCompletionMessage
    selectors_content = selectors_message.content

    # Print selectors to debug
    print("Extracted selectors:", selectors_content)

    # Parse the selectors from the string to a Python dictionary
    try:
        # Find the JSON object within the content
        json_start = selectors_content.find('{')
        json_end = selectors_content.rfind('}') + 1
        json_str = selectors_content[json_start:json_end]

        selectors_dict = json.loads(json_str)
    except json.JSONDecodeError:
        print("Error parsing JSON from OpenAI response.")
        return {"team": []}


    # Set up the Selenium driver again to scrape the page using the extracted selectors
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    driver = webdriver.Chrome(options=options)

    try:
        # Navigate to the team page URL
        driver.get(team_url)

        team_data = {"team": []}

        # Wait for the team member elements to be loaded and use the selectors from OpenAI
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selectors_dict['team_member']))
        )

        # Find all team member elements
        team_members = driver.find_elements(By.CSS_SELECTOR, selectors_dict['team_member'])

        for member in team_members:
            # Extract details using the site's selectors
            name = member.find_element(By.CSS_SELECTOR, selectors_dict['name']).text if member.find_elements(
                By.CSS_SELECTOR, selectors_dict['name']) else ""
            title = member.find_element(By.CSS_SELECTOR, selectors_dict['title']).text if member.find_elements(
                By.CSS_SELECTOR, selectors_dict['title']) else ""
            bio = member.find_element(By.CSS_SELECTOR, selectors_dict['bio']).text if member.find_elements(
                By.CSS_SELECTOR, selectors_dict['bio']) else ""
            links = [link.get_attribute('href') for link in
                     member.find_elements(By.CSS_SELECTOR, selectors_dict['links'])]

            # Add the member's data to the result
            team_data["team"].append({
                "name": name,
                "title": title,
                "bio": bio,
                "links": links
            })

        return team_data

    finally:
        driver.quit()

# Example usage:
if __name__ == "__main__":
    team_url = "https://www.accel.com/people"  # Replace with the actual team page URL you want to scrape
    team_data = scrape_team_page_with_auto_selectors(team_url)
    print(json.dumps(team_data, indent=4))
