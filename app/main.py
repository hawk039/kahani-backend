import traceback

from fastapi import FastAPI
from starlette.responses import JSONResponse

from app.routes import auth
from app.db.database import Base, engine
import traceback

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)


@app.exception_handler(Exception)
async def all_exception_handler(request, Exception):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
