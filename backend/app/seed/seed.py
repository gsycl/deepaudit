"""
Seed script: populates the database with 100+ realistic unemployment fraud scenarios.
Run: python -m app.seed.seed
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta, date
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from faker import Faker
from sqlalchemy.orm import Session

from app.database import engine, Base, SessionLocal
from app.models import (
    Applicant, Address, Application, ApplicationStatus, ProgramType,
    EmploymentHistory, WeeklyCertification, FinancialRecord, HouseholdMember,
)
from app.models.metadata import SubmissionMetadata
from app.services.fraud_engine import run_fraud_analysis
from app.services.claude_service import get_ai_recommendation, apply_ai_result_to_application
from app.seed.patterns import (
    sha256,
    PATTERN_A, FRAUD_RING_A_AT, FRAUD_RING_A_IP, FRAUD_RING_A_DEVICE,
    PATTERN_B,
    PATTERN_C, DEVICE_CLUSTER_FP, DEVICE_CLUSTER_IP,
    PATTERN_D,
    PATTERN_E, FRAUD_RING_E_AT, FRAUD_RING_E_IP, FRAUD_RING_E_DEVICE,
    PATTERN_F,
    PATTERN_G, BOTFARM_AT, BOTFARM_IP, BOTFARM_DEVICE,
    PATTERN_H, EMPLOYER_COLLUSION_AT,
    PATTERN_I,
    PATTERN_J,
)

fake = Faker()
Faker.seed(42)

# ── helpers ───────────────────────────────────────────────────────────────────

def days_ago(n: int) -> datetime:
    return datetime.utcnow() - timedelta(days=n)


def date_ago(n: int) -> date:
    return (datetime.utcnow() - timedelta(days=n)).date()


def make_certs(application_id, n_weeks=8, contacts=None, out_state=None, home_state="IL"):
    certs = []
    for i in range(n_weeks):
        week_start = date_ago((n_weeks - i) * 7)
        if out_state:
            ip = f"{out_state}.{fake.random_int(1,254)}.{fake.random_int(1,254)}.{fake.random_int(1,254)}"
        else:
            ip = f"{home_state}.{fake.random_int(1,254)}.{fake.random_int(1,254)}.{fake.random_int(1,254)}"
        certs.append(WeeklyCertification(
            application_id=application_id,
            week_start=week_start,
            did_work=False,
            reported_earnings=Decimal("0.00"),
            job_search_contacts=contacts if contacts is not None else fake.random_int(1, 7),
            submitted_ip=ip,
        ))
    return certs


def make_applicant(db: Session, data: dict) -> Applicant:
    applicant = Applicant(
        ssn_hash=data["ssn_hash"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        dob=data["dob"],
        phone=data.get("phone", fake.phone_number()),
        email=data.get("email", fake.email()),
        is_deceased=data.get("is_deceased", False),
    )
    db.add(applicant)
    db.flush()

    addr = data.get("address") or {
        "street": fake.street_address(),
        "city": fake.city(),
        "state": data.get("state", "IL"),
        "zip_code": fake.zipcode(),
    }
    db.add(Address(
        applicant_id=applicant.id,
        street=addr["street"], city=addr["city"],
        state=addr["state"], zip_code=addr["zip_code"],
        lat=addr.get("lat"), lon=addr.get("lon"),
        is_primary=True,
    ))
    db.add(FinancialRecord(
        applicant_id=applicant.id,
        bank_account_hash=data["bank_account_hash"],
        institution_name=fake.company() + " Bank",
        account_type="checking",
        monthly_income_reported=Decimal(str(data.get("monthly_income", 3000))),
    ))
    db.flush()
    return applicant


def make_application(
    db: Session,
    applicant: Applicant,
    emp_data: dict,
    weekly_benefit: float,
    submitted_at: datetime,
    device_fp: str = None,
    ip_hash: str = None,
    cert_contacts: int = None,
    out_state: str = None,
    status: ApplicationStatus = ApplicationStatus.PENDING,
) -> Application:
    home_state = applicant.addresses[0].state if applicant.addresses else "IL"

    app = Application(
        applicant_id=applicant.id,
        program_type=ProgramType.UNEMPLOYMENT,
        status=status,
        submitted_at=submitted_at,
        weekly_benefit_amount=Decimal(str(weekly_benefit)),
        claim_start_date=date_ago(90),
        claim_end_date=date_ago(0),
    )
    db.add(app)
    db.flush()

    db.add(EmploymentHistory(
        application_id=app.id,
        employer_name=emp_data["employer_name"],
        employer_ein_hash=emp_data.get("employer_ein_hash"),
        start_date=emp_data["start_date"],
        end_date=emp_data.get("end_date"),
        separation_reason=emp_data["separation_reason"],
        reported_salary=Decimal(str(emp_data.get("reported_salary", 40000))),
        is_verified=False,
    ))

    db.add_all(make_certs(app.id, contacts=cert_contacts, out_state=out_state, home_state=home_state))

    db.add(SubmissionMetadata(
        application_id=app.id,
        ip_address=f"10.0.0.{fake.random_int(1, 254)}",
        ip_hash=ip_hash or sha256(f"ip_{fake.ipv4()}_{app.id}"),
        device_fingerprint=device_fp or sha256(f"fp_{fake.uuid4()}"),
        user_agent=fake.user_agent(),
        time_to_complete_seconds=fake.random_int(90, 900),
        submitted_at=submitted_at,
    ))
    db.flush()
    return app


# ── pattern seeders ───────────────────────────────────────────────────────────

def seed_clean(db: Session, count: int = 65) -> list:
    apps = []
    statuses = [ApplicationStatus.PENDING] * 40 + [ApplicationStatus.APPROVED] * 15 + [ApplicationStatus.DENIED] * 10
    for i in range(count):
        state = fake.state_abbr()
        applicant = make_applicant(db, {
            "first_name": fake.first_name(), "last_name": fake.last_name(),
            "dob": fake.date_of_birth(minimum_age=22, maximum_age=62),
            "ssn_hash": sha256(f"clean_ssn_{fake.ssn()}_{fake.uuid4()}"),
            "phone": fake.phone_number(), "email": fake.email(),
            "bank_account_hash": sha256(f"clean_bank_{fake.bban()}_{fake.uuid4()}"),
            "monthly_income": fake.random_int(1800, 5500),
            "state": state,
        })
        emp = {
            "employer_name": fake.company(),
            "employer_ein_hash": sha256(f"ein_{fake.ein()}"),
            "start_date": fake.date_between(start_date="-5y", end_date="-6m"),
            "end_date": date_ago(fake.random_int(15, 120)),
            "separation_reason": fake.random_element(["laid_off", "laid_off", "quit"]),
            "reported_salary": fake.random_int(28000, 70000),
        }
        app = make_application(
            db, applicant, emp,
            weekly_benefit=fake.random_int(180, 450),
            submitted_at=days_ago(fake.random_int(1, 60)),
            cert_contacts=fake.random_int(1, 7),
            status=statuses[i % len(statuses)],
        )
        apps.append(app)
    db.commit()
    print(f"  ✓ Clean applicants: {count}")
    return apps


def seed_pattern(db: Session, pattern: dict, base_time: datetime = None,
                 base_ip: str = None, base_device: str = None,
                 out_state: str = None, label: str = "") -> list:
    apps = []
    members = pattern.get("members", [pattern.get("member")])
    base_time = base_time or days_ago(fake.random_int(2, 14))

    for member in members:
        applicant = make_applicant(db, member)
        offset = member.get("submitted_offset_seconds", 0)
        app = make_application(
            db, applicant,
            emp_data=member["employment"],
            weekly_benefit=member["weekly_benefit"],
            submitted_at=base_time + timedelta(seconds=offset),
            device_fp=member.get("device_fingerprint") or base_device,
            ip_hash=member.get("ip_hash") or base_ip,
            cert_contacts=member.get("cert_contacts"),
            out_state=member.get("out_state") or out_state,
        )
        apps.append(app)
    db.commit()
    print(f"  ✓ {label or pattern['name']}: {len(apps)} applications")
    return apps


# ── AI analysis ───────────────────────────────────────────────────────────────

async def run_ai(db: Session, all_apps: list):
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select

    high_risk = [a.id for a in all_apps if (a.risk_score or 0) > 25]
    print(f"\n  Running mock AI analysis on {len(high_risk)} applications (risk > 25)...")

    for app_id in high_risk:
        try:
            app = db.execute(
                select(Application)
                .options(
                    selectinload(Application.applicant).selectinload(Applicant.addresses),
                    selectinload(Application.employment_history),
                    selectinload(Application.weekly_certifications),
                    selectinload(Application.fraud_signals),
                )
                .where(Application.id == app_id)
            ).scalar_one()
            result = await get_ai_recommendation(app, app.fraud_signals, app.applicant)
            apply_ai_result_to_application(app, result)
            db.commit()
        except Exception as e:
            print(f"    ✗ {app_id}: {e}")

    print(f"  ✓ AI analysis complete")


# ── main ──────────────────────────────────────────────────────────────────────

async def main():
    print("DeepAudit Seed Script — Extended")
    print("=" * 50)

    print("\nDropping and recreating all tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("  Tables ready.")

    db = SessionLocal()
    all_apps = []

    try:
        print("\nSeeding patterns...")

        # Control group — clean applicants (mix of pending/approved/denied)
        all_apps += seed_clean(db, count=65)

        # A: Fraud ring — shared bank + address + device + bulk timing + still employed
        all_apps += seed_pattern(db, PATTERN_A, base_time=FRAUD_RING_A_AT, base_ip=FRAUD_RING_A_IP, base_device=FRAUD_RING_A_DEVICE, label="Pattern A — Fraud Ring Alpha")

        # B: Income misreporting — high monthly income vs zero-earnings certifications + fake job search
        all_apps += seed_pattern(db, PATTERN_B, label="Pattern B — Income Misreporting")

        # C: Device/IP cluster — same device + IP, 5 states, out-of-state certs
        all_apps += seed_pattern(db, PATTERN_C, base_device=DEVICE_CLUSTER_FP, base_ip=DEVICE_CLUSTER_IP, out_state="TX", label="Pattern C — Device/IP Cluster")

        # D: Deceased applicants
        all_apps += seed_pattern(db, PATTERN_D, label="Pattern D — Deceased Applicants")

        # E: Second fraud ring — different shared bank + address + still employed
        all_apps += seed_pattern(db, PATTERN_E, base_time=FRAUD_RING_E_AT, base_ip=FRAUD_RING_E_IP, base_device=FRAUD_RING_E_DEVICE, label="Pattern E — Fraud Ring Beta")

        # F: Duplicate SSN — identity theft, two applicants same SSN
        all_apps += seed_pattern(db, PATTERN_F, label="Pattern F — Duplicate SSN (Identity Theft)")

        # G: Bot farm — 8 people, same device + IP, all within 88 seconds
        all_apps += seed_pattern(db, PATTERN_G, base_time=BOTFARM_AT, base_ip=BOTFARM_IP, base_device=BOTFARM_DEVICE, label="Pattern G — Bot Farm Bulk Submission")

        # H: Employer collusion — 6 people same EIN, all claim layoff same week, still employed
        all_apps += seed_pattern(db, PATTERN_H, base_time=EMPLOYER_COLLUSION_AT, label="Pattern H — Employer Collusion")

        # I: Out-of-state seasonal claimants — IL registered, certifying from FL
        all_apps += seed_pattern(db, PATTERN_I, out_state="FL", label="Pattern I — Out-of-State Seasonal")

        # J: Working while claiming — high income + zero-earnings certs + uniform job search
        all_apps += seed_pattern(db, PATTERN_J, label="Pattern J — Working While Claiming")

        # Run fraud engine on every application
        print(f"\nRunning fraud engine on {len(all_apps)} applications...")
        for app in all_apps:
            risk_score, _ = run_fraud_analysis(app.id, db)
            app.risk_score = risk_score
        db.commit()
        print("  ✓ Fraud engine complete.")

        # Risk summary
        buckets = [(">80", 80), ("61-80", 60), ("31-60", 30), ("≤30", -1)]
        print("\n  Risk distribution:")
        print(f"    Critical  (>80):  {sum(1 for a in all_apps if (a.risk_score or 0) > 80)}")
        print(f"    High    (61-80):  {sum(1 for a in all_apps if 60 < (a.risk_score or 0) <= 80)}")
        print(f"    Medium  (31-60):  {sum(1 for a in all_apps if 30 < (a.risk_score or 0) <= 60)}")
        print(f"    Low       (≤30):  {sum(1 for a in all_apps if (a.risk_score or 0) <= 30)}")

        await run_ai(db, all_apps)

    finally:
        db.close()

    print("\n" + "=" * 50)
    print(f"Done! Total applications seeded: {len(all_apps)}")
    print("API docs: http://localhost:8000/docs")
    print("Frontend: http://localhost:5173")


if __name__ == "__main__":
    asyncio.run(main())
