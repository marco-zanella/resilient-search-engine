import os
import re
from fastapi import APIRouter

router = APIRouter(prefix="/api/logs", tags=["Logs"])
log_dir = os.path.join(os.getcwd(), 'logs')
log_file = os.path.join(log_dir, 'webapp.log')
log_re = re.compile(r"\[(.*)\]\[(.*)\]\[(.*)\] (.*)")

def parseLog(line: str) -> dict:
    match = log_re.findall(line)
    if not match:
        return {}
    return {
        "timestamp": match[0][0],
        "level": match[0][1],
        "service": match[0][2],
        "message": match[0][3],
    }


@router.get("/")
def get_log():
    with open(log_file, "r", encoding="utf-8") as f:
        return [parseLog(line) for line in f.readlines()]


@router.delete("/")
def delete_log():
    with open(log_file, "w", encoding="utf-8") as f:
        pass