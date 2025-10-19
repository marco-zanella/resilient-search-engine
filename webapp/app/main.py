from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import health, log, languages, indexing, dataset, search, frontend, testcase, testcollection, resultcollection, comment
from app.logging_config import setup_logging

setup_logging()

app = FastAPI(title="Ancient Text Search Engine")

app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.include_router(health.router)
app.include_router(log.router)
app.include_router(languages.router)
app.include_router(indexing.router)
app.include_router(dataset.router)
app.include_router(search.router)
app.include_router(frontend.router)
app.include_router(testcase.router)
app.include_router(testcollection.router)
app.include_router(resultcollection.router)
app.include_router(comment.router)