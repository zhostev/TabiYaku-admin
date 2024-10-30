# api/v1/recipes/schemas.py
from pydantic import BaseModel, HttpUrl
from typing import Optional

class RecipeRecognitionRequest(BaseModel):
    image_url: HttpUrl

class RecipeRecognitionResponse(BaseModel):
    id: int
    recognized_text: str
    created_at: str

class RecipeRecognitionQueryResponse(BaseModel):
    id: int
    image_url: HttpUrl
    recognized_text: str
    created_at: str