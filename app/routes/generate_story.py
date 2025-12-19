from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict

from app.db.database import SessionLocal
from app.core.security import get_current_user
from app.schemas.user_schema import UserResponse
from app.core.validators import validate_story_input
from app.services.story_generator_service import (
    create_story_prompt,
    generate_story_from_image_and_prompt,
)

router = APIRouter(prefix="/generate-story", tags=["Generate Story"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/generate")
async def generate_story_endpoint(
    validated_data: Dict = Depends(validate_story_input),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Receives an image and story metadata, validates them,
    creates a prompt, and returns a generated story.
    """
    # 1. Data is already validated by the `validate_story_input` dependency.
    file = validated_data["file"]
    genre = validated_data["genre"]
    tone = validated_data["tone"]
    language = validated_data["language"]

    # 2. Create the prompt using the service
    prompt = create_story_prompt(genre, tone, language)

    # 3. Generate the story using the service (currently mocked)
    story = await generate_story_from_image_and_prompt(file, prompt)

    # 4. Return the final result
    return {
        "statusCode": 200,
        "story": story,
        "metadata": {
            "genre": genre,
            "tone": tone,
            "language": language,
            "filename": file.filename,
        },
        "user": current_user.email
    }
