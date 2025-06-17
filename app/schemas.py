# app/schemas.py

from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional, List

# ——— SOC2 Models ———
class ScoreBreakdown(BaseModel):
    trust_criteria: float
    exception_count: float
    exception_criticality: float
    security_controls_implemented: float
    security_controls_effectiveness: float
    breach_history: float
    mfa_adoption: float
    data_encryption: float
    patch_timeliness: float
    subcontractor_compliance: float
    audit_firm: float

class Score(BaseModel):
    final_private_score_60_percent_weightage: float
    total_private_score: float
    breakdown: ScoreBreakdown

class ReportResponse(BaseModel):
    id: int
    filename: str
    score: Score
    created_at: datetime
    extracted_data: Dict[str, Any]

class ReportListItem(BaseModel):
    id: int
    filename: str
    score: float
    created_at: datetime

# ——— Breach Models ———
class BreachResponse(BaseModel):
    id: int
    name: str
    title: str
    domain: Optional[str]
    breach_date: Optional[str]
    added_date: Optional[str]
    pwn_count: Optional[int]
    description: str
    data_classes: str
    is_verified: bool
    is_fabricated: bool

class BreachStats(BaseModel):
    total_breaches: int
    total_pwned_accounts: int
    last_updated: str

# ——— CVE/Vulnerability Models ———
class CVEResponse(BaseModel):
    id: int
    cve_id: str
    description: str
    published_date: Optional[datetime]
    cvss_v3_score: Optional[float]
    cvss_v3_severity: Optional[str]
    vendor_project: Optional[str]
    product: Optional[str]
    cwe_id: Optional[str]
    attack_vector: Optional[str]
    is_analyzed: bool
    created_at: datetime

class CVEDetailResponse(BaseModel):
    id: int
    cve_id: str
    description: str
    published_date: Optional[datetime]
    last_modified: Optional[datetime]
    cvss_v3_score: Optional[float]
    cvss_v3_severity: Optional[str]
    cvss_v2_score: Optional[float]
    vendor_project: Optional[str]
    product: Optional[str]
    version_affected: Optional[str]
    cwe_id: Optional[str]
    references: Optional[str]
    attack_vector: Optional[str]
    attack_complexity: Optional[str]
    privileges_required: Optional[str]
    user_interaction: Optional[str]
    scope: Optional[str]
    confidentiality_impact: Optional[str]
    integrity_impact: Optional[str]
    availability_impact: Optional[str]
    is_analyzed: bool
    created_at: datetime

class VulnerabilityStats(BaseModel):
    total_cves: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    recent_7_days: int
    unanalyzed_count: int
    last_updated: str

class AlertResponse(BaseModel):
    id: int
    cve_id: str
    alert_type: str
    message: str
    is_read: bool
    created_at: datetime
