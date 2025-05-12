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
    
def simulate_mock_interview(company, position, resume_text=None, user_response=None, session_id=None, is_start=False, force_complete=False, asked_questions=None):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        if asked_questions is None:
            asked_questions = []

        if force_complete:
            prompt = f"""
You are concluding a mock interview for {position} at {company}. Based on the candidate's responses, provide a detailed evaluation.

Previous questions and responses summary:
{asked_questions}

Final response from candidate: {user_response}

Provide a complete evaluation following this exact JSON format with detailed feedback:
{{
    "is_complete": true,
    "scores": {{
        "communication": <score 1-10>,
        "technical_knowledge": <score 1-10>,
        "problem_solving": <score 1-10>,
        "overall_score": <score 1-10>
    }},
    "feedback": {{
        "strengths": [
            "<specific strength point 1>",
            "<specific strength point 2>",
            "<specific strength point 3>"
        ],
        "areas_for_improvement": [
            "<specific improvement point 1>",
            "<specific improvement point 2>",
            "<specific improvement point 3>"
        ],
        "specific_recommendations": [
            "<detailed recommendation 1>",
            "<detailed recommendation 2>",
            "<detailed recommendation 3>"
        ]
    }}
}}

Ensure your response:
1. Contains only the JSON object
2. Includes specific, actionable feedback
3. References actual responses from the interview
4. Provides meaningful scores based on performance
"""
            try:
                response = model.generate_content(prompt)
                response_text = response.text.strip()
                
                # Clean any markdown formatting
                cleaned_response = re.sub(r"^```(?:json)?\s*|\s*```$", "", response_text, flags=re.MULTILINE).strip()
                
                # Parse JSON response
                evaluation = json.loads(cleaned_response)
                
                # Validate the structure
                required_keys = ["is_complete", "scores", "feedback"]
                if all(key in evaluation for key in required_keys):
                    return evaluation
                else:
                    raise ValueError("Invalid response structure")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Error parsing final evaluation: {str(e)}")
                # Create a more personalized fallback response
                return {
                    "is_complete": True,
                    "scores": {
                        "communication": 7,
                        "technical_knowledge": 7,
                        "problem_solving": 7,
                        "overall_score": 7
                    },
                    "feedback": {
                        "strengths": [
                            f"Completed full interview for {position} position",
                            "Maintained professional communication",
                            "Engaged thoroughly in the process"
                        ],
                        "areas_for_improvement": [
                            "Consider providing more specific examples",
                            "Focus on role-specific technical details",
                            "Structure responses more concisely"
                        ],
                        "specific_recommendations": [
                            f"Research more about {company}'s technical requirements",
                            "Practice the STAR method for behavioral questions",
                            "Prepare concrete examples of past experiences"
                        ]
                    }
                }

        elif is_start:
            prompt = f"""
You are conducting a 15-minute mock interview as a hiring manager at {company} for the {position} position.

Follow these rules:
1. Start with a brief introduction as the interviewer
2. Ask one relevant question that hasn't been asked before
3. Mix behavioral and technical questions relevant to the role
4. Maintain a professional tone

Resume Context:
{resume_text or "No resume provided"}

Begin the interview with your introduction and first question.
"""
        else:
            prompt = f"""
Continue the mock interview for {position} at {company}.

Previous questions asked: {asked_questions}
Previous response from candidate: {user_response}

Analyze the response and ask a new question that:
1. Hasn't been asked before
2. Is relevant to the role
3. Builds on previous responses
4. Alternates between behavioral and technical focus

Response analysis considerations:
- Clarity and communication
- Relevance to the question
- Professional demeanor
- Technical accuracy (if applicable)

Provide a new, unique interview question.
"""

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Handle forced completion or try to parse JSON response
        if force_complete:
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                # If parsing fails, create a generic completion response
                return {
                    "is_complete": True,
                    "scores": {
                        "communication": 7,
                        "technical_knowledge": 7,
                        "problem_solving": 7,
                        "overall_score": 7
                    },
                    "feedback": {
                        "strengths": ["Good participation", "Engaged in conversation"],
                        "areas_for_improvement": ["Interview ended due to length limit"],
                        "specific_recommendations": ["Practice more concise responses"]
                    }
                }
        
        # Return in the expected format for continuing interview
        return {
            'interviewer_response': response_text,
            'is_complete': False
        }

    except Exception as e:
        logger.error(f"Error in mock interview: {str(e)}")
        return {"error": str(e)}