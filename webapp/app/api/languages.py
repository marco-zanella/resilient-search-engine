from fastapi import APIRouter
from app.services.index_manager import SUPPORTED_LANGUAGES

router = APIRouter()

@router.get("/api/languages")
def get_languages():
    return SUPPORTED_LANGUAGES