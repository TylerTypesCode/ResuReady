import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
import os
import logging

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# Load environment variables
load_dotenv()

# Fetch the Gemini API key from environment variables
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    logger.error("Gemini API Key is not set. Please check your environment variables.")
else:
    logger.debug(f"Gemini API Key loaded successfully.")

def get_job_market_trends():
    """
    Fetch 3 current job market trends using Gemini 2.0 Flash.

    Returns:
        List of dictionaries: [{ 'title': str, 'summary': str }]
    """
    if not api_key:
        logger.error("API Key is missing. Cannot proceed.")
        return []

    try:
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Construct the prompt for Gemini 2.0
        prompt = (
            "Provide exactly 3 concise and current job market trends for today "
            "in the U.S. Each trend should include a short title and a 2-sentence summary. "
            "Format it as a JSON list of objects with keys 'title' and 'summary'."
        )

        logger.debug(f"Sending request to Gemini with prompt: {prompt}")

        # Fetch content from Gemini API
        response = model.generate_content(prompt)

        # Get the raw response text from Gemini
        content = response.text.strip()
        logger.debug(f"Received response from Gemini: {content}")

        if content:
            try:
                # ✅ Clean response from ```json and ``` if they exist
                cleaned_content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE).strip()

                # Parse the cleaned content as JSON
                trends = json.loads(cleaned_content)

                # Ensure the response is a list, then return the first 3 trends
                if isinstance(trends, list):
                    logger.debug(f"Parsed JSON trends successfully: {trends}")
                    return trends[:3]
                else:
                    logger.error("Received response is not in the expected list format.")
                    return []
            except json.JSONDecodeError as e:
                logger.error(f"Error: Could not parse JSON response. {e}")
                return []
        else:
            logger.error("Error: Empty response received from Gemini.")
            return []

    except Exception as e:
        # General exception catch to log any unexpected errors
        logger.error(f"Gemini API error: {e}")
        return []

