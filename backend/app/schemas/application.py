from __future__ import annotations
import uuid
import json
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, field_validator
from ..models.application import ApplicationStatus, ProgramType


class AddressSchema(BaseModel):
    id: uuid.UUID
    street: str
    city: str
    state: str
    zip_code: str
    lat: float | None = None
    lon: float | None = None

    model_config = {"from_attributes": True}


class EmploymentHistorySchema(BaseModel):
    id: uuid.UUID
    employer_name: str
    start_date: date
    end_date: date | None = None
    separation_reason: str
    reported_salary: Decimal | None = None
    is_verified: bool

    model_config = {"from_attributes": True}


class WeeklyCertificationSchema(BaseModel):
    id: uuid.UUID
    week_start: date
    did_work: bool
    reported_earnings: Decimal
    job_search_contacts: int
    submitted_at: datetime

    model_config = {"from_attributes": True}


class FraudSignalSchema(BaseModel):
    id: uuid.UUID
    rule_id: str
    signal_type: str
    severity: str
    score_contribution: int
    description: str
    metadata: dict | None = None
    detected_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        if hasattr(obj, "signal_metadata"):
            data = {
                "id": obj.id,
                "rule_id": obj.rule_id,
                "signal_type": obj.signal_type,
                "severity": obj.severity,
                "score_contribution": obj.score_contribution,
                "description": obj.description,
                "metadata": obj.signal_metadata,
                "detected_at": obj.detected_at,
            }
            return cls(**data)
        return super().model_validate(obj, **kwargs)

    model_config = {"from_attributes": True}


class FinancialRecordSchema(BaseModel):
    id: uuid.UUID
    institution_name: str | None = None
    account_type: str
    monthly_income_reported: Decimal | None = None

    model_config = {"from_attributes": True}


class ApplicantSummary(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    dob: date
    state: str | None = None
    is_deceased: bool

    model_config = {"from_attributes": True}


class ApplicationSummary(BaseModel):
    id: uuid.UUID
    program_type: ProgramType
    status: ApplicationStatus
    submitted_at: datetime
    risk_score: int | None = None
    ai_recommendation: str | None = None
    ai_headline: str | None = None
    weekly_benefit_amount: Decimal | None = None
    applicant_name: str
    applicant_id: uuid.UUID

    model_config = {"from_attributes": True}


class ApplicationDetail(BaseModel):
    id: uuid.UUID
    program_type: ProgramType
    status: ApplicationStatus
    submitted_at: datetime
    weekly_benefit_amount: Decimal | None = None
    claim_start_date: date | None = None
    claim_end_date: date | None = None
    risk_score: int | None = None
    ai_recommendation: str | None = None
    ai_explanation: str | None = None
    ai_headline: str | None = None
    ai_confidence: str | None = None
    ai_key_signals: list[str] | None = None
    ai_suggested_action: str | None = None
    ai_analyzed_at: datetime | None = None
    last_analyzed_at: datetime | None = None

    applicant_id: uuid.UUID
    applicant_first_name: str
    applicant_last_name: str
    applicant_dob: date
    applicant_is_deceased: bool
    applicant_phone: str
    applicant_email: str

    addresses: list[AddressSchema] = []
    employment_history: list[EmploymentHistorySchema] = []
    weekly_certifications: list[WeeklyCertificationSchema] = []
    fraud_signals: list[FraudSignalSchema] = []
    financial_records: list[FinancialRecordSchema] = []

    model_config = {"from_attributes": True}

    @field_validator("ai_key_signals", mode="before")
    @classmethod
    def parse_key_signals(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v


class PaginatedApplicationList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ApplicationSummary]


class DecisionPayload(BaseModel):
    action: str  # approve, deny, flag
    auditor_name: str
    notes: str | None = None
