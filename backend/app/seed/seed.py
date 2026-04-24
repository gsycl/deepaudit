"""
Seed script: populates the database with realistic unemployment fraud scenarios.
Run: python -m app.seed.seed
"""
import asyncio
import hashlib
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
    EmploymentHistory, WeeklyCertification, FinancialRecord,
    FraudSignal, HouseholdMember,
)
from app.models.metadata import SubmissionMetadata
from app.services.fraud_engine import run_fraud_analysis
from app.services.claude_service import get_ai_recommendation, apply_ai_result_to_application
from app.seed.patterns import (
    PATTERN_A, PATTERN_B, PATTERN_C, PATTERN_D,
    FRAUD_RING_SUBMITTED_AT, FRAUD_RING_IP_HASH, FRAUD_RING_DEVICE_FP,
    DEVICE_CLUSTER_FP, DEVICE_CLUSTER_IP_HASH,
    sha256,
)

fake = Faker()
Faker.seed(42)


def days_ago(n: int) -> datetime:
    return datetime.utcnow() - timedelta(days=n)


def date_from_days_ago(n: int) -> date:
    return (datetime.utcnow() - timedelta(days=n)).date()


def make_cert_weeks(application_id, n_weeks=8, contacts=None, out_state=None):
    certs = []
    for i in range(n_weeks):
        week_start = date_from_days_ago((n_weeks - i) * 7)
        submitted_ip = None
        if out_state:
            submitted_ip = f"{out_state}.{fake.random_int(1, 254)}.{fake.random_int(1, 254)}.{fake.random_int(1, 254)}"
        certs.append(WeeklyCertification(
            application_id=application_id,
            week_start=week_start,
            did_work=False,
            reported_earnings=Decimal("0.00"),
            job_search_contacts=contacts if contacts is not None else fake.random_int(1, 5),
            submitted_ip=submitted_ip or f"IL.{fake.random_int(1, 254)}.{fake.random_int(1, 254)}.{fake.random_int(1, 254)}",
        ))
    return certs


def create_applicant_with_address(db: Session, data: dict) -> Applicant:
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

    addr_data = data.get("address", {
        "street": fake.street_address(),
        "city": fake.city(),
        "state": data.get("state", fake.state_abbr()),
        "zip_code": fake.zipcode(),
        "lat": float(fake.latitude()),
        "lon": float(fake.longitude()),
    })

    address = Address(
        applicant_id=applicant.id,
        street=addr_data["street"],
        city=addr_data["city"],
        state=addr_data["state"],
        zip_code=addr_data["zip_code"],
        lat=addr_data.get("lat"),
        lon=addr_data.get("lon"),
        is_primary=True,
    )
    db.add(address)

    financial = FinancialRecord(
        applicant_id=applicant.id,
        bank_account_hash=data["bank_account_hash"],
        institution_name=fake.company() + " Bank",
        account_type="checking",
        monthly_income_reported=Decimal(str(data.get("monthly_income", 3000))),
    )
    db.add(financial)
    db.flush()
    return applicant


def create_application(db: Session, applicant: Application, emp_data: dict,
                        weekly_benefit: float, submitted_at: datetime,
                        device_fp: str = None, ip_hash: str = None,
                        cert_contacts: int = None, out_state: str = None) -> Application:
    state = applicant.addresses[0].state if applicant.addresses else "IL"

    app = Application(
        applicant_id=applicant.id,
        program_type=ProgramType.UNEMPLOYMENT,
        status=ApplicationStatus.PENDING,
        submitted_at=submitted_at,
        weekly_benefit_amount=Decimal(str(weekly_benefit)),
        claim_start_date=date_from_days_ago(90),
        claim_end_date=date_from_days_ago(0),
    )
    db.add(app)
    db.flush()

    emp = EmploymentHistory(
        application_id=app.id,
        employer_name=emp_data["employer_name"],
        employer_ein_hash=emp_data.get("employer_ein_hash"),
        start_date=emp_data["start_date"],
        end_date=emp_data.get("end_date"),
        separation_reason=emp_data["separation_reason"],
        reported_salary=Decimal(str(emp_data.get("reported_salary", 40000))),
        is_verified=False,
    )
    db.add(emp)

    certs = make_cert_weeks(app.id, n_weeks=8, contacts=cert_contacts, out_state=out_state)
    db.add_all(certs)

    meta = SubmissionMetadata(
        application_id=app.id,
        ip_address=f"10.0.0.{fake.random_int(1, 254)}",
        ip_hash=ip_hash or sha256(f"ip_{fake.ipv4()}_{app.id}"),
        device_fingerprint=device_fp or sha256(f"fp_{fake.uuid4()}"),
        user_agent=fake.user_agent(),
        time_to_complete_seconds=fake.random_int(120, 900),
        submitted_at=submitted_at,
    )
    db.add(meta)
    db.flush()
    return app


