### project/app/sync_reports.py
```python
from datetime import date
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import PrivateReport, PublicScore
from .crud import compute_grade_and_flag, upsert_public_score
from .scoring import calculate_public_risk_score, calculate_soc2_score


def sync_and_flag_all_reports():
    """
    Fetches each PrivateReport, recalculates both public and private scores,
    computes combined total score, assigns grades and flags,
    upserts the monthly PublicScore record, and updates the PrivateReport JSON.
    """
    with SessionLocal() as db:
        # Fetch all private reports
        private_reports = db.query(PrivateReport).all()
        for rpt in private_reports:
            # Recalculate public scores
            public_json = calculate_public_risk_score(rpt.result)
            as_of = date.today().replace(day=1)

            # Upsert monthly PublicScore
            score_in = type('ScoreIn', (), {
                'as_of_month': as_of,
                'total_public_score': public_json['total_public_score'],
                'final_public_score_40_percent_weightage': public_json['final_public_score_40_percent_weightage'],
                'public_breakdown': public_json['public_breakdown']
            })
            public_score = upsert_public_score(db, rpt.id, score_in)

            # Compute private scores
            private_json = calculate_soc2_score(rpt.result)

            # Compute combined total (public 40% + private 60%)
            combined_score = (
                private_json['final_private_score_60_percent_weightage'] +
                public_json['final_public_score_40_percent_weightage']
            )
            grade_combined, flagged_combined = compute_grade_and_flag(combined_score)

            # Merge all results into private JSON
            merged = dict(rpt.result)
            merged.update({
                # private
                'total_private_score': private_json['total_private_score'],
                'final_private_score_60_percent_weightage': private_json['final_private_score_60_percent_weightage'],
                'private_breakdown': private_json['private_breakdown'],
                # public
                'total_public_score': public_json['total_public_score'],
                'final_public_score_40_percent_weightage': public_json['final_public_score_40_percent_weightage'],
                'public_breakdown': public_json['public_breakdown'],
                # monthly PublicScore metadata
                'grade_public': public_score.grade,
                'flagged_public': public_score.is_flagged,
                # private grade
                'grade_private': compute_grade_and_flag(private_json['total_private_score'])[0],
                'flagged_private': compute_grade_and_flag(private_json['total_private_score'])[1],
                # combined
                'total_public_private_score': round(combined_score, 2),
                'grade_combined': grade_combined,
                'flagged_combined': flagged_combined
            })

            # Persist updated JSON
            rpt.result = merged
            db.add(rpt)

        db.commit()


if __name__ == '__main__':
    sync_and_flag_all_reports()
```
