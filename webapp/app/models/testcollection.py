from pydantic import BaseModel
from typing import Optional, List, Dict

class TestCollection(BaseModel):
    name: str
    description: Optional[str] = None
    weights: Dict[str, float] = {}
    sources: List[str] = []
    books: List[str] = []

class TestCollectionWithID(TestCollection):
    id: int

class TestCollectionMembership(BaseModel):
    test_case_id: int
    test_collection_id: int