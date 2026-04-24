from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Protocol
import uuid

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..models import (
    Application, Applicant, EmploymentHistory, WeeklyCertification,
    FinancialRecord, SubmissionMetadata, FraudSignal, SignalSeverity,
    HouseholdMember,
)


@dataclass
class SignalResult:
    triggered: bool
    rule_id: str
    signal_type: str
    severity: SignalSeverity
    score_contribution: int
    description: str
    metadata: dict = field(default_factory=dict)


@dataclass
class RuleContext:
    db: Session
    application: Application
    applicant: Applicant
    employment_history: list
    weekly_certs: list
    financial_records: list
    submission_meta: object | None
    household_members: list


class FraudRule(Protocol):
    rule_id: str
    signal_type: str
    weight: int

    def evaluate(self, ctx: RuleContext) -> SignalResult: ...


class StillEmployedRule:
    rule_id = "RULE_001"
    signal_type = "still_employed_check"
    weight = 20

    def evaluate(self, ctx: RuleContext) -> SignalResult:
        today = datetime.utcnow().date()
        for emp in ctx.employment_history:
            if emp.separation_reason == "laid_off" and (emp.end_date is None or emp.end_date > today):
                return SignalResult(
                    triggered=True,
                    rule_id=self.rule_id,
                    signal_type=self.signal_type,
                    severity=SignalSeverity.HIGH,
                    score_contribution=self.weight,
                    description=f"Applicant claims layoff from {emp.employer_name} but end date {emp.end_date} is in the future or missing.",
                    metadata={"employer": emp.employer_name, "end_date": str(emp.end_date)},
                )
        return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                            severity=SignalSeverity.LOW, score_contribution=0, description="")


class IncomeDuringClaimRule:
    rule_id = "RULE_002"
    signal_type = "income_during_claim"
    weight = 15

    def evaluate(self, ctx: RuleContext) -> SignalResult:
        if not ctx.financial_records or not ctx.weekly_certs:
            return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                                severity=SignalSeverity.LOW, score_contribution=0, description="")

        monthly_income = float(ctx.financial_records[0].monthly_income_reported or 0)
        weekly_benefit = float(ctx.application.weekly_benefit_amount or 0)
        zero_earning_weeks = sum(1 for c in ctx.weekly_certs if not c.did_work and float(c.reported_earnings) == 0)

        if monthly_income > weekly_benefit * 4 * 1.5 and zero_earning_weeks > 0:
            return SignalResult(
                triggered=True,
                rule_id=self.rule_id,
                signal_type=self.signal_type,
                severity=SignalSeverity.MEDIUM,
                score_contribution=self.weight,
                description=f"Financial records show ${monthly_income:.0f}/month income but {zero_earning_weeks} weeks certified with zero earnings.",
                metadata={"monthly_income": monthly_income, "zero_earning_weeks": zero_earning_weeks},
            )
        return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                            severity=SignalSeverity.LOW, score_contribution=0, description="")


class SharedBankAccountRule:
    rule_id = "RULE_003"
    signal_type = "shared_bank_account"
    weight = 15

    def evaluate(self, ctx: RuleContext) -> SignalResult:
        if not ctx.financial_records:
            return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                                severity=SignalSeverity.LOW, score_contribution=0, description="")

        from ..models.financial import FinancialRecord
        from ..models.applicant import Applicant as ApplicantModel

        bank_hash = ctx.financial_records[0].bank_account_hash
        shared = ctx.db.execute(
            select(func.count(FinancialRecord.id.distinct()))
            .where(FinancialRecord.bank_account_hash == bank_hash)
            .where(FinancialRecord.applicant_id != ctx.applicant.id)
        ).scalar() or 0

        if shared > 0:
            count = shared + 1
            severity = SignalSeverity.CRITICAL if count >= 3 else SignalSeverity.HIGH
            contribution = min(self.weight, self.weight * count // 2)
            return SignalResult(
                triggered=True,
                rule_id=self.rule_id,
                signal_type=self.signal_type,
                severity=severity,
                score_contribution=contribution,
                description=f"Bank account is shared with {shared} other applicant(s). Total {count} applicants use this account.",
                metadata={"shared_count": int(shared), "bank_hash_prefix": bank_hash[:8]},
            )
        return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                            severity=SignalSeverity.LOW, score_contribution=0, description="")


