import io
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from core.normalize import normalize
from db.models import LedgerEntry
from db.session import get_db

_backend = Path(__file__).resolve().parent.parent
load_dotenv(_backend / "db" / ".env")
load_dotenv(_backend / ".env")

router = APIRouter()


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    contents = await file.read()

    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

    try:
        rows = normalize(df)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    if not rows:
        return JSONResponse(
            status_code=400,
            content={"error": "No valid rows after normalization"},
        )

    period = rows[0]["period"]

    archive_path: str
    archive_error: str | None = None
    try:
        uploads_dir = Path(os.getenv("LOCAL_UPLOAD_DIR", _backend / "uploads"))
        uploads_dir.mkdir(parents=True, exist_ok=True)
        archive_name = (
            f"{period}_"
            f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.csv"
        )
        archive_file = uploads_dir / archive_name
        archive_file.write_bytes(contents)
        archive_path = str(archive_file)
    except Exception as err:
        print(err)
        archive_path = "local_archive_failed"
        archive_error = str(err)
        # Non-blocking: local archive is best-effort in MVP

    db.query(LedgerEntry).filter(LedgerEntry.period == period).delete(
        synchronize_session=False
    )
    db.bulk_insert_mappings(LedgerEntry, rows)
    db.commit()

    out = {
        "status": "ok",
        "period": period,
        "inserted_rows": len(rows),
        "archive_path": archive_path,
    }
    if archive_error is not None:
        out["archive_error"] = archive_error
    return out
