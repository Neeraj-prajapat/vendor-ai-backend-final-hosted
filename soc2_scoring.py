
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
        """Score security control effectiveness out of 4"""
        score = 4  # full points

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
        """
        Score exceptions (out of 20), combining:
        • Original severity deductions
        • Duplicate‐exception deductions (formerly 3 pts)
        
        summary should be:
        {
            'original_severity_count': {'low': int, 'medium': int, 'high': int},
            'repeated_exceptions': [
            {'occurrences': int, …},
            …
            ]
        }
        """
        # 1) Original‑severity deductions
        orig = no_of_exception
        # low_orig = orig.get('low', 0)
        # med_orig = orig.get('medium', 0)
        # high_orig  = orig.get('high', 0)
        low_orig  = safe_int(orig.get('low'))
        med_orig  = safe_int(orig.get('medium'))
        high_orig = safe_int(orig.get('high'))

        total_orig_ded = low_orig * (1) + med_orig *(4) + high_orig * (10)

        # 2) Duplicate‑exception deductions (formerly out of 3)
        dup_list = repeated_exception
        dup_ded = 0
        for item in dup_list:
            occ = item.get('occurrences', 0)
            if occ == 2:
                dup_ded += 1
            elif 3 <= occ <= 4:
                dup_ded += 2
            elif occ >= 5:
                dup_ded += 3

        # cap duplicate deduction at 3
        # dup_ded = min(dup_ded, 3)
        dup_ded = min(dup_ded, 20)

        total_deduction = total_orig_ded + dup_ded

        # final score out of 20
        return clamp(20 - total_deduction, 0, 20)

    def score_patch_coverage(patch_coverage):
        # if patch_coverage is None:
        #     return 0
        cov = safe_float(patch_coverage, default=0.0)
        return round(cov / 20)

    # timeline_days = data.get('patch_timeline_summary', {}).get('timeline_days')
    patch_timeline_data = data.get('patch_timeline_summary', {})
    
    timeline_days = patch_timeline_data.get('timeline_days')
    timeline_coverage = patch_timeline_data.get('patch_coverage')
    timeline_description = patch_timeline_data.get('timeline_description', '')
    
    # Data Validation & Sanitization
    validated_data = {
        'trust_criteria': [str(c).lower() for c in data.get('trust_criteria_covered', [])],
        
        # 'mfa_adoption': clamp(float(data.get('mfa_adoption', 0)), 0, 100),
        # 'mfa_adoption': clamp(float(data.get('mfa_summary', {}).get('adoption_percentage', 0)), 0, 100),
        'mfa_adoption': clamp(safe_float(data.get('mfa_summary', {}).get('adoption_percentage')), 0, 100),
        
        # 'encryption_coverage': clamp(float(data.get('encryption_coverage', 0)), 0, 100),
        # 'encryption_coverage': clamp(float(data.get('encryption_summary', {}).get('encryption_coverage', 0)), 0, 100),
        'encryption_coverage': clamp(safe_float(data.get('encryption_summary', {}).get('encryption_coverage')), 0, 100),
        
        # 'patch_timeliness_days': int(data.get('patch_timeliness_days', 90)),
        # 'patch_timeliness_days': int(timeline_days) if isinstance(timeline_days, int) else 0,
        'patch_timeliness_days': safe_int(timeline_days),
        'patch_timeline_description': str(timeline_description),
        # 'timeline_coverage': clamp(float(timeline_coverage), 0, 100),
        'timeline_coverage': clamp(safe_float(timeline_coverage), 0, 100),
        
        # 'subcontractor_compliant': bool(data.get('subcontractor_compliant', False)),
        'subcontractor_compliant': bool(data.get('subcontractor_compliance', {}).get('compliant', False)),
        
        'audit_firm': str(data.get('audit_firm', '')).lower(),
        'breaches': data.get('breaches', []),
        
        # 'security_controls_implemented': clamp(float(data.get('security_controls_implemented', {}).get('implemented_percentage', 0)), 0, 100),
        'security_controls_implemented': clamp(safe_float(data.get('security_controls_implemented', {}).get('implemented_percentage')), 0, 100),
        
        'effectiveness_controls': data.get('effectiveness_controls', {}),
        'exceptions': data.get('exceptions', []),
        'exception_criticality' : data.get('exception_criticality_summary', {}).get('escalated_severity_count',{}),
        'no_of_exception' : data.get('exception_criticality_summary', {}).get('original_severity_count',{}),
        'repeated_exception' : data.get('exception_criticality_summary', {}).get('repeated_exceptions',{})
    }

    # Early termination for critical failures
    # if 'security' not in validated_data['trust_criteria']:
    #     return {
    #         'final_score': 0.0,
    #         'breakdown': {'critical_failure': 'Missing security criteria'},
    #         'compliance_status': 'Fail'
    #     }

    # Scoring components
    breakdown = {}
    
    # 1. Trust Service Criteria (10%) — Security is mandatory
    trust_weights = {'security': 4.0, 'availability': 2.0, 'processing integrity': 1.0, 
                    'confidentiality': 2.0, 'privacy': 1.0}
    # trust_score = sum(trust_weights.get(crit, 0) for crit in validated_data['trust_criteria'])
    covered_criteria = validated_data['trust_criteria']

    if 'security' not in covered_criteria:
        trust_score = 0  # Security missing, so 0 for trust criteria
    else:
        trust_score = sum(trust_weights.get(crit, 0) for crit in covered_criteria)
        
    breakdown['trust_criteria'] = clamp(trust_score, 0, 10)
    
    
    
    # 2. ─── Exception Count (20 %) ───
    # Use summary['original_severity_count']
    no_of_excep = validated_data["no_of_exception"]
    repeats   = validated_data["repeated_exception"]
    # Compute combined 20‑pt exception score
    breakdown['exception_count'] = score_exception_count(no_of_excep, repeats)

    
    # 3. Exception Criticality (15%)
    # Use summary['escalated_severity_count']
    escal = validated_data['exception_criticality']
    low_e, med_e, hi_e = escal.get('low', 0), escal.get('medium', 0), escal.get('high', 0)

    # Per your rules: low → -2.5, medium → -5, high → -10 each
    crit_ded = low_e * 2.5 + med_e * 5 + hi_e * 10
    breakdown['exception_criticality'] = clamp(15 - crit_ded, 0, 15)
    
    
    #? 4. Security Controls (10%)
  
    controls_pct = validated_data['security_controls_implemented']
    # Percentage implemented (6%)
    if controls_pct == 100:
        controls_score = 6
    elif controls_pct >= 90:
        controls_score = 5
    elif controls_pct >= 80:
        controls_score = 4
    elif controls_pct >= 70:
        controls_score = 3
    elif controls_pct >= 60:
        controls_score = 2
    elif controls_pct >= 50:
        controls_score = 1
    else:
        controls_score = 0
    
    breakdown['security_controls_implemented'] = clamp(controls_score, 0, 6)
    
    # Effectiveness penalties (4%)
    eff_controls_score = score_effectiveness_controls(validated_data['effectiveness_controls'])
    breakdown['security_controls_effectiveness'] = eff_controls_score
        

    
    #? 5. Breach History (10%)  
    
    raw_breaches = validated_data['breaches']
    validated_breaches = []
    for b in raw_breaches:
        desc   = b.get('description', '').strip()
        status = b.get('status', '').lower().strip()
        validated_breaches.append({
            'description': desc,
            'resolved': (status == 'resolved')
        })
        
    penalties = 0
    for b in validated_breaches:
        penalties += 1 if b['resolved'] else 2

    breakdown['breach_history'] = clamp(10 - penalties, 0, 10)
    
    # 6. MFA Adoption (10% total)
    breakdown['mfa_adoption'] = clamp(int(validated_data['mfa_adoption'] // 10), 0, 10)
    
    # 7. Data Encryption (10% total)
    breakdown['data_encryption'] = clamp(int(validated_data['encryption_coverage'] // 10), 0, 10)
    
    # 8. Patch Management (5%)
    # patch_days = validated_data['patch_timeliness_days']
    # patch_description = validated_data['patch_timeline_description'].lower()
        
    # # Default score
    # raw_patch_score = 0

    # if patch_days > 0:
    #     # only score when there's actually a timeline
    #     if patch_days <= 7:
    #         raw_patch_score = 5
    #     elif patch_days <= 30:
    #         raw_patch_score = 4
    #     # (you can extend for >30 if needed)
    # elif any(keyword in patch_description for keyword in ['timely', 'automated', 'policy-driven', 'regular', 'scheduled']):
    #     raw_patch_score = 3
    # elif any(keyword in patch_description for keyword in ['irregular', 'manual', 'partially documented']):
    #     raw_patch_score = 2
    # elif 'reactive' in patch_description or 'no automation' in patch_description:
    #     raw_patch_score = 1
    
    # Clamp just in case (though this will always be within 0–5):
    raw_patch_score = score_patch_coverage(validated_data['timeline_coverage'])
    breakdown['patch_timeliness'] = clamp(raw_patch_score, 0, 5)
    
    # 9. Third Party Management (5%)
    breakdown['subcontractor_compliance'] = 5 if validated_data['subcontractor_compliant'] else 0
    
    # 11. Audit Firm Reputation (5%)
    big4 = {'deloitte','ey','kpmg','pwc','ernst & young','pricewaterhousecoopers'}
    top_tier = {'crowdstrike', 'mandiant', 'palo alto networks'}
    firm = validated_data['audit_firm']
    if any(f in firm for f in big4):
        breakdown['audit_firm'] = 5
    elif any(f in firm for f in top_tier):
        breakdown['audit_firm'] = 3
    else:
        breakdown['audit_firm'] = 0

    # Final Calculation
    total_sum_up_score = sum(breakdown.values())                   # ye percentage me hi aaya hai
    weighted_score = clamp(total_sum_up_score * 0.60, 0, 60)       # 60% weighting
    # weighted_score = total_sum_up_score * 0.60                   # giving directly is more better
    
    return {
        'final_private_score_60_percent_weightage': round(weighted_score, 2),
        'total_private_score': total_sum_up_score,
        'breakdown': {k: round(v, 2) for k, v in breakdown.items()},
        # 'compliance_status': 'Pass' if weighted_score >= 36 else 'Fail',
    }








    # breakdown['security_controls'] = {
    #     'implementation': round(impl,2),
    #     'effectiveness': round(eff,2)
    # }
