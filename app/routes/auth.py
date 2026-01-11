from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Callable

from app.db.database import SessionLocal
from app.schemas.user_schema import UserCreate, UserResponse, ForgetPassword
from app.core.security import (
    verify_password,
    create_access_token,
    hash_password,
    get_current_user,
    oauth2_scheme,
)
from app.services.token_blacklist_service import blacklist_token
from app.core.s3_service import upload_file_bytes_to_s3
from app.models.user import User # Import User model
import firebase_admin
from firebase_admin import auth as firebase_auth

from app.services.user_queries import (
    get_user_by_email_query,
    create_user_query,
    create_user_with_google_query,
)


# Custom APIRoute class to handle exceptions for this router only
class AuthRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request):
            try:
                return await original_route_handler(request)
            except HTTPException as exc:
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"statusCode": exc.status_code, "detail": exc.detail},
                )

        return custom_route_handler


# Use the custom route class in the router
router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    route_class=AuthRoute
)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SignUpResponse(BaseModel):
    statusCode: int
    user: UserResponse
    access_token: str


# -------------------------
# Normal email/password signup
# -------------------------
@router.post("/signup", response_model=SignUpResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email_query(db, user.email):
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = create_user_query(db, user)
    token = create_access_token({"sub": new_user.email})
    return {
        "statusCode": 200,
        "user": new_user,
        "access_token": token,
    }


# -------------------------
# Login
# -------------------------
@router.post("/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email_query(db, user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token({"sub": user.email})
    return {"statusCode": 200, "access_token": token}


# -------------------------
# Forgot password
# -------------------------
@router.post("/fpassword")
def fpassword(payload: ForgetPassword, db: Session = Depends(get_db)):
    db_user = get_user_by_email_query(db, payload.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_pw = hash_password(payload.new_password)
    db_user.hashed_password = hashed_pw
    db.commit()
    db.refresh(db_user)
    return {"statusCode": 200, "message": "Password updated successfully"}


# -------------------------
# Logout
# -------------------------
@router.post("/logout")
def logout(
        token: str = Depends(oauth2_scheme),
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db),
):
    blacklist_token(db, token)
    return {"statusCode": 200, "message": "Logged out successfully"}


# -------------------------
# Google Authentication
# -------------------------
class GoogleUserCreate(BaseModel):
    uid: str
    email: str
    token: str


@router.post("/google-signup", response_model=SignUpResponse)
def google_signup(user: GoogleUserCreate, db: Session = Depends(get_db)):
    try:
        decoded_token = firebase_auth.verify_id_token(user.token)
        if decoded_token["uid"] != user.uid:
            raise HTTPException(status_code=400, detail="UID mismatch")

        if get_user_by_email_query(db, user.email):
            raise HTTPException(status_code=400, detail="Email already exists")

        new_user = create_user_with_google_query(db, user)
        token = create_access_token({"sub": new_user.email})
        return {
            "statusCode": 200,
            "user": new_user,
            "access_token": token,
        }

    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Expired Firebase token")
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/google-signin")
def google_signin(user: GoogleUserCreate, db: Session = Depends(get_db)):
    try:
        decoded_token = firebase_auth.verify_id_token(user.token)
        if decoded_token["uid"] != user.uid:
            raise HTTPException(status_code=400, detail="UID mismatch")

        existing_user = get_user_by_email_query(db, user.email)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found. Please sign up first.")

        token = create_access_token({"sub": existing_user.email})
        return {"statusCode": 200, "access_token": token}

    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Expired Firebase token")
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------
# Update Avatar
# -------------------------
@router.put("/update-avatar")
async def update_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Updates the current user's avatar.
    Uploads the image to S3 and saves the URL to the database.
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Read file bytes
        file_bytes = await file.read()
        
        # Upload to S3
        avatar_url = await upload_file_bytes_to_s3(file_bytes, file.filename, file.content_type)
        
        # Re-fetch user from the current session to ensure persistence
        user_to_update = db.query(User).filter(User.id == current_user.id).first()
        
        if not user_to_update:
            raise HTTPException(status_code=404, detail="User not found")

        # Update user record
        user_to_update.avatar_url = avatar_url
        db.commit()
        db.refresh(user_to_update)
        
        return {
            "statusCode": 200,
            "message": "Avatar updated successfully",
            "user": {
                "id": user_to_update.id,
                "email": user_to_update.email,
                "avatar_url": user_to_update.avatar_url
            }
        }
        
    except Exception as e:
        # Print error for debugging
        print(f"Error updating avatar: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update avatar: {str(e)}")
