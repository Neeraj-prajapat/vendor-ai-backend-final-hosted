from soc2_public_scoring import calculate_public_risk_score

# Dummy input you can pass directly into calculate_public_risk_score():
dummy_data = {
    "past_breaches": 2,
    "regulatory_fines": 1,
    "recent_incidents": 3,
    "dark_web_exposure": False,
    "customer_reviews": 4.2,
    "employee_sentiment": 3.8,
    "social_media": "neutral",
    "critical_cves": 5,
    "outdated_tech_percent": 30.0,
    "cloud_compliant": True
}

# When you call:
result = calculate_public_risk_score(dummy_data)

print(result)