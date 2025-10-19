from fastapi import APIRouter, Query
from typing import List, Optional
from pydantic import BaseModel
from app.services.search_engine import search

class SearchRequest(BaseModel):
    query: str

    # Textual weights
    text_weight: float = 0.1
    shingle_weight: float = 0.1
    trigram_weight: float = 0.1

    # Variant textual weights
    variant_text_weight: float = 0.25
    variant_shingle_weight: float = 0.25
    variant_trigram_weight: float = 0.25

    # Semantic weights
    semantic_weight: float = 0.9
    variant_semantic_weight: float = 0.45

    # Filters
    books: Optional[List[str]] = None
    sources: Optional[List[str]] = None

    # Pagination
    size: int = 50

    # Score stats
    score_stats: bool = False


router = APIRouter()
@router.post("/api/search/{language}")
def search_endpoint(language: str, body: SearchRequest):
    return search(
        language=language,
        query_text=body.query,
        text_weight=body.text_weight,
        shingle_weight=body.shingle_weight,
        trigram_weight=body.trigram_weight,
        variant_text_weight=body.variant_text_weight,
        variant_shingle_weight=body.variant_shingle_weight,
        variant_trigram_weight=body.variant_trigram_weight,
        semantic_weight=body.semantic_weight,
        variant_semantic_weight=body.variant_semantic_weight,
        books=body.books,
        sources=body.sources,
        size=body.size,
        score_stats=body.score_stats
    )