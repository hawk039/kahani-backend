from pydantic import BaseModel, Field
from typing import Optional

class StoryUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, description="The new title of the story")
    story: Optional[str] = Field(None, min_length=10, description="The new content of the story")

    class Config:
        from_attributes = True