class SharedDeviceFingerprintRule:
    rule_id = "RULE_004"
    signal_type = "shared_device_fingerprint"
    weight = 12

    def evaluate(self, ctx: RuleContext) -> SignalResult:
        if not ctx.submission_meta:
            return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                                severity=SignalSeverity.LOW, score_contribution=0, description="")

        from ..models.metadata import SubmissionMetadata

        fp = ctx.submission_meta.device_fingerprint
        shared = ctx.db.execute(
            select(func.count(SubmissionMetadata.id))
            .where(SubmissionMetadata.device_fingerprint == fp)
            .where(SubmissionMetadata.application_id != ctx.application.id)
        ).scalar() or 0

        if shared > 0:
            return SignalResult(
                triggered=True,
                rule_id=self.rule_id,
                signal_type=self.signal_type,
                severity=SignalSeverity.HIGH,
                score_contribution=self.weight,
                description=f"Device fingerprint matches {shared} other application(s). Possible coordinated submission.",
                metadata={"shared_applications": int(shared)},
            )
        return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                            severity=SignalSeverity.LOW, score_contribution=0, description="")


class SharedIPAddressRule:
    rule_id = "RULE_005"
    signal_type = "shared_ip_address"
    weight = 10

    def evaluate(self, ctx: RuleContext) -> SignalResult:
        if not ctx.submission_meta:
            return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                                severity=SignalSeverity.LOW, score_contribution=0, description="")

        from ..models.metadata import SubmissionMetadata
        from ..models.application import Application as App

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        ip_hash = ctx.submission_meta.ip_hash

        count = ctx.db.execute(
            select(func.count(SubmissionMetadata.id))
            .join(App, App.id == SubmissionMetadata.application_id)
            .where(SubmissionMetadata.ip_hash == ip_hash)
            .where(SubmissionMetadata.application_id != ctx.application.id)
            .where(App.submitted_at >= thirty_days_ago)
        ).scalar() or 0

        if count >= 3:
            severity = SignalSeverity.CRITICAL if count >= 6 else SignalSeverity.HIGH
            return SignalResult(
                triggered=True,
                rule_id=self.rule_id,
                signal_type=self.signal_type,
                severity=severity,
                score_contribution=self.weight,
                description=f"IP address linked to {count} other applications in the last 30 days. Possible bulk submission.",
                metadata={"ip_matches_30_days": int(count)},
            )
        return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                            severity=SignalSeverity.LOW, score_contribution=0, description="")


class DuplicateSSNRule:
    rule_id = "RULE_006"
    signal_type = "duplicate_ssn"
    weight = 20

    def evaluate(self, ctx: RuleContext) -> SignalResult:
        from ..models.applicant import Applicant as ApplicantModel

        count = ctx.db.execute(
            select(func.count(ApplicantModel.id))
            .where(ApplicantModel.ssn_hash == ctx.applicant.ssn_hash)
            .where(ApplicantModel.id != ctx.applicant.id)
        ).scalar() or 0

        if count > 0:
            return SignalResult(
                triggered=True,
                rule_id=self.rule_id,
                signal_type=self.signal_type,
                severity=SignalSeverity.CRITICAL,
                score_contribution=self.weight,
                description=f"SSN is associated with {count} other applicant record(s). Possible identity duplication or fraud ring.",
                metadata={"duplicate_count": int(count)},
            )
        return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                            severity=SignalSeverity.LOW, score_contribution=0, description="")


class OutOfStateUsageRule:
    rule_id = "RULE_007"
    signal_type = "out_of_state_usage"
    weight = 8

    def evaluate(self, ctx: RuleContext) -> SignalResult:
        if not ctx.applicant.addresses or not ctx.weekly_certs:
            return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                                severity=SignalSeverity.LOW, score_contribution=0, description="")

        primary_state = next((a.state for a in ctx.applicant.addresses if a.is_primary), None)
        if not primary_state:
            return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                                severity=SignalSeverity.LOW, score_contribution=0, description="")

        out_of_state_ips = []
        for cert in ctx.weekly_certs:
            if cert.submitted_ip:
                # Embedded state code in IP for seed data: format "XX.x.x.x" where XX is state code
                parts = cert.submitted_ip.split(".")
                if len(parts) >= 1 and len(parts[0]) == 2 and parts[0].isalpha():
                    cert_state = parts[0].upper()
                    if cert_state != primary_state:
                        out_of_state_ips.append((cert.submitted_ip, cert_state))

        if out_of_state_ips:
            states = list(set(s for _, s in out_of_state_ips))
            return SignalResult(
                triggered=True,
                rule_id=self.rule_id,
                signal_type=self.signal_type,
                severity=SignalSeverity.MEDIUM,
                score_contribution=self.weight,
                description=f"Weekly certifications submitted from state(s) {', '.join(states)} while registered address is in {primary_state}.",
                metadata={"registered_state": primary_state, "cert_states": states},
            )
        return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                            severity=SignalSeverity.LOW, score_contribution=0, description="")


