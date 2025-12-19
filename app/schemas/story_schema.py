from pydantic import BaseModel

class StoryMetadata(BaseModel):
    genre: str
    tone: str
    language: str
