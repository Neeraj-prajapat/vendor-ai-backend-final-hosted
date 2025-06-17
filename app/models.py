# app/models.py

from sqlalchemy import Column, Integer, Text, DateTime, String, Date, Boolean, Float
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from .database import Base

class SOC2Report(Base):
    __tablename__ = "soc2_reports"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(Text, nullable=False)
    result = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Breach(Base):
    __tablename__ = "breaches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    title = Column(String)
    domain = Column(String, index=True)
    breach_date = Column(Date)
    added_date = Column(Date)
    pwn_count = Column(Integer)
    description = Column(Text)
    data_classes = Column(Text)
    is_verified = Column(Boolean, default=False)
    is_fabricated = Column(Boolean, default=False)
    is_sensitive = Column(Boolean, default=False)
    is_retired = Column(Boolean, default=False)
    is_spam_list = Column(Boolean, default=False)

class CVE(Base):
    __tablename__ = "cves"
    
    id = Column(Integer, primary_key=True, index=True)
    cve_id = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    published_date = Column(DateTime)
    last_modified = Column(DateTime)
    cvss_v3_score = Column(Float)
    cvss_v3_severity = Column(String)
    cvss_v2_score = Column(Float)
    vendor_project = Column(String, index=True)
    product = Column(String, index=True)
    version_affected = Column(Text)
    cwe_id = Column(String)  # Common Weakness Enumeration
    references = Column(Text)  # JSON string of reference URLs
    attack_vector = Column(String)
    attack_complexity = Column(String)
    privileges_required = Column(String)
    user_interaction = Column(String)
    scope = Column(String)
    confidentiality_impact = Column(String)
    integrity_impact = Column(String)
    availability_impact = Column(String)
    is_analyzed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class VulnerabilityAlert(Base):
    __tablename__ = "vulnerability_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    cve_id = Column(String, index=True)
    alert_type = Column(String)  # 'critical', 'high_priority', 'trending'
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
