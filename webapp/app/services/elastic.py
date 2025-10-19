from elasticsearch import Elasticsearch
import os
import logging

SUPPORTED_LANGUAGES = ["greek"] #, "latin", "arabic"]

logger = logging.getLogger(__name__)
es = Elasticsearch(os.getenv("ELASTIC_URL", "http://localhost:9200"))

def ping_elasticsearch():
    try:
        return es.ping()
    except Exception as e:
        logger.warning(f"Elasticsearch connection error: {e}")
        return False