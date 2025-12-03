import traceback
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from app.routes import auth, generate_story
from app.db.database import Base, engine

# Create tables
Base.metadata.create_all(bind=engine)

# ----- Firebase Admin Initialization -----
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("app/firebase/serviceAccountKey.json")  # Update path if needed
firebase_admin.initialize_app(cred)
# -----------------------------------------

app = FastAPI()

# Include routers
app.include_router(auth.router)
app.include_router(generate_story.router)


# Global exception handler
@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
