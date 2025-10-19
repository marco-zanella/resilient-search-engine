from fastapi import APIRouter
from app.services.elastic import ping_elasticsearch

router = APIRouter()

@router.get("/api/health")
def health_check():
    if ping_elasticsearch():
        return {"status": "ok", "elasticsearch": "connected"}
    return {"status": "error", "elasticsearch": "unreachable"}