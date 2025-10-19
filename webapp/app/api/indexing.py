from fastapi import APIRouter, HTTPException
from app.services.index_manager import SUPPORTED_LANGUAGES, create_index, delete_index, reload_index

router = APIRouter()

@router.post("/api/indices/{language}/reload")
def reload_language_index(language: str):
    return reload_index(language)

@router.post("/api/indices/reload")
def reload_all_indices():
    results = {}
    for lang in SUPPORTED_LANGUAGES:
        results[lang] = reload_index(lang)
    return results

@router.post("/api/indices/{language}")
def create_language_index(language: str):
    return create_index(language)
    
@router.post("/api/indices")
def create_indices():
    results = {}
    for lang in SUPPORTED_LANGUAGES:
        results[lang] = create_index(lang)
    return results

@router.delete("/api/indices/{language}")
def delete_language_index(language: str):
    return delete_index(language)

@router.delete("/api/indices")
def delete_all_indices():
    results = {}
    for lang in SUPPORTED_LANGUAGES:
        results[lang] = delete_index(lang)
    return results