def seed_clean_applicants(db: Session, count: int = 35) -> list:
    apps = []
    for _ in range(count):
        state = fake.state_abbr()
        applicant_data = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "dob": fake.date_of_birth(minimum_age=22, maximum_age=62),
            "ssn_hash": sha256(f"clean_ssn_{fake.ssn()}_{fake.uuid4()}"),
            "phone": fake.phone_number(),
            "email": fake.email(),
            "bank_account_hash": sha256(f"clean_bank_{fake.bban()}_{fake.uuid4()}"),
            "monthly_income": fake.random_int(2000, 5000),
            "state": state,
        }
        applicant = create_applicant_with_address(db, applicant_data)

        emp_data = {
            "employer_name": fake.company(),
            "employer_ein_hash": sha256(f"ein_{fake.ein()}"),
            "start_date": fake.date_between(start_date="-5y", end_date="-6m"),
            "end_date": date_from_days_ago(fake.random_int(30, 90)),
            "separation_reason": fake.random_element(["laid_off", "quit"]),
            "reported_salary": fake.random_int(30000, 65000),
        }

        app = create_application(
            db, applicant, emp_data,
            weekly_benefit=fake.random_int(200, 400),
            submitted_at=days_ago(fake.random_int(1, 30)),
            cert_contacts=fake.random_int(1, 7),
        )
        apps.append(app)

    db.commit()
    print(f"  Created {count} clean applicants")
    return apps


def seed_pattern_a(db: Session) -> list:
    apps = []
    for member in PATTERN_A["members"]:
        applicant = create_applicant_with_address(db, member)
        offset = member["submitted_offset_seconds"]
        submitted_at = FRAUD_RING_SUBMITTED_AT + timedelta(seconds=offset)

        app = create_application(
            db, applicant, member["employment"],
            weekly_benefit=member["weekly_benefit"],
            submitted_at=submitted_at,
            device_fp=FRAUD_RING_DEVICE_FP,
            ip_hash=FRAUD_RING_IP_HASH,
        )
        apps.append(app)

    db.commit()
    print(f"  Created Pattern A (Fraud Ring): {len(apps)} applications")
    return apps


def seed_pattern_b(db: Session) -> list:
    apps = []
    for member in PATTERN_B["members"]:
        applicant = create_applicant_with_address(db, member)
        app = create_application(
            db, applicant, member["employment"],
            weekly_benefit=member["weekly_benefit"],
            submitted_at=days_ago(fake.random_int(5, 15)),
            cert_contacts=member["cert_contacts"],
        )
        apps.append(app)

    db.commit()
    print(f"  Created Pattern B (Income Misreporting): {len(apps)} applications")
    return apps


def seed_pattern_c(db: Session) -> list:
    apps = []
    for member in PATTERN_C["members"]:
        state = member["state"]
        member["address"] = {
            "street": fake.street_address(),
            "city": fake.city(),
            "state": state,
            "zip_code": fake.zipcode(),
        }
        applicant = create_applicant_with_address(db, member)
        app = create_application(
            db, applicant, member["employment"],
            weekly_benefit=member["weekly_benefit"],
            submitted_at=days_ago(fake.random_int(2, 10)),
            device_fp=DEVICE_CLUSTER_FP,
            ip_hash=DEVICE_CLUSTER_IP_HASH,
            out_state="TX",  # Certs submitted from TX regardless of home state
        )
        apps.append(app)

    db.commit()
    print(f"  Created Pattern C (Device Cluster): {len(apps)} applications")
    return apps


def seed_pattern_d(db: Session) -> list:
    member = PATTERN_D["member"]
    applicant = create_applicant_with_address(db, member)
    app = create_application(
        db, applicant, member["employment"],
        weekly_benefit=member["weekly_benefit"],
        submitted_at=days_ago(2),
        device_fp=member["device_fingerprint"],
        ip_hash=DEVICE_CLUSTER_IP_HASH,
    )
    db.commit()
    print(f"  Created Pattern D (Deceased Applicant): 1 application")
    return [app]


async def run_ai_on_high_risk(db: Session, all_apps: list):
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models import Application, Applicant

    high_risk_ids = [a.id for a in all_apps if (a.risk_score or 0) > 30]
    print(f"\n  Running Claude AI analysis on {len(high_risk_ids)} high-risk applications...")

    for app_id in high_risk_ids:
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
            print(f"    ✓ {app.id} → {result.get('recommendation', 'N/A')}")
        except Exception as e:
            print(f"    ✗ {app_id}: {e}")


async def main():
    print("DeepAudit Seed Script")
    print("=" * 50)

    print("\nDropping and recreating all tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("  Tables created.")

    db = SessionLocal()
    all_apps = []

    try:
        print("\nSeeding data...")
        all_apps.extend(seed_clean_applicants(db, count=35))
        all_apps.extend(seed_pattern_a(db))
        all_apps.extend(seed_pattern_b(db))
        all_apps.extend(seed_pattern_c(db))
        all_apps.extend(seed_pattern_d(db))

        print(f"\nRunning fraud analysis on {len(all_apps)} applications...")
        for app in all_apps:
            risk_score, signals = run_fraud_analysis(app.id, db)
            app.risk_score = risk_score

        db.commit()
        print("  Fraud analysis complete.")

        high_risk = [a for a in all_apps if (a.risk_score or 0) > 30]
        print(f"\n  Risk score summary:")
        print(f"    High risk (>70):   {sum(1 for a in all_apps if (a.risk_score or 0) > 70)}")
        print(f"    Medium risk (30-70): {sum(1 for a in all_apps if 30 < (a.risk_score or 0) <= 70)}")
        print(f"    Low risk (<30):    {sum(1 for a in all_apps if (a.risk_score or 0) <= 30)}")

        await run_ai_on_high_risk(db, all_apps)

    finally:
        db.close()

    print("\n" + "=" * 50)
    print(f"Seed complete! Total applications: {len(all_apps)}")
    print("Start the server: uvicorn app.main:app --reload")
    print("View API docs:    http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(main())
