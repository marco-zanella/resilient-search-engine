from fastapi import APIRouter, HTTPException
from typing import List
import logging
from psycopg2.extras import Json
from psycopg2.extras import RealDictCursor
from app.models.testcollection import TestCollection, TestCollectionWithID
from app.services.db import get_connection
from app.services.search_engine import search

router = APIRouter(prefix="/api/test-collections", tags=["Test Collections"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=TestCollectionWithID)
def create_collection(collection: TestCollection):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO test_collection (name, description, weights, sources, books)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (collection.name, collection.description, Json(collection.weights), collection.sources, collection.books)
    )
    new_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return TestCollectionWithID(id=new_id, **collection.dict())



@router.get("/", response_model=List[TestCollectionWithID])
def list_collections():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_collection ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [TestCollectionWithID(**dict(zip([desc[0] for desc in cursor.description], row))) for row in rows]


@router.get("/{collection_id}", response_model=TestCollectionWithID)
def get_collection(collection_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_collection WHERE id = %s", (collection_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Collection not found")
    return TestCollectionWithID(**dict(zip([desc[0] for desc in cursor.description], row)))


@router.put("/{collection_id}", response_model=TestCollectionWithID)
def update_collection(collection_id: int, collection: TestCollection):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE test_collection
        SET name = %s, description = %s, weights = %s, sources = %s, books = %s
        WHERE id = %s
        """,
        (collection.name, collection.description, Json(collection.weights), collection.sources, collection.books, collection_id)
    )
    conn.commit()
    conn.close()
    return TestCollectionWithID(id=collection_id, **collection.dict())


@router.delete("/{collection_id}")
def delete_collection(collection_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM test_collection WHERE id = %s", (collection_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}


@router.post("/{collection_id}/tests/{test_id}")
def add_test_case_to_collection(collection_id: int, test_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO test_collection_membership (test_case_id, test_collection_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        """,
        (test_id, collection_id)
    )
    conn.commit()
    conn.close()
    return {"status": "added"}


@router.get("/{collection_id}/tests")
async def get_test_cases_in_collection(collection_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT test_case_id FROM test_collection_membership WHERE test_collection_id = %s",
        (collection_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


@router.delete("/{collection_id}/tests/{test_id}")
def remove_test_case_from_collection(collection_id: int, test_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM test_collection_membership
        WHERE test_case_id = %s AND test_collection_id = %s
        """,
        (test_id, collection_id)
    )
    conn.commit()
    conn.close()
    return {"status": "removed"}


@router.post("/{collection_id}/run")
def run_collection(collection_id: int):
    logger.info(f"Running tests for collection {collection_id}")
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # Fetch collection configuration
            logger.info(f"Fetching configuration for collection {collection_id}")
            cursor.execute("SELECT weights, sources, books FROM test_collection WHERE id = %s", (collection_id,))
            collection = cursor.fetchone()
            if not collection:
                raise HTTPException(status_code=404, detail="Test collection not found")
            weights = collection[0]
            sources = collection[1]
            books = collection[2]

            # Fetch test cases
            logger.info(f"Fetching test cases for collection {collection_id}")
            cursor.execute("""
                SELECT tc.id, tc.content, tc.language, tc.target FROM test_case tc
                JOIN test_collection_membership tcm ON tc.id = tcm.test_case_id
                WHERE tcm.test_collection_id = %s
            """, (collection_id,))
            test_cases = cursor.fetchall()

            # Insert collection result
            logger.info(f"Creating collection result for collection {collection_id}")
            cursor.execute("""
                INSERT INTO result_collection (test_collection_id, weights, sources, books)
                VALUES (%s, %s, %s, %s) RETURNING id
            """, (collection_id, Json(weights), sources, books))
            collection_result_id = cursor.fetchone()[0]
            logger.info(f"Created collection result with id {collection_result_id} for collection {collection_id}")

            # Run tests
            for test_case in test_cases:
                logger.info(f"Running test case {test_case[0]} for collection {collection_id}")
                result = search(
                    test_case[2],
                    test_case[1],
                    text_weight=weights.get("text", 0.0),
                    shingle_weight=weights.get("shingle", 0.0),
                    trigram_weight=weights.get("trigram", 0.0),
                    variant_text_weight=weights.get("variantText", 0.0),
                    variant_shingle_weight=weights.get("variantShingle", 0.0),
                    variant_trigram_weight=weights.get("variantTrigram", 0.0),
                    semantic_weight=weights.get("semantic", 0.0),
                    variant_semantic_weight=weights.get("variantSemantic", 0.0),
                    sources=sources,
                    books=books,
                    size=50,
                    score_stats=True
                )

                # Find rank of expected target
                rank = -1
                for idx, hit in enumerate(result["results"]):
                    if hit["id"] == test_case[3]:
                        rank = idx + 1
                        break
                
                # Insert case result
                logger.info(f"Creating case result for test case {test_case[0]}")
                cursor.execute("""
                    INSERT INTO result_case (test_case_id, result_collection_id, rank_of_expected, results)
                    VALUES (%s, %s, %s, %s)
                """, (test_case[0], collection_result_id, rank, Json(result)))
    return {"resultConnectionId": collection_result_id}


@router.get("/{collection_id}/results")
def get_results_for_collection(collection_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Metadata
            cursor.execute("SELECT id, name, description FROM test_collection WHERE id = %s", (collection_id,))
            meta = cursor.fetchone()

            # Retrieve statistics for a result collection
            def get_statistics(result_collection_id):
                cursor.execute("SELECT rank_of_expected FROM result_case WHERE result_collection_id = %s", (result_collection_id,))
                ranks = [row["rank_of_expected"] for row in cursor.fetchall()]
                found_ranks = [r for r in ranks if r > 0]
                total = len(ranks)
                return {
                    "recallAt10": sum(1 for r in found_ranks if r <= 10) / total if total > 0 else 0.0,
                    "mrr": sum(1 / r for r in found_ranks) / total if total > 0 else 0.0,
                }
            
            # Retrieve result collections
            cursor.execute("SELECT id, timestamp FROM result_collection WHERE test_collection_id = %s ORDER BY timestamp DESC", (collection_id,))
            results = []
            for collection in cursor.fetchall():
                id = collection["id"]
                timestamp = collection["timestamp"]
                statistics = get_statistics(id)
                results.append({
                    "id": id,
                    "timestamp": timestamp,
                    "recallAt10": statistics["recallAt10"],
                    "mrr": statistics["mrr"]
                })
            return {
                "metadata": meta,
                "results": results
            }
