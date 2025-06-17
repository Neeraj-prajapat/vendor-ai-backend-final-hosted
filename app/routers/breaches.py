# app/routers/breaches.py

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.breach_service import fetch_all_hibp_breaches
from .. import crud, schemas

router = APIRouter()

@router.post("/sync-breaches", response_model=dict)
# @router.post("/breaches/sync-breaches", response_model=dict)
def sync_breaches(db: Session = Depends(get_db)):
    try:
        count = fetch_all_hibp_breaches(db)
        return {"status": "success", "message": f"Synced {count} breaches", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing breaches: {e}")

@router.get("/search", response_model=list[schemas.BreachResponse])
# @router.get("/breaches/search", response_model=list[schemas.BreachResponse])
def search_breaches(
    query: str = Query(..., min_length=2),
    limit: int = Query(50, ge=1),
    db: Session = Depends(get_db)
):
    results = crud.search_breaches(db, query, limit)
    return [
        schemas.BreachResponse(
            id=b.id,
            name=b.name,
            title=b.title or b.name,
            domain=b.domain,
            breach_date=str(b.breach_date) if b.breach_date else None,
            added_date=str(b.added_date) if b.added_date else None,
            pwn_count=b.pwn_count,
            description=b.description or "",
            data_classes=b.data_classes or "",
            is_verified=b.is_verified,
            is_fabricated=b.is_fabricated,
        )
        for b in results
    ]

@router.get("/stats", response_model=schemas.BreachStats)
# @router.get("/breaches/stats", response_model=schemas.BreachStats)
def get_breach_stats(db: Session = Depends(get_db)):
    data = crud.get_breach_stats(db)
    return schemas.BreachStats(**data)

@router.get("/{breach_id}", response_model=schemas.BreachResponse)
# @router.get("/breaches/{breach_id}", response_model=schemas.BreachResponse)
def get_breach_detail(breach_id: int, db: Session = Depends(get_db)):
    breach = crud.get_breach_by_id(db, breach_id)
    if not breach:
        raise HTTPException(status_code=404, detail="Breach not found")
    return schemas.BreachResponse(
        id=breach.id,
        name=breach.name,
        title=breach.title or breach.name,
        domain=breach.domain,
        breach_date=str(breach.breach_date) if breach.breach_date else None,
        added_date=str(breach.added_date) if breach.added_date else None,
        pwn_count=breach.pwn_count,
        description=breach.description or "",
        data_classes=breach.data_classes or "",
        is_verified=breach.is_verified,
        is_fabricated=breach.is_fabricated,
    )

@router.get("/domain/{domain}", response_model=list[schemas.BreachResponse])
# @router.get("/breaches/domain/{domain}", response_model=list[schemas.BreachResponse])
def search_by_domain(domain: str, db: Session = Depends(get_db)):
    breaches = crud.get_breaches_by_domain(db, domain)
    return [
        schemas.BreachResponse(
            id=b.id,
            name=b.name,
            title=b.title or b.name,
            domain=b.domain,
            breach_date=str(b.breach_date) if b.breach_date else None,
            added_date=str(b.added_date) if b.added_date else None,
            pwn_count=b.pwn_count,
            description=b.description or "",
            data_classes=b.data_classes or "",
            is_verified=b.is_verified,
            is_fabricated=b.is_fabricated,
        )
        for b in breaches
    ]
