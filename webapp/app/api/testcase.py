from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models.testcase import TestCase, TestCaseWithID
from app.services.db import get_connection

router = APIRouter()

@router.post("/api/test-cases", response_model=TestCaseWithID)
def create_test_case(test_case: TestCase):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO test_case (source, content, context, language, target, tags)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                test_case.source,
                test_case.content,
                test_case.context,
                test_case.language,
                test_case.target,
                test_case.tags,
            ))
            new_id = cur.fetchone()[0]
    return TestCaseWithID(id=new_id, **test_case.dict())


@router.get("/api/test-cases", response_model=List[TestCaseWithID])
def list_test_cases(tag: Optional[str] = None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if tag:
                cur.execute("""
                    SELECT * FROM test_case
                    WHERE %s = ANY (tags)
                    ORDER BY id DESC
                """, (tag,))
            else:
                cur.execute("SELECT * FROM test_case ORDER BY id DESC")
            rows = cur.fetchall()
    return [TestCaseWithID(
        id=row[0], source=row[1], content=row[2],
        context=row[3], language=row[4], target=row[5], tags=row[6]
    ) for row in rows]


@router.get("/api/test-cases/{test_case_id}", response_model=TestCaseWithID)
def get_test_case(test_case_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, source, content, context, language, target, tags FROM test_case WHERE id = %s", (test_case_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Test case not found")
    return TestCaseWithID(
        id=row[0], source=row[1], content=row[2],
        context=row[3], language=row[4], target=row[5], tags=row[6]
    )


@router.put("/api/test-cases/{test_case_id}", response_model=TestCaseWithID)
def update_test_case(test_case_id: int, test_case: TestCase):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE test_case
                SET source = %s, content = %s, context = %s,
                    language = %s, target = %s, tags = %s
                WHERE id = %s
            """, (
                test_case.source, test_case.content, test_case.context,
                test_case.language, test_case.target, test_case.tags, test_case_id
            ))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Test case not found")
    return TestCaseWithID(id=test_case_id, **test_case.dict())


@router.delete("/api/test-cases/{test_case_id}")
def delete_test_case(test_case_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM test_case WHERE id = %s", (test_case_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Test case not found")
    return {"message": f"Test case {test_case_id} deleted successfully"}