from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import Dict, Optional
from datetime import datetime

from app.db.database import SessionLocal
from app.core.security import get_current_user
from app.schemas.user_schema import UserResponse
from app.core.validators import validate_story_input
from app.services.story_generator_service import (
    create_story_prompt,
    generate_story_from_image_bytes_and_prompt,
)
from app.core.s3_service import upload_file_bytes_to_s3
from app.models.story import Story

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
    uploads the image to S3, creates a prompt, generates a story with a title, 
    saves it to the DB, and returns the saved record.
    """
    # 1. Data is already validated by the `validate_story_input` dependency.
    file = validated_data["file"]
    genre = validated_data["genre"]
    tone = validated_data["tone"]
    language = validated_data["language"]

    # READ THE FILE ONCE INTO MEMORY
    file_bytes = await file.read()

    # 2. Upload image to S3 using the bytes
    image_url = await upload_file_bytes_to_s3(file_bytes, file.filename, file.content_type)

    # 3. Create the prompt using the service
    prompt = create_story_prompt(genre, tone, language)

    # 4. Generate the story using the service using the bytes
    # Now returns a tuple: (title, story_text)
    title, story_text = await generate_story_from_image_bytes_and_prompt(file_bytes, prompt)

    # 5. Save to Database
    new_story = Story(
        user_id=current_user.id,
        title=title, # Save the generated title
        content=story_text,
        genre=genre,
        tone=tone,
        language=language,
        image_filename=image_url
    )
    db.add(new_story)
    db.commit()
    db.refresh(new_story)

    # 6. Return the final result
    return {
        "statusCode": 200,
        "id": new_story.id,
        "createdAt": new_story.created_at.isoformat(),
        "title": new_story.title, # Return the title
        "story": new_story.content,
        "metadata": {
            "genre": new_story.genre,
            "tone": new_story.tone,
            "language": new_story.language,
            "image_url": new_story.image_filename,
        },
        "user": current_user.email
    }

@router.get("/my-stories")
def get_my_stories(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term for title or content"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Fetches paginated stories for the current user with optional search.
    """
    # Base query: filter by current user
    query = db.query(Story).filter(Story.user_id == current_user.id)

    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Story.title.ilike(search_term),
                Story.content.ilike(search_term),
                Story.genre.ilike(search_term)
            )
        )

    # Get total count before pagination
    total_stories = query.count()

    # Apply pagination and sorting (newest first)
    offset = (page - 1) * limit
    stories = query.order_by(desc(Story.created_at)).offset(offset).limit(limit).all()

    # Format the response
    data = []
    for story in stories:
        data.append({
            "id": story.id,
            "title": story.title,
            "story": story.content,
            "createdAt": story.created_at.isoformat(),
            "metadata": {
                "genre": story.genre,
                "tone": story.tone,
                "language": story.language,
                "image_url": story.image_filename,
            }
        })

    return {
        "statusCode": 200,
        "data": data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_stories,
            "totalPages": (total_stories + limit - 1) // limit
        }
    }
