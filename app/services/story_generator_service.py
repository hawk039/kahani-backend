from fastapi import UploadFile, HTTPException
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import os
from dotenv import load_dotenv
from PIL import Image
import io
import asyncio

# Load environment variables
load_dotenv()

# Configure the Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the Gemini model
# Using the alias 'gemini-flash-latest' to ensure we get a valid model version
model = genai.GenerativeModel('gemini-flash-latest')

def create_story_prompt(genre: str, tone: str, language: str) -> str:
    """
    Creates a detailed prompt for the LLM based on user input.
    """
    prompt = (
        f"Generate a short, engaging story in {language}. "
        f"The story should be in the {genre} genre and have a {tone} tone. "
        "The story should be inspired by the accompanying image. "
        "Describe the scene and characters vividly. Do not add any titles or headers."
    )
    return prompt

async def generate_story_from_image_and_prompt(
    file: UploadFile, 
    prompt: str
) -> str:
    """
    Processes an image, sends it to the Gemini API with a prompt,
    and returns the generated story. Handles rate limits with retries.
    """
    try:
        # Read the image file
        image_bytes = await file.read()
        
        # Open the image using Pillow to ensure it's a valid image
        try:
            img = Image.open(io.BytesIO(image_bytes))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file.")

        # Retry logic for rate limits
        max_retries = 3
        base_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                # Generate content using the Gemini API
                response = await model.generate_content_async([prompt, img])
                return response.text
            
            except google_exceptions.ResourceExhausted:
                # If we hit a rate limit, wait and try again
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt) # Exponential backoff: 2s, 4s, 8s
                    print(f"Rate limit hit. Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    # If we run out of retries, raise a specific 429 error
                    raise HTTPException(
                        status_code=429, 
                        detail="Service is busy (Rate Limit Exceeded). Please try again later."
                    )
            except Exception as e:
                # Re-raise other exceptions immediately
                raise e

    except HTTPException as he:
        raise he
    except Exception as e:
        # Handle potential API errors or other issues
        print(f"An error occurred during story generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate story.")
