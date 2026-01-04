from fastapi import HTTPException
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import os
from dotenv import load_dotenv
from PIL import Image
import io
import asyncio
from typing import Tuple
import re

# Load environment variables
load_dotenv()

# Configure the Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-flash-latest')


def create_story_prompt(genre: str, tone: str, language: str) -> str:
    """
    Creates a detailed prompt for the LLM based on user input.
    """
    prompt = (
        f"Analyze the uploaded image to establish the setting and atmosphere of the story. "
        f"Write a high-quality, immersive story in {language}. "
        f"Genre: {genre}. Tone: {tone}.\n\n"
        "Guidelines:\n"
        "1. Open with a gripping hook that immediately pulls the reader into the scene.\n"
        "2. Create a compelling protagonist whose emotions resonate with the setting.\n"
        "3. Use the environment to build atmosphere and mood, describing sights, sounds, and feelings vividly.\n"
        "4. Focus on narrative flow and character depth. Do NOT use camera angles, script directions, or technical film jargon.\n"
        "5. Keep the pacing tight and the dialogue natural.\n"
        "6. Build toward a high-stakes moment or realization.\n"
        "7. End with a powerful, resonant conclusion.\n\n"
        "Format:\n"
        "Title: [Your Creative Title]\n"
        "[Story Content]"
    )
    return prompt


async def generate_story_from_image_bytes_and_prompt(
        image_bytes: bytes,
        prompt: str
) -> Tuple[str, str]:
    """
    Processes image bytes, sends it to the Gemini API with a prompt,
    and returns a tuple of (title, story_content).
    """
    try:
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
                full_text = response.text

                # Parse the response to separate Title and Content
                lines = full_text.strip().split('\n')
                title = "Untitled Story"
                story_content = full_text

                if lines:
                    first_line = lines[0].strip()
                    
                    # Check if the first line looks like a title
                    if first_line.lower().startswith("title:") or "**title:" in first_line.lower():
                        # Remove "Title:" prefix (case insensitive)
                        title = re.sub(r'(?i)^[\*]*title:[\*]*', '', first_line).strip()
                        # Remove any remaining bold markers
                        title = title.replace('**', '').strip()
                        
                        story_content = "\n".join(lines[1:]).strip()
                    else:
                        # If the model didn't follow format strictly, try to use the first line as title
                        # if it's short enough
                        if len(first_line) < 100:
                            title = first_line.replace('**', '').strip()
                            story_content = "\n".join(lines[1:]).strip()

                return title, story_content

            except google_exceptions.ResourceExhausted:
                # If we hit a rate limit, wait and try again
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)  # Exponential backoff: 2s, 4s, 8s
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
        
        # This part is unreachable due to the loop logic raising exceptions,
        # but we add a return to satisfy static analysis tools.
        raise HTTPException(status_code=500, detail="Failed to generate story after retries.")

    except HTTPException as he:
        raise he
    except Exception as e:
        # Handle potential API errors or other issues
        print(f"An error occurred during story generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate story.")
