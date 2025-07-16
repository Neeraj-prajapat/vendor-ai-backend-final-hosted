def calculate_soc2_score(data: dict) -> dict:
    """Calculate SOC 2 compliance score with enhanced validation and scoring"""
    
    def clamp(value: float, min_val: float, max_val: float) -> float:
        return max(min(value, max_val), min_val)

    def safe_float(val, default=0.0):
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    def safe_int(val, default=0):
        try:
            return int(val)
        except (TypeError, ValueError):
            return default

    def score_effectiveness_controls(eff: dict) -> float:
        score = 4
        rbac = eff.get("role_based_access", {})
        if not (rbac.get("rbac_implemented") and rbac.get("no_privilege_escalation_issues")):
            score -= 1

        mfa = eff.get("mfa_implemented", {})
        if not mfa.get("mfa_enforced"):
            score -= 1

        ir = eff.get("incident_response_tested", {})
        if not (ir.get("documented_ir_plan") and ir.get("tested_ir_plan")):
            score -= 1

        enc = eff.get("encryption_enabled", {})
        if not (enc.get("encryption_at_rest") and enc.get("encryption_in_transit")):
            score -= 1

        return clamp(score, 0, 4)
    
    def score_exception_count(no_of_exception: dict, repeated_exception: list) -> float:
        # Coerce counts to int
        low_orig = safe_int(no_of_exception.get('low'))
        med_orig = safe_int(no_of_exception.get('medium'))
        high_orig = safe_int(no_of_exception.get('high'))

        total_orig_ded = low_orig * 1 + med_orig * 4 + high_orig * 10

        dup_ded = 0
        for item in repeated_exception or []:
            occ = safe_int(item.get('occurrences'))
            if occ == 2:
                dup_ded += 1
            elif 3 <= occ <= 4:
                dup_ded += 2
            elif occ >= 5:
                dup_ded += 3
        dup_ded = min(dup_ded, 20)

        total_deduction = total_orig_ded + dup_ded
        return clamp(20 - total_deduction, 0, 20)

    def score_patch_coverage(patch_coverage):
        return clamp(round(safe_float(patch_coverage) / 20), 0, 5)

    # Pull patch timeline data
    patch_timeline_data = data.get('patch_timeline_summary', {})
    timeline_days = patch_timeline_data.get('timeline_days')
    timeline_coverage = patch_timeline_data.get('patch_coverage')
    timeline_description = patch_timeline_data.get('timeline_description', '')

    # Data Validation & Sanitization
    validated_data = {
        'trust_criteria': [str(c).lower() for c in data.get('trust_criteria_covered', [])],
        'mfa_adoption': clamp(safe_float(data.get('mfa_summary', {}).get('adoption_percentage')), 0, 100),
        'encryption_coverage': clamp(safe_float(data.get('encryption_summary', {}).get('encryption_coverage')), 0, 100),
        'patch_timeliness_days': safe_int(timeline_days),
        'patch_timeline_description': str(timeline_description),
        'timeline_coverage': clamp(safe_float(timeline_coverage), 0, 100),
        'subcontractor_compliant': bool(data.get('subcontractor_compliance', {}).get('compliant', False)),
        'audit_firm': str(data.get('audit_firm', '')).lower(),
        'breaches': data.get('breaches', []),
        'security_controls_implemented': clamp(safe_float(data.get('security_controls_implemented', {}).get('implemented_percentage')), 0, 100),
        'effectiveness_controls': data.get('effectiveness_controls', {}),
        'exceptions': data.get('exceptions', []),
        'exception_criticality': data.get('exception_criticality_summary', {}).get('escalated_severity_count', {}),
        'no_of_exception': data.get('exception_criticality_summary', {}).get('original_severity_count', {}),
        'repeated_exception': data.get('exception_criticality_summary', {}).get('repeated_exceptions', []),
    }

    # Scoring components
    breakdown = {}

    # 1. Trust Service Criteria (10%)
    weights = {'security': 4.0, 'availability': 2.0, 'processing integrity': 1.0, 
               'confidentiality': 2.0, 'privacy': 1.0}
    covered = validated_data['trust_criteria']
    breakdown['trust_criteria'] = 0 if 'security' not in covered else clamp(sum(weights.get(c, 0) for c in covered), 0, 10)

    # 2. Exception Count (20%)
    breakdown['exception_count'] = score_exception_count(validated_data['no_of_exception'], validated_data['repeated_exception'])

    # 3. Exception Criticality (15%)
    escal = validated_data['exception_criticality']
    low_e, med_e, hi_e = safe_int(escal.get('low')), safe_int(escal.get('medium')), safe_int(escal.get('high'))
    crit_ded = low_e * 2.5 + med_e * 5 + hi_e * 10
    breakdown['exception_criticality'] = clamp(15 - crit_ded, 0, 15)

    # 4. Security Controls Implementation (6%)
    pct = validated_data['security_controls_implemented']
    if pct == 100:
        cs = 6
    elif pct >= 90:
        cs = 5
    elif pct >= 80:
        cs = 4
    elif pct >= 70:
        cs = 3
    elif pct >= 60:
        cs = 2
    elif pct >= 50:
        cs = 1
    else:
        cs = 0
    breakdown['security_controls_implemented'] = clamp(cs, 0, 6)

    # 5. Security Controls Effectiveness (4%)
    breakdown['security_controls_effectiveness'] = score_effectiveness_controls(validated_data['effectiveness_controls'])

    # 6. Breach History (10%)
    pens = sum(1 if b.get('status','').lower() == 'resolved' else 2 for b in validated_data['breaches'])
    breakdown['breach_history'] = clamp(10 - pens, 0, 10)

    # 7. MFA Adoption (10%)
    breakdown['mfa_adoption'] = clamp(int(validated_data['mfa_adoption'] // 10), 0, 10)

    # 8. Data Encryption (10%)
    breakdown['data_encryption'] = clamp(int(validated_data['encryption_coverage'] // 10), 0, 10)

    # 9. Patch Management (5%)
    breakdown['patch_timeliness'] = score_patch_coverage(validated_data['timeline_coverage'])

    # 10. Third Party Management (5%)
    breakdown['subcontractor_compliance'] = 5 if validated_data['subcontractor_compliant'] else 0

    # 11. Audit Firm Reputation (5%)
    big4 = {'deloitte','ey','kpmg','pwc','ernst & young','pricewaterhousecoopers'}
    top_tier = {'crowdstrike','mandiant','palo alto networks'}
    firm = validated_data['audit_firm']
    if any(f in firm for f in big4):
        breakdown['audit_firm'] = 5
    elif any(f in firm for f in top_tier):
        breakdown['audit_firm'] = 3
    else:
        breakdown['audit_firm'] = 0

    # Final Calculation
    total = sum(breakdown.values())
    weighted = clamp(total * 0.60, 0, 60)

    return {
        'final_private_score_60_percent_weightage': round(weighted, 2),
        'total_private_score': round(total, 2),
        'breakdown': {k: round(v, 2) for k, v in breakdown.items()},
    }
    
    
    
    
    
    
    
    
    
    
    
    
    
    
#  {
#   "name": "Controls Summary",
#   "check": "Extract every SOC 2 control into its proper group by applying three steps in order:\n\n1. **Heading match**: If the text around a control ID appears under a recognizable section heading (e.g., “Control Environment”, “Risk Assessment”, “Change Management”, “Availability”, “Confidentiality”, “Processing Integrity”, “Privacy”), assign it to that group.\n2. **Trust ID table**: If you see a table labeled “Tests of Operating Effectiveness and Results of Tests” or any table with a “Trust ID” column, extract each row’s ID, description, and test result, then map as in step 1 or step 3.\n3. **ID prefix fallback**: Otherwise, infer the group from the control ID prefix (CC1 → Control Environment, CC2 → Communication & Information, CC3 → Risk Assessment, CC4 → Monitoring Activities, CC5 → Control Activities, CC6 → Logical & Physical Access, CC7 → System Operations, CC8 → Change Management, CC9 → Risk Mitigation; A1 → Availability; C1 → Confidentiality; PI1 → Processing Integrity; P1 → Privacy).\n\nDo not omit any control IDs. For each control, output an object with:\n- `id`: the control ID (e.g. “CC1.1”)\n- `description`: the control description text, or `\"\"` if missing\n- `status`: one of `\"pass\"` (no exceptions), `\"partial\"` (minor deviations), or `\"fail\"` (major issues)\n- `result`: short audit result narrative (e.g. “No exceptions noted”, “Backup testing delayed”), or `null` if none given\n- `remediation`: `\"\"` if the report provides no remediation guidance\n\nReturn a fully populated JSON object under the key `controls_summary` with lists for `common_criteria`, `availability`, `confidentiality`, `processing_integrity`, and `privacy`.",
#   "output_field": "controls_summary",
#   "format": "object",
#   "object_fields": [
#     "common_criteria: list<object>",
#     "availability: list<object>",
#     "confidentiality: list<object>",
#     "processing_integrity: list<object>",
#     "privacy: list<object>"
#   ]
# }
   