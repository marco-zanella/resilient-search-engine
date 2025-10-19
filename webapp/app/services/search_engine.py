from typing import List, Optional
import logging
from elasticsearch import Elasticsearch
import os
from app.services.embedder import query_embedding

logger = logging.getLogger(__name__)
es = Elasticsearch(os.getenv("ELASTIC_URL", "http://localhost:9200"))

def compute_filters(
    books: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
):
    filters = []
    if books:
        filters.append({"terms": {"book": books}})
    if sources:
        filters.append({"terms": {"source": sources}})
    return filters


def compute_language_query(
    query_text: str,
    filters: List = [],
    text_weight: float = 0.0,
    shingle_weight: float = 0.0,
    trigram_weight: float = 0.0,
    variant_text_weight: float = 0.0,
    variant_shingle_weight: float = 0.0,
    variant_trigram_weight: float = 0.0,
):
    should_match = []

    fields = []
    if text_weight:
        fields.append(f"content.text^{text_weight}")
    if shingle_weight:
        fields.append(f"content.shingle^{shingle_weight}")
    if trigram_weight:
        fields.append(f"content.trigram^{trigram_weight}")
    if fields:
        should_match.append({
            "multi_match": {
                "query": query_text,
                "fields": fields,
            }
        })
    
    variant_fields = []
    if variant_text_weight:
        variant_fields.append(f"variant.content.text^{variant_text_weight}")
    if variant_shingle_weight:
        variant_fields.append(f"variant.content.shingle^{variant_shingle_weight}")
    if variant_trigram_weight:
        variant_fields.append(f"variant.content.trigram^{variant_trigram_weight}")
    if variant_fields:
        should_match.append({
            "nested": {
                "path": "variant",
                "query": {
                    "multi_match": {
                        "query": query_text,
                        "fields": variant_fields,
                    }
                },
                "score_mode": "max"
            }
        })
    
    if not should_match:
        should_match = [{"match_none": {}}]
    
    return {
        "bool": {
            "should": should_match,
            "filter": filters,
            "minimum_should_match": 1,
        }
    }


def compute_semantic_query(
        embedding: List,
        filters: List,
        semantic_weight: float,
        variant_semantic_weight: float,
        k: int = 11,
):
    semantic_query = []
    if semantic_weight > 0:
        semantic_query.append({
            "field": "embedding",
            "query_vector": embedding,
            "k": k,
            "num_candidates": 10000,
            "boost": semantic_weight,
            "filter": filters
        })
    if variant_semantic_weight > 0:
        semantic_query.append({
            "field": "variant.embedding",
            "query_vector": embedding,
            "k": k,
            "num_candidates": 10000,
            "boost": variant_semantic_weight,
            "filter": filters
        })
    return semantic_query


def compute_aggs(score_stats):
    aggs = {
        "unfiltered": {
            "global": {},
            "aggs": {
                "by_source": {
                    "terms": {
                        "field": "source",
                        "size": 1000,
                    },
                    "aggs": {
                        "by_book": {
                            "terms": {
                                "field": "book",
                                "size": 1000,
                            },
                        }
                    }
                },
                "by_book": {
                    "terms": {
                        "field": "book",
                        "size": 1000,
                    }
                }
            }
        },
    }
    if score_stats:
        aggs["score_stats"] = {
            "extended_stats": {
                "script": "_score",
            }
        }
        aggs["score_percentiles"] = {
            "percentiles": {
                "script": "_score",
                "percents": [0.1, 1, 5, 25, 50, 75, 95, 99, 99.9, 99.95, 99.99],
            }
        }
    return aggs


def parse_result(hit):
    return {
        "id": hit["_source"]["id"],
        "type": hit["_source"]["type"],
        "source": hit["_source"]["source"],
        "book": hit["_source"]["book"],
        "chapter": hit["_source"]["chapter"],
        "verse": hit["_source"]["verse"],
        "score": hit["_score"],
        "content": hit["_source"]["content"],
        "variant": [{
            "source": variant["source"],
            "content": variant["content"],
        } for variant in hit["_source"].get("variant", [])],
    }


def search(
    language: str,
    query_text: str,
    text_weight: float = 0.0,
    shingle_weight: float = 0.0,
    trigram_weight: float = 0.0,
    variant_text_weight: float = 0.0,
    variant_shingle_weight: float = 0.0,
    variant_trigram_weight: float = 0.0,
    semantic_weight: float = 1.0,
    variant_semantic_weight: float = 0.5,
    books: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    size: int = 50,
    score_stats: bool = False,
):
    index = language
    logger.info(f"Incoming query for '{query_text}' on '{language}'")
    embedding = query_embedding(language, query_text)
    filters = compute_filters(books, sources)
    syntactic_query = compute_language_query(
        query_text, filters,
        text_weight, shingle_weight, trigram_weight,
        variant_text_weight, variant_shingle_weight, variant_trigram_weight
    )
    semantic_query = compute_semantic_query(embedding, filters, semantic_weight, variant_semantic_weight)
    aggs = compute_aggs(score_stats)

    try:
        response = es.search(
            index=index,
            query=syntactic_query,
            knn=semantic_query,
            aggs=aggs,
            track_total_hits=True,
            size=size,
        )
        result =  {
            "time": response["took"],
            "count": response["hits"]["total"]["value"],
            "results": [parse_result(hit) for hit in response["hits"]["hits"]],
            "stats": response["aggregations"]
        }
    except Exception as e:
        logger.error(str(e))
        result =  {
            "time": 0,
            "count": 0,
            "results": [],
            "stats": []
        }
    
    return result