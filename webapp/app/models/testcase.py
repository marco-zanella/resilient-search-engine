from pydantic import BaseModel
from typing import List, Optional

class TestCase(BaseModel):
    source: Optional[str] = None
    content: str
    context: Optional[str] = None
    language: str
    target: str
    tags: List[str] = []

class TestCaseWithID(TestCase):
    id: int