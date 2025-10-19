from fastapi import APIRouter
from app.services.dataset_info import list_available_datasets, list_language_datasets
from app.services import data_indexer

router = APIRouter()

@router.post("/api/data")
def api_index_all():
    return data_indexer.index_all()

@router.post("/api/data/{language}")
def api_index_language(language: str):
    return data_indexer.index_language(language)

@router.post("/api/data/{language}/{dataset}")
def api_index_dataset(language: str, dataset: str):
    return data_indexer.index_dataset(language, dataset)

@router.get("/api/data")
def get_all_datasets():
    return list_available_datasets()

@router.get("/api/data/{language}")
def get_datasets_for_language(language: str):
    datasets = list_language_datasets(language)
    if not datasets:
        return {"language": language, "datasets": [], "message": "No datasets found"}
    return {"language": language, "datasets": datasets}

@router.delete("/api/data")
def api_delete_all():
    return data_indexer.delete_all()

@router.delete("/api/data/{language}")
def api_delete_language(language: str):
    return data_indexer.delete_language(language)

@router.delete("/api/data/{language}/{dataset}")
def api_delete_dataset(language: str, dataset: str):
    return data_indexer.delete_dataset(language, dataset)

@router.delete("/api/data/{language}/{dataset}/embedding")
def api_delete_embedding_cache(language: str, dataset: str):
    return data_indexer.delete_embedded_documents(language, dataset)