class BulkSubmissionTimingRule:
    rule_id = "RULE_008"
    signal_type = "bulk_submission_timing"
    weight = 5

    def evaluate(self, ctx: RuleContext) -> SignalResult:
        from ..models.application import Application as App

        window_start = ctx.application.submitted_at - timedelta(seconds=60)
        window_end = ctx.application.submitted_at + timedelta(seconds=60)

        nearby = ctx.db.execute(
            select(func.count(App.id))
            .where(App.submitted_at.between(window_start, window_end))
            .where(App.id != ctx.application.id)
        ).scalar() or 0

        if nearby >= 5:
            return SignalResult(
                triggered=True,
                rule_id=self.rule_id,
                signal_type=self.signal_type,
                severity=SignalSeverity.MEDIUM,
                score_contribution=self.weight,
                description=f"{nearby} other applications submitted within 60 seconds of this one. Possible automated bulk submission.",
                metadata={"nearby_applications": int(nearby)},
            )
        return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                            severity=SignalSeverity.LOW, score_contribution=0, description="")


class FakeJobSearchRule:
    rule_id = "RULE_009"
    signal_type = "fake_job_search"
    weight = 8

    def evaluate(self, ctx: RuleContext) -> SignalResult:
        if len(ctx.weekly_certs) < 3:
            return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                                severity=SignalSeverity.LOW, score_contribution=0, description="")

        contacts = [c.job_search_contacts for c in ctx.weekly_certs]
        if len(set(contacts)) == 1 and contacts[0] <= 3:
            return SignalResult(
                triggered=True,
                rule_id=self.rule_id,
                signal_type=self.signal_type,
                severity=SignalSeverity.MEDIUM,
                score_contribution=self.weight,
                description=f"Job search contacts reported as exactly {contacts[0]} every single week across {len(contacts)} certifications. Suspiciously uniform — possible fabrication.",
                metadata={"reported_contacts_per_week": contacts[0], "weeks": len(contacts)},
            )
        return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                            severity=SignalSeverity.LOW, score_contribution=0, description="")


class DeceasedApplicantRule:
    rule_id = "RULE_010"
    signal_type = "deceased_applicant"
    weight = 20

    def evaluate(self, ctx: RuleContext) -> SignalResult:
        if ctx.applicant.is_deceased:
            return SignalResult(
                triggered=True,
                rule_id=self.rule_id,
                signal_type=self.signal_type,
                severity=SignalSeverity.CRITICAL,
                score_contribution=self.weight,
                description="Applicant is flagged as deceased in the system. This application may represent identity theft or posthumous fraud.",
                metadata={"dob": str(ctx.applicant.dob), "is_deceased": True},
            )
        return SignalResult(triggered=False, rule_id=self.rule_id, signal_type=self.signal_type,
                            severity=SignalSeverity.LOW, score_contribution=0, description="")


ALL_RULES: list[FraudRule] = [
    StillEmployedRule(),
    IncomeDuringClaimRule(),
    SharedBankAccountRule(),
    SharedDeviceFingerprintRule(),
    SharedIPAddressRule(),
    DuplicateSSNRule(),
    OutOfStateUsageRule(),
    BulkSubmissionTimingRule(),
    FakeJobSearchRule(),
    DeceasedApplicantRule(),
]


def run_fraud_analysis(application_id: uuid.UUID, db: Session) -> tuple[int, list[SignalResult]]:
    from sqlalchemy.orm import selectinload

    app = db.execute(
        select(Application)
        .options(
            selectinload(Application.applicant).selectinload(Applicant.addresses),
            selectinload(Application.applicant).selectinload(Applicant.financial_records),
            selectinload(Application.applicant).selectinload(Applicant.household_members),
            selectinload(Application.employment_history),
            selectinload(Application.weekly_certifications),
            selectinload(Application.submission_metadata),
        )
        .where(Application.id == application_id)
    ).scalar_one_or_none()

    if not app:
        raise ValueError(f"Application {application_id} not found")

    ctx = RuleContext(
        db=db,
        application=app,
        applicant=app.applicant,
        employment_history=app.employment_history,
        weekly_certs=app.weekly_certifications,
        financial_records=app.applicant.financial_records,
        submission_meta=app.submission_metadata,
        household_members=app.applicant.household_members,
    )

    db.execute(
        FraudSignal.__table__.delete().where(FraudSignal.application_id == application_id)
    )

    results = []
    triggered_signals = []

    for rule in ALL_RULES:
        result = rule.evaluate(ctx)
        results.append(result)
        if result.triggered:
            triggered_signals.append(FraudSignal(
                application_id=application_id,
                rule_id=result.rule_id,
                signal_type=result.signal_type,
                severity=result.severity,
                score_contribution=result.score_contribution,
                description=result.description,
                signal_metadata=result.metadata,
            ))

    db.add_all(triggered_signals)

    risk_score = min(100, sum(s.score_contribution for s in results if s.triggered))
    app.risk_score = risk_score
    app.last_analyzed_at = datetime.utcnow()
    db.commit()

    return risk_score, [r for r in results if r.triggered]
