from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def read_index():
    with open("frontend/index.html") as f:
        return HTMLResponse(content=f.read())

@router.get("/test-cases", response_class=HTMLResponse)
async def read_test():
    with open("frontend/test.html") as f:
        return HTMLResponse(content=f.read())

@router.get("/test-collections", response_class=HTMLResponse)
async def read_test():
    with open("frontend/test-collections.html") as f:
        return HTMLResponse(content=f.read())

@router.get("/test-collections/{collection_id}/results", response_class=HTMLResponse)
async def serve_results_page(collection_id: int):
    with open("frontend/result-collections.html") as f:
        return HTMLResponse(content=f.read())

@router.get("/test-collections/{test_collection_id}/results/{result_collection_id}", response_class=HTMLResponse)
async def serve_results_page(test_collection_id: int, result_collection_id: int):
    with open("frontend/result-collection.html") as f:
        return HTMLResponse(content=f.read())

@router.get("/test-collections/{test_collection_id}/results/{result_collection_id}/cases/{case_id}", response_class=HTMLResponse)
async def serve_results_page(test_collection_id: int, result_collection_id: int, case_id: int):
    with open("frontend/result-case.html") as f:
        return HTMLResponse(content=f.read())

@router.get("/admin", response_class=HTMLResponse)
async def read_index():
    with open("frontend/admin.html") as f:
        return HTMLResponse(content=f.read())