from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CommentCreate(BaseModel):
    content: str
    author: Optional[str] = None

class CommentUpdate(BaseModel):
    content: str
    author: Optional[str] = None

class Comment(BaseModel):
    id: int
    result_collection_id: Optional[int]
    result_case_id: Optional[int]
    content: str
    author: Optional[str]
    created_at: datetime