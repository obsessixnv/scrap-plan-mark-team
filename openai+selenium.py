from flask import Flask, request, jsonify
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urljoin
from crawl4ai.web_crawler import WebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field
import json

app = Flask(__name__)


def find_team_page(base_url):
    # Keywords to search for in the URLs
    keywords = ['team', 'people', 'about', 'staff', 'leadership', 'our-team', 'who-we-are']

    # Set up the web driver (Chrome in this example)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode to avoid opening a browser window
    driver = webdriver.Chrome(options=options)  # Ensure chromedriver is in PATH or specify its path

    try:
        # Navigate to the base URL
        driver.get(base_url)

        # Find all links (anchor tags with href attributes)
        links = driver.find_elements(By.TAG_NAME, 'a')

        # Loop through the links to find matching keywords
        for link in links:
            href = link.get_attribute('href')
            text = link.text.lower()

            # Skip empty or None hrefs
            if href:
                href_lower = href.lower()

                # Check if the href or link text contains any of the keywords
                if any(keyword in href_lower for keyword in keywords) or any(keyword in text for keyword in keywords):
                    # Join relative URLs with the base URL
                    full_url = urljoin(base_url, href)
                    print(f"Found possible team page: {full_url}")
                    return full_url

        print("No team/people page found.")
        return base_url

    finally:
        # Close the browser
        driver.quit()

class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(..., description="Fee for output token for the OpenAI model.")


@app.route('/extract_team_info', methods=['POST'])
def extract_team_info():
    data = request.json
    domain = data.get('domain')

    if not domain:
        return jsonify({"error": "Domain is required"}), 400

    url = find_team_page(domain)

    crawler = WebCrawler()
    crawler.warmup()

    result = crawler.run(
        url=url,
        word_count_threshold=1,
        extraction_strategy=LLMExtractionStrategy(
            provider="openai/gpt-4o-mini",
            api_token=os.getenv('OPENAI_API_KEY'),
            schema=OpenAIModelFee.model_json_schema(),
            extraction_type="schema",
            instruction="Extract all team members mentioned on the page. "
                        "Look for sections related to 'Team', 'People', 'Bio' or any equivalent terms. "
                        "For each team member found, extract the following details and format them into JSON: "
                        "- Name: 'The full name of the team member' "
                        "- Title: 'The professional title of the team member' "
                        "- info: 'link that follows click on member card or member photo or his name or specific button so we redirect to his info page(<a href = this link>) If no member link provided parse members info. It can be in :before :after structure or just on member card.(text)'"
                        "If no team member or people information is found on the page, return an empty array. "
                        "One extracted team member JSON format should look like this: "
                        '{ "name": "John Doe", "title": "CEO", "info": "https://example/author/john-doe/" or "information about team member" } '
                        "Ensure that you find all information for every member on the page"
                        "If no member link provided parse members info. It can be in :before :after structure or just on member card.(text)"
                        "Do not dive in xml files, work with opened structure and links provided to user"
                        "For info field try all cases for each member first, then find the most informative case and only then add it to 'info' field "
                        "Make sure the function handles pages with no team information by returning an empty array if nothing is found."),
        bypass_cache=True,
    )

    team_info = json.loads(result.extracted_content)

    output = {
        "team": team_info,
        "team_domain": url

    }

    return jsonify(output)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
