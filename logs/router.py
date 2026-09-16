from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
import json
import os
from datetime import date as date_type
from utils import get_current_active_user, response
from auth.models import User
from fastapi import Depends
from .config import LOG_DIR

BASE_LOG_NAME = "requests.log"
router = APIRouter()

def get_log_file_for_date(target_date: str) -> str:
    today = date_type.today().isoformat()
    if target_date == today:
        return os.path.join(LOG_DIR, BASE_LOG_NAME)
    return os.path.join(LOG_DIR, f"{BASE_LOG_NAME}.{target_date}")

@router.get("/logs")
def get_logs(
    date: Optional[date_type] = Query(None, description="Filter by date, format YYYY-MM-DD"),
    request_id: Optional[str] = Query(None, description="Filter by request UUID"),
    user: User = Depends(get_current_active_user)
):
    print(f'date:{date}')
    if not user.is_admin:
        return response(
            status= 403,
            message= 'You do not have rights to access this info.'
        )
    matched_logs = []
    
    target_date = date or date_type.today().isoformat()
    print(f'target_date:{target_date}')
    log_file_path = get_log_file_for_date(target_date)
    print(f'log_file_path:{log_file_path}')

    try:
        with open(log_file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue  # skip malformed lines instead of crashing the whole request

                if request_id and entry.get("uuid") != request_id:
                    continue

                if date:
                    entry_timestamp = entry.get("timestamp", "")
                    entry_date = entry_timestamp.split("T")[0] if "T" in entry_timestamp else None
                    if entry_date != date:
                        continue

                matched_logs.append(entry)

    except FileNotFoundError:
        return {"status": 404, "message": "Log file not found", "data": []}

    return response(
        status= 200,
        message= f"Found {len(matched_logs)} matching log(s)",
        data= matched_logs
    )