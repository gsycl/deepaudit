import asyncio
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Application, Applicant, ApplicationStatus, ProgramType, AuditLog, FraudSignal
from ..models.audit import AuditAction
from ..models.applicant import Address
from ..schemas.application import (
    ApplicationSummary, ApplicationDetail, PaginatedApplicationList, DecisionPayload,
    AddressSchema, EmploymentHistorySchema, WeeklyCertificationSchema,
    FraudSignalSchema, FinancialRecordSchema,
)
from ..services.claude_service import get_ai_recommendation, apply_ai_result_to_application

router = APIRouter()


@router.get("", response_model=PaginatedApplicationList)
def list_applications(
    status: Optional[str] = None,
    min_risk: Optional[int] = Query(None, ge=0, le=100),
    max_risk: Optional[int] = Query(None, ge=0, le=100),
    program_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(Application).join(Applicant, Applicant.id == Application.applicant_id)

    if status:
        try:
            query = query.where(Application.status == ApplicationStatus(status))
        except ValueError:
            pass

    if min_risk is not None:
        query = query.where(Application.risk_score >= min_risk)
    if max_risk is not None:
        query = query.where(Application.risk_score <= max_risk)
    if program_type:
        try:
            query = query.where(Application.program_type == ProgramType(program_type))
        except ValueError:
            pass

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

    apps = db.execute(
        query
        .options(selectinload(Application.applicant).selectinload(Applicant.addresses))
        .order_by(Application.risk_score.desc().nulls_last(), Application.submitted_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    items = []
    for app in apps:
        primary_address = next((a for a in app.applicant.addresses if a.is_primary), None)
        items.append(ApplicationSummary(
            id=app.id,
            program_type=app.program_type,
            status=app.status,
            submitted_at=app.submitted_at,
            risk_score=app.risk_score,
            ai_recommendation=app.ai_recommendation,
            ai_headline=app.ai_headline,
            weekly_benefit_amount=app.weekly_benefit_amount,
            applicant_name=f"{app.applicant.first_name} {app.applicant.last_name}",
            applicant_id=app.applicant_id,
        ))

    return PaginatedApplicationList(total=total, page=page, page_size=page_size, items=items)


@router.get("/{application_id}", response_model=ApplicationDetail)
async def get_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
):
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
    ).scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app.ai_analyzed_at is None and app.risk_score is not None:
        asyncio.create_task(_run_ai_analysis(application_id))

    primary_address = next((a for a in app.applicant.addresses if a.is_primary), None)

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


@router.post("/{application_id}/decision", response_model=ApplicationSummary)
def submit_decision(
    application_id: uuid.UUID,
    payload: DecisionPayload,
    db: Session = Depends(get_db),
):
    app = db.execute(
        select(Application)
        .options(selectinload(Application.applicant).selectinload(Applicant.addresses))
        .where(Application.id == application_id)
    ).scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    action_map = {
        "approve": (AuditAction.APPROVED, ApplicationStatus.APPROVED),
        "deny": (AuditAction.DENIED, ApplicationStatus.DENIED),
        "flag": (AuditAction.FLAGGED, ApplicationStatus.FLAGGED),
    }

    if payload.action not in action_map:
        raise HTTPException(status_code=400, detail=f"Invalid action: {payload.action}")

    audit_action, new_status = action_map[payload.action]
    previous_status = app.status

    audit_log = AuditLog(
        application_id=app.id,
        auditor_name=payload.auditor_name,
        action=audit_action,
        notes=payload.notes,
        previous_status=previous_status,
        new_status=new_status,
    )
    app.status = new_status
    db.add(audit_log)
    db.commit()
    db.refresh(app)

    return ApplicationSummary(
        id=app.id,
        program_type=app.program_type,
        status=app.status,
        submitted_at=app.submitted_at,
        risk_score=app.risk_score,
        ai_recommendation=app.ai_recommendation,
        ai_headline=app.ai_headline,
        weekly_benefit_amount=app.weekly_benefit_amount,
        applicant_name=f"{app.applicant.first_name} {app.applicant.last_name}",
        applicant_id=app.applicant_id,
    )


async def _run_ai_analysis(application_id: uuid.UUID):
    from ..database import SessionLocal
    from sqlalchemy.orm import selectinload

    db = SessionLocal()
    try:
        app = db.execute(
            select(Application)
            .options(
                selectinload(Application.applicant).selectinload(Applicant.addresses),
                selectinload(Application.employment_history),
                selectinload(Application.weekly_certifications),
                selectinload(Application.fraud_signals),
            )
            .where(Application.id == application_id)
        ).scalar_one_or_none()

        if not app:
            return

        result = await get_ai_recommendation(app, app.fraud_signals, app.applicant)
        apply_ai_result_to_application(app, result)
        db.commit()
    except Exception:
        pass
    finally:
        db.close()
