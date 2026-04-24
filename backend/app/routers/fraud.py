import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from ..database import get_db
from ..models import Application, Applicant
from ..services.fraud_engine import run_fraud_analysis
from ..services.claude_service import get_ai_recommendation, apply_ai_result_to_application
from ..schemas.application import ApplicationDetail, AddressSchema, EmploymentHistorySchema, WeeklyCertificationSchema, FraudSignalSchema, FinancialRecordSchema

router = APIRouter()


@router.post("/analyze/{application_id}", response_model=ApplicationDetail)
async def reanalyze_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    app = db.execute(
        select(Application).where(Application.id == application_id)
    ).scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    run_fraud_analysis(application_id, db)

    app = db.execute(
        select(Application)
        .options(
            selectinload(Application.applicant).selectinload(Applicant.addresses),
            selectinload(Application.applicant).selectinload(Applicant.financial_records),
            selectinload(Application.applicant).selectinload(Applicant.household_members),
            selectinload(Application.employment_history),
            selectinload(Application.weekly_certifications),
            selectinload(Application.fraud_signals),
            selectinload(Application.submission_metadata),
        )
        .where(Application.id == application_id)
    ).scalar_one()

    ai_result = await get_ai_recommendation(app, app.fraud_signals, app.applicant)
    apply_ai_result_to_application(app, ai_result)
    db.commit()
    db.refresh(app)

    return ApplicationDetail(
        id=app.id,
        program_type=app.program_type,
        status=app.status,
        submitted_at=app.submitted_at,
        weekly_benefit_amount=app.weekly_benefit_amount,
        claim_start_date=app.claim_start_date,
        claim_end_date=app.claim_end_date,
        risk_score=app.risk_score,
        ai_recommendation=app.ai_recommendation,
        ai_explanation=app.ai_explanation,
        ai_headline=app.ai_headline,
        ai_confidence=app.ai_confidence,
        ai_key_signals=app.ai_key_signals,
        ai_suggested_action=app.ai_suggested_action,
        ai_analyzed_at=app.ai_analyzed_at,
        last_analyzed_at=app.last_analyzed_at,
        applicant_id=app.applicant_id,
        applicant_first_name=app.applicant.first_name,
        applicant_last_name=app.applicant.last_name,
        applicant_dob=app.applicant.dob,
        applicant_is_deceased=app.applicant.is_deceased,
        applicant_phone=app.applicant.phone,
        applicant_email=app.applicant.email,
        addresses=[AddressSchema.model_validate(a) for a in app.applicant.addresses],
        employment_history=[EmploymentHistorySchema.model_validate(e) for e in app.employment_history],
        weekly_certifications=[WeeklyCertificationSchema.model_validate(c) for c in app.weekly_certifications],
        fraud_signals=[FraudSignalSchema.model_validate(s) for s in app.fraud_signals],
        financial_records=[FinancialRecordSchema.model_validate(f) for f in app.applicant.financial_records],
    )
