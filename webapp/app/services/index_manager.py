import os
import logging
import json
from elasticsearch import Elasticsearch

SUPPORTED_LANGUAGES = ["greek", "latin"] #, "arabic"]

logger = logging.getLogger(__name__)
es = Elasticsearch(os.getenv("ELASTIC_URL", "http://localhost:9200"))

def create_index(language: str) -> dict:
    index_name = f"{language}"
    logger.info(f"Creating index for {language}")

    if language not in SUPPORTED_LANGUAGES:
        logger.info(f"Language {language} is not supported")
        return {"success": False, "error": f"Unsupported language '{language}'"}

    if es.indices.exists(index=index_name):
        logger.info(f"Index for {language} already exisys")
        return {"success": True, "message": f"Index '{index_name}' already exists."}

    with open("assets/elasticsearch/mappings.json", "r", encoding="UTF-8") as f:
        mappings = json.load(f)
    with open(f"assets/elasticsearch/settings-{language.lower()}.json", "r", encoding="UTF-8") as f:
        settings = json.load(f)
    es.indices.create(index=index_name, mappings=mappings, settings=settings)
    logger.info(f"Index for {language} created")
    return {"success": True, "message": f"Index '{index_name}' created."}


def delete_index(language: str) -> dict:
    index_name = f"{language}"
    logger.info(f"Deleting index for {language}")
    if not es.indices.exists(index=index_name):
        logger.info(f"Index for {language} does not exist")
        return {"success": False, "message": f"Index '{index_name}' does not exist."}
    es.indices.delete(index=index_name)
    logger.info(f"Index for {language} deleted")
    return {"success": True, "message": f"Index '{index_name}' deleted."}


def reload_index(language: str) -> dict:
    logger.info(f"Reloading index for {language}")
    delete_result = delete_index(language)
    if not delete_result["success"] and "does not exist" not in delete_result["message"]:
        return delete_result
    return create_index(language)