import logging
from sentence_transformers import SentenceTransformer
from app.services.retriever import SentenceTransformerAdapter

logger = logging.getLogger(__name__)
embedding_models = {
    "greek": {
        "encoder": SentenceTransformer('bowphs/SPhilBerta'),
        "index_prefix": "",
        "index_suffix": "",
        "query_prefix": "",
        "query_suffix": "",
    },
    "latin": {
        "encoder": SentenceTransformerAdapter('itserr/LaBERTa-W_VULG-S_VL-Synt', 'cuda'),
        "index_prefix": "",
        "index_suffix": "",
        "query_prefix": "",
        "query_suffix": "",
    }
}

def index_embedding(language, text):
    if language not in embedding_models:
        logger.warning(f"No embedding model for language {language}")
        return []
    model = embedding_models[language]
    text = model["index_prefix"] + text + model["index_suffix"]
    return model["encoder"].encode(text).tolist()

def query_embedding(language, text):
    if language not in embedding_models:
        logger.warning(f"No embedding model for language {language}")
        return []
    model = embedding_models[language]
    text = model["query_prefix"] + text + model["query_suffix"]
    return model["encoder"].encode(text).tolist()