from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.schemas.story_schema import StoryMetadata
from app.core.security import get_current_user
from app.schemas.user_schema import UserResponse

# We will create these modules in the next steps
# from app.services.image_service import save_image_to_db
# from app.schemas.image_schema import ImageResponse

router = APIRouter(prefix="/generate-story", tags=["Generate Story"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Receives an image, saves it to the database.
    """
    # Placeholder for the actual implementation
    # image = save_image_to_db(db, file)
    # return image
    return {"filename": file.filename, "content_type": file.content_type, "user": current_user.email}


@router.post("/metadata")
async def receive_metadata(
    metadata: StoryMetadata,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Receives story metadata (genre and tone).
    """
    # For now, just return the received data
    return {"genre": metadata.genre, "tone": metadata.tone, "user": current_user.email}
