from elasticsearch import Elasticsearch, helpers
from pathlib import Path
import json
import logging
import os
from app.services.embedder import index_embedding

DATA_DIR = Path("assets/datasets")
CACHE_DIR = Path("cache/embedded_documents")

logger = logging.getLogger(__name__)
es = Elasticsearch(os.getenv("ELASTIC_URL", "http://localhost:9200"))


def get_embedded_documents(language: str, dataset_name: str, dataset: list[dict]) -> dict:
    cache_language_path = CACHE_DIR / language
    path = cache_language_path / f"{dataset_name}.json"
    os.makedirs(cache_language_path, exist_ok=True)
    logger.info(f"Retrieving embedded dataset for {dataset_name}")

    # Read and return embedded dataset if it already exists
    if path.exists():
        logger.info(f"Embbeded dataset found in {path}: returning it")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Compute, store and return embedded dataset if it does not exist
    logger.info(f"Embedded dataset not found in {path}: computing embeddings")
    for document in dataset:
        document["embedding"] = index_embedding(language, document["content"])
        if "variant" in document:
            for variant in document["variant"]:
                variant["embedding"] = index_embedding(language, document["content"])
    logger.info(f"Writing embedded dataset to {path}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False)
    
    return dataset


def delete_embedded_documents(language: str, dataset: str):
    path = CACHE_DIR / language / f"{dataset}.json"
    logger.info(f"Clearing embedding cache at {path}")
    path.unlink(missing_ok=True)


def index_dataset(language: str, dataset: str) -> dict:
    path = DATA_DIR / language / f"{dataset}.json"
    logger.info(f"Indexing {dataset}")
    index = language

    if not path.exists():
        logger.warning(f"Dataset {dataset} does not exist")
        return {"success": False, "message": f"{dataset} not found for {language}"}

    with path.open(encoding="utf-8") as f:
        docs = json.load(f)
    embedded_docs = get_embedded_documents(language, dataset, docs)

    logger.info("Sending embedded documents")
    actions = [{"_index": index, "_id": doc["id"], "_source": doc} for doc in embedded_docs]
    try:
        helpers.bulk(es, actions)
    except helpers.BulkIndexError as e:
        for error in e.errors:
            logger.error(error)

    logger.info(f"Dataset {dataset} indexed")
    return {"success": True, "message": f"Indexed {len(embedded_docs)} docs from {dataset}"}


def index_language(language: str) -> dict:
    logger.info(f"Indexing every dataset for language {language}")
    dataset_dir = DATA_DIR / language
    if not dataset_dir.exists():
        return {"success": False, "message": f"No data for {language}"}

    results = {}
    for f in dataset_dir.glob("*.json"):
        dataset = f.stem
        results[dataset] = index_dataset(language, dataset)
    return results


def index_all() -> dict:
    logger.info(f"Indexing every dataset")
    results = {}
    for lang_dir in DATA_DIR.iterdir():
        if lang_dir.is_dir():
            lang = lang_dir.name
            results[lang] = index_language(lang)
    return results


def delete_dataset(language: str, dataset: str) -> dict:
    logger.info(f"Removing {dataset}")
    index = language
    query = {"query": {"match": {"source": dataset}}}
    es.delete_by_query(index=index, body=query)
    return {"success": True, "message": f"Deleted {dataset} from {index}"}


def delete_language(language: str) -> dict:
    logger.info(f"Removing every dataset for language {language}")
    index = language
    query = {"query": {"match_all": {}}}
    try:
        es.delete_by_query(index=index, body=query)
    except:
        logger.warning(f"Could not delete data from index {index}")
        return {"success": False, "message": f"Could not delete data from index {index}"}
    return {"success": True, "message": f"Deleted all docs from {index}"}


def delete_all() -> dict:
    logger.info(f"Removing every dataset")
    results = {}
    for lang_dir in DATA_DIR.iterdir():
        if lang_dir.is_dir():
            lang = lang_dir.name
            results[lang] = delete_language(lang)
    return results