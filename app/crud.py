# app/crud.py

from sqlalchemy.orm import Session
from . import models
from datetime import datetime

# ——— SOC2Report CRUD ———
def create_report(db: Session, filename: str, result: dict) -> models.SOC2Report:
    report = models.SOC2Report(filename=filename, result=result)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

def get_all_reports(db: Session):
    return db.query(models.SOC2Report).all()

def get_report_by_id(db: Session, report_id: int):
    return db.query(models.SOC2Report).filter(models.SOC2Report.id == report_id).first()

# ——— Breach CRUD ———
def upsert_breach(db: Session, breach_data: dict):
    existing = db.query(models.Breach).filter(models.Breach.name == breach_data["name"]).first()
    if existing:
        for k, v in breach_data.items():
            setattr(existing, k, v)
        db.commit()
        return existing
    else:
        breach = models.Breach(**breach_data)
        db.add(breach)
        db.commit()
        db.refresh(breach)
        return breach

def search_breaches(db: Session, term: str, limit: int):
    pattern = f"%{term.lower()}%"
    return (
        db.query(models.Breach)
        .filter(
            (models.Breach.name.ilike(pattern)) |
            (models.Breach.title.ilike(pattern)) |
            (models.Breach.domain.ilike(pattern)) |
            (models.Breach.description.ilike(pattern))
        )
        .order_by(models.Breach.pwn_count.desc())
        .limit(limit)
        .all()
    )

def get_breach_by_id(db: Session, breach_id: int):
    return db.query(models.Breach).filter(models.Breach.id == breach_id).first()

def get_breaches_by_domain(db: Session, domain: str):
    return (
        db.query(models.Breach)
        .filter(models.Breach.domain.ilike(f"%{domain}%"))
        .order_by(models.Breach.pwn_count.desc())
        .all()
    )

def get_breach_stats(db: Session):
    total_breaches = db.query(models.Breach).count()
    total_accounts = [row[0] for row in db.query(models.Breach.pwn_count).all() if row[0]]
    total_pwned = sum(total_accounts)
    return {
        "total_breaches": total_breaches,
        "total_pwned_accounts": total_pwned,
        "last_updated": datetime.utcnow().isoformat()
    }
