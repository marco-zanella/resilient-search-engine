import logging
from fastapi import APIRouter, HTTPException
from psycopg2.extras import RealDictCursor
from app.services.db import get_connection
from app.models.comment import CommentCreate, CommentUpdate, Comment

router = APIRouter(prefix="/api", tags=["Comments"])
logger = logging.getLogger(__name__)


@router.post("/result-collections/{collection_id}/comments")
def create_comment_for_collection(collection_id: int, comment: CommentCreate):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO comment (result_collection_id, content, author)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (collection_id, comment.content, comment.author))
            comment_id = cursor.fetchone()[0]
            conn.commit()
            return {"id": comment_id}


@router.post("/result-collections/{collection_id}/cases/{case_id}/comments")
def create_comment_for_case(collection_id: int, case_id: int, comment: CommentCreate):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO comment (result_case_id, content, author)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (case_id, comment.content, comment.author))
            comment_id = cursor.fetchone()[0]
            conn.commit()
            return {"id": comment_id}


@router.get("/result-collections/{collection_id}/comments", response_model=list[Comment])
def get_comments_for_collection(collection_id: int):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM comment WHERE result_collection_id = %s ORDER BY created_at ASC
            """, (collection_id,))
            return cursor.fetchall()


@router.get("/result-collections/{collection_id}/cases/{case_id}/comments", response_model=list[Comment])
def get_comments_for_case(collection_id: int, case_id: int):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM comment WHERE result_case_id = %s ORDER BY created_at ASC
            """, (case_id,))
            return cursor.fetchall()


@router.put("/comments/{comment_id}")
def update_comment(comment_id: int, comment: CommentUpdate):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE comment SET content = %s, author = %s
                WHERE id = %s
            """, (comment.content, comment.author, comment_id))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Comment not found")
            conn.commit()
            return {"status": "updated"}


@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM comment WHERE id = %s", (comment_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Comment not found")
            conn.commit()
            return {"status": "deleted"}