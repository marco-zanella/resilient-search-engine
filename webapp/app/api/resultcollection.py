from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import io
import csv
import logging
import zipfile
from psycopg2.extras import RealDictCursor
from app.services.db import get_connection

router = APIRouter(prefix="/api/result-collections", tags=["Result collections"])
logger = logging.getLogger(__name__)


@router.get("/{collection_id}")
def get_result_collection(collection_id):
    logger.info(f"Retrieving result collection {collection_id}")
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Retrieve metadata
            cursor.execute("""
                SELECT rc.id, rc.test_collection_id, tc.name, tc.description, rc.weights, rc.sources, rc.books, rc.timestamp
                FROM test_collection tc JOIN result_collection rc ON tc.id = rc.test_collection_id
                WHERE rc.id = %s
            """, (collection_id,))
            meta = cursor.fetchone()

            # Retrieve cases
            cases = get_result_cases_for_collection(collection_id)

            # Computes statistics
            logger.info("Computing statistics")
            total = len(cases)
            ranks = [case["rank_of_expected"] for case in cases]
            found_ranks = [r for r in ranks if r > 0]
            def recall_at_k(k):
                return sum(1 for r in found_ranks if r <= k) / total if total > 0 else 0.0
            def mrr():
                return sum(1 / r for r in found_ranks) / total if total > 0 else 0.0
            def mean_rank():
                return sum(found_ranks) / len(found_ranks) if found_ranks else 0.0

            return {
                "metadata": meta,
                "statistics": {
                    "total": total,
                    "recallAtK": [recall_at_k(k) for k in range(0, 51)],
                    "mrr": mrr(),
                    "meanRank": mean_rank(),
                },
                "cases": cases,
            }


@router.get("/{collection_id}/csv")
def get_result_collection_as_csv(collection_id):
    memory_zip = io.BytesIO()

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT tc.id, tc.source, tc.content, tc.target, rc.results
                FROM result_case rc JOIN test_case tc ON rc.test_case_id = tc.id
                WHERE rc.result_collection_id = %s
            """, (collection_id,))
            test_cases = cursor.fetchall()

    with zipfile.ZipFile(memory_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for index, test_case in enumerate(test_cases):
            data = []
            max_variant = 0
            for idx, result in enumerate(test_case["results"]["results"]):
                entry = {
                    "source": test_case["source"],
                    "query": test_case["content"],
                    "target": test_case["target"],
                    "position": idx + 1,
                    "found": test_case["target"] == result["id"],
                    "id": result["id"],
                    "content": result["content"],
                }
                for v_idx, variant in enumerate(result.get("variant", [])):
                    entry[f"variant_{v_idx + 1}_source"] = variant["source"]
                    entry[f"variant_{v_idx + 1}_content"] = variant["content"]
                    if v_idx + 1 > max_variant:
                        max_variant = v_idx + 1
                data.append(entry)

            fieldnames = ["source", "query", "target", "position", "found", "id", "content"]
            for i in range(1, max_variant + 1):
                fieldnames.append(f"variant_{i}_source")
                fieldnames.append(f"variant_{i}_content")

            csv_buffer = io.StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")
            zf.writestr(f"test_case_{test_case['id']}.csv", csv_bytes)

    memory_zip.seek(0)
    return StreamingResponse(
        memory_zip,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=collection_{collection_id}.zip"}
    )


@router.get("/{collection_id}/cases")
def get_result_cases_for_collection(collection_id):
    logger.info(f"Retrieving result cases for collection {collection_id}")
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT rc.id, rc.test_case_id, tc.source, tc.content, tc.language, tc.target, rc.rank_of_expected
                FROM test_case tc JOIN result_case rc ON tc.id = rc.test_case_id
                WHERE rc.result_collection_id = %s
                ORDER BY rc.id
            """, (collection_id,))
            return cursor.fetchall()


@router.get("/{collection_id}/cases/{case_id}")
def get_result_case(collection_id: int, case_id: int):
    logger.info(f"Retrieving result case {case_id} for collection {collection_id}")
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT tc.source, tc.content, tc.context, tc.language, tc.target, rc.rank_of_expected, rc.results, rc.timestamp
                FROM test_case tc JOIN result_case rc ON tc.id = rc.test_case_id
                WHERE rc.id = %s
            """, (case_id,))
            return cursor.fetchone()
