


def calculate_public_risk_score(data: dict) -> dict:
    """Calculate a public-facing SOC 2–style cybersecurity score (0–100)
    based on breaches, fines, incidents, dark‑web, sentiment, CVEs, tech stack, and cloud compliance."""

    def clamp(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
        return max(min(value, max_val), min_val)

    # 1. Validate & normalize raw inputs
    validated = {
        'breaches':         int(data.get('past_breaches', 0)),
        'fines':            int(data.get('regulatory_fines', 0)),
        'incidents':        int(data.get('recent_incidents', 0)),
        'dark_web':         bool(data.get('dark_web_exposure', False)),
        'reviews':          float(data.get('customer_reviews', 0.0)),      # 0–5 star
        'employee_sent':    float(data.get('employee_sentiment', 0.0)),    # 0–5 star
        'social_media':     str(data.get('social_media', 'neutral')).lower(),  # 'positive','neutral','negative'
        'cves':             int(data.get('critical_cves', 0)),
        'outdated_pct':     float(data.get('outdated_tech_percent', 0.0)),    # 0–100%
        'cloud_compliant':  bool(data.get('cloud_compliant', False))
    }

    breakdown = {}
    # total = 0.0

    # Past Breaches (20 points → −5 per breach, capped at −20, offset to [0–20])
    b_score = clamp(-5 * validated['breaches'], -20, 0) + 20
    breakdown['past_breaches'] = round(b_score, 2)
    # total += b_score

    # Regulatory Fines (10 points → −5 per fine, capped at −10, offset to [0–10])
    f_score = clamp(-5 * validated['fines'], -10, 0) + 10
    breakdown['regulatory_fines'] = round(f_score, 2)
    # total += f_score

    # Recent Incidents (10 points → −3 per incident, capped at −10, offset to [0–10])
    i_score = clamp(-3 * validated['incidents'], -10, 0) + 10
    breakdown['recent_incidents'] = round(i_score, 2)
    # total += i_score

    # Dark‑Web Exposure (10 points → 0 if exposed, else 10)
    dw_score = 0 if validated['dark_web'] else 10
    breakdown['dark_web_exposure'] = round(dw_score, 2)
    # total += dw_score

    # Customer Reviews (5 points → map 0–5 stars → 0–5 points)
    cr_score = clamp(validated['reviews'] * 1.0, 0, 5)
    breakdown['customer_reviews'] = round(cr_score, 2)
    # total += cr_score

    # Employee Sentiment (5 points → map 0–5 stars → 0–5 points)
    es_score = clamp(validated['employee_sent'] * 1.0, 0, 5)
    breakdown['employee_sentiment'] = round(es_score, 2)
    # total += es_score

    # Social Media (10 points → positive=10, neutral=5, negative=0)
    sm = validated['social_media']
    if sm == 'positive':
        sm_score = 10
    elif sm == 'neutral':
        sm_score = 5
    else:
        sm_score = 0
    breakdown['social_media'] = round(sm_score, 2)
    # total += sm_score

    # CVE Vulnerabilities (10 points → −1 per CVE, capped at −10, offset to [0–10])
    cv_score = clamp(-1 * validated['cves'], -10, 0) + 10
    breakdown['cve_vulnerabilities'] = round(cv_score, 2)
    # total += cv_score

    # Tech Stack Risk (10 points → map outdated_pct 0–100% to 10–0 points)
    ts_score = clamp((100.0 - validated['outdated_pct']) * 0.1, 0, 10)
    breakdown['tech_stack'] = round(ts_score, 2)
    # total += ts_score

    # Cloud Compliance (10 points → 10 if compliant, else 0)
    cc_score = 10 if validated['cloud_compliant'] else 0
    breakdown['cloud_compliance'] = round(cc_score, 2)
    # total += cc_score



    # Aggregate total cleanly
    total_sum_up_score = sum(breakdown.values())
    weighted_score = clamp(total_sum_up_score * 0.40, 0, 40)  # 40% weight for public score
    # Final aggregation & clamp to 0–100
    final_score = clamp(total_sum_up_score, 0, 100)

    return {
        'final_public_score_40_percent_weightage': round(weighted_score, 2),
        'total_public_score': round(final_score, 2),
        'public_breakdown': breakdown
    }






































































# def calculate_public_risk_score(data: dict) -> dict:
#     """Calculate a public-facing SOC 2–style cybersecurity score (0–100)
#     based on public signals: breaches, CVEs, fines, sentiment, dark‑web leaks, tech stack."""
    
#     def clamp(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
#         return max(min(value, max_val), min_val)
    
#     # 1. Validate & normalize raw inputs
#     validated = {
#         # Number of public breach incidents
#         'breaches': int(data.get('breaches_count', 0)),
#         # Sum of CVSS scores for unpatched vulnerabilities
#         'cve_sum': float(data.get('cve_score_sum', 0.0)),
#         # Number of regulatory fines/penalties
#         'fines': int(data.get('fines_count', 0)),
#         # Sentiment polarity in [-1.0, +1.0]
#         'sentiment': float(data.get('sentiment_polarity', 0.0)),
#         # Number of distinct leaked credential sets
#         'leaks': int(data.get('leaked_credentials_count', 0)),
#         # Percentage of systems running outdated/high-risk software (0–100)
#         'outdated_pct': float(data.get('outdated_tech_percent', 0.0))
#     }
    
#     # 2. Compute per‑category subscores (0–100)
#     breakdown = {}
    
#     # Breaches: each incident subtracts 20 points from 100
#     breakdown['breaches'] = clamp(100.0 - 20.0 * validated['breaches'])
    
#     # Vulnerabilities: subtract the total CVSS sum from 100
#     breakdown['vulnerabilities'] = clamp(100.0 - validated['cve_sum'])
    
#     # Fines: each fine subtracts 25 points
#     breakdown['fines'] = clamp(100.0 - 25.0 * validated['fines'])
    
#     # Sentiment: map polarity [-1,+1] → [0,100]
#     breakdown['sentiment'] = clamp((validated['sentiment'] + 1.0) * 50.0)
    
#     # Dark‑web leaks: each credential set subtracts 30 points
#     breakdown['darkweb'] = clamp(100.0 - 30.0 * validated['leaks'])
    
#     # Tech stack: subtract 20×(outdated%) from 100
#     breakdown['tech'] = clamp(100.0 - 20.0 * (validated['outdated_pct'] / 100.0))
    
#     # 3. Apply weights and compute final score
#     weights = {
#         'breaches':        0.20,  # 20%
#         'vulnerabilities': 0.25,  # 25%
#         'fines':           0.15,  # 15%
#         'sentiment':       0.10,  # 10%
#         'darkweb':         0.20,  # 20%
#         'tech':            0.10   # 10%
#     }
    
#     final_score = 0.0
#     for category, weight in weights.items():
#         final_score += breakdown[category] * weight
    
#     # 4. Clamp & round
#     final_score = clamp(final_score)
    
#     return {
#         'final_score': round(final_score, 2),
#         'breakdown': {k: round(v, 2) for k, v in breakdown.items()}
#     }
