# app/routers/reports.py

import os
import tempfile
import shutil

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.soc2_extractor import SOC2Extractor
from .. import crud, schemas

from core.config import API_KEY  # import from config
# API_KEY = os.getenv("PERPLEXITY_API_KEY")

router = APIRouter()

@router.post("/upload", response_model=schemas.ReportResponse)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not (file.filename.lower().endswith(".pdf") or file.filename.lower().endswith(".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    temp_dir = tempfile.mkdtemp()
    try:
        # temp_file_path = temp_dir + "/" + file.filename
        temp_file_path = os.path.join(temp_dir, file.filename)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extractor = SOC2Extractor(api_key=API_KEY)
        result = extractor.extract(temp_file_path)

        report = crud.create_report(db, filename=file.filename, result=result)
        return {
            "id": report.id,
            "filename": report.filename,
            "score": result["score"],
            "created_at": report.created_at,
            "extracted_data": result["extracted"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {e}")
    finally:
        shutil.rmtree(temp_dir)

@router.get("/", response_model=list[schemas.ReportResponse])
def list_reports(db: Session = Depends(get_db)):
    reports = crud.get_all_reports(db)
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "score": r.result["score"],
            "created_at": r.created_at,
            "extracted_data": r.result["extracted"],
        }
        for r in reports
    ]

@router.get("/{report_id}", response_model=schemas.ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = crud.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id": report.id,
        "filename": report.filename,
        "score": report.result["score"],
        "created_at": report.created_at,
        "extracted_data": report.result["extracted"],
    }
