from fastapi import UploadFile, HTTPException, Form

# Allowed image types
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def validate_story_input(
    file: UploadFile,
    genre: str = Form(...),
    tone: str = Form(...),
    language: str = Form(...)
):
    """
    Dependency (Middleware) to validate story generation input.
    """
    # 1. Validate Image Type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid image type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )

    # 2. Validate File Size (Optional, requires reading the file which moves the cursor)
    # For now, we'll skip strict size check to avoid consuming the stream before the logic.

    # 3. Validate Metadata
    if not genre.strip():
        raise HTTPException(status_code=400, detail="Genre cannot be empty")
    
    if not tone.strip():
        raise HTTPException(status_code=400, detail="Tone cannot be empty")
        
    if not language.strip():
        raise HTTPException(status_code=400, detail="Language cannot be empty")

    return {
        "file": file,
        "genre": genre,
        "tone": tone,
        "language": language
    }
