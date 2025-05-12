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

# Function to get Job Market Trends from AI (Gemini)
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

# Function to get resume analysis from AI (Gemini)
def analyze_resume_with_ai(resume_content):
    try:
        # Configure Gemini API
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Construct prompt correctly
        prompt = f"""
You are a professional resume analyst.  
Always respond in this strict JSON format:

{{
  "Overall Score": "<integer>/10",
  "Rationale": "<short summary of the score reasoning>",
  "Detailed Breakdown": {{
    "Contact Information": {{
      "Strengths": ["..."],
      "Weaknesses": ["..."],
      "Recommendations": ["..."]
    }},
    "Skills": {{
      "Strengths": ["..."],
      "Weaknesses": ["..."],
      "Recommendations": ["..."]
    }},
    "Work Experience": {{
      "Strengths": ["..."],
      "Weaknesses": ["..."],
      "Recommendations": ["..."]
    }},
    "Education": {{
      "Strengths": ["..."],
      "Weaknesses": ["..."],
      "Recommendations": ["..."]
    }},
    "Certifications": {{
      "Strengths": ["..."],
      "Weaknesses": ["..."],
      "Recommendations": ["..."]
    }}
  }},
  "Overall Recommendations": [
    "...",
    "...",
    "..."
  ]
}}

Analyze this resume and return the JSON only.  
Resume Content:
{resume_content}
"""

        # Send request to Gemini API
        response = model.generate_content(prompt)
        analysis_text = response.text.strip()

        # Clean any Markdown code blocks if present
        cleaned_content = re.sub(r"^```(?:json)?\s*|\s*```$", "", analysis_text, flags=re.MULTILINE).strip()

        # Validate JSON
        analysis_json = json.loads(cleaned_content)

        # ✅ Return JSON object (you can convert to string later when rendering)
        return analysis_json

    except Exception as e:
        logger.error(f"Error in resume analysis: {str(e)}")
        return {"error": str(e)}
    
