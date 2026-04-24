"""
Fraud pattern definitions for seed data.
Each pattern is a dict describing the setup. The seed orchestrator uses these.
"""
import hashlib
from datetime import datetime, timedelta, date


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def days_ago(n: int) -> datetime:
    return datetime.utcnow() - timedelta(days=n)


def date_ago(n: int) -> date:
    return (datetime.utcnow() - timedelta(days=n)).date()


FRAUD_RING_BANK_HASH = sha256("routing_021000089_acct_987654321_ring")
FRAUD_RING_IP_HASH = sha256("192.168.99.1")
FRAUD_RING_DEVICE_FP = sha256("device_ring_botfarm_001")
FRAUD_RING_ADDRESS = {
    "street": "742 Evergreen Terrace",
    "city": "Springfield",
    "state": "IL",
    "zip_code": "62701",
    "lat": 39.7817,
    "lon": -89.6501,
}
FRAUD_RING_SUBMITTED_AT = days_ago(3)

DEVICE_CLUSTER_FP = sha256("device_botfarm_cluster_002")
DEVICE_CLUSTER_IP_HASH = sha256("10.0.0.55")

PATTERN_A = {
    "name": "Fraud Ring",
    "description": "3 applicants sharing address, bank account, and bulk submission timing",
    "members": [
        {
            "first_name": "Alice",
            "last_name": "Johnson",
            "dob": date(1985, 4, 12),
            "ssn_hash": sha256("ssn_alice_johnson_123456789"),
            "phone": "312-555-0101",
            "email": "alice.j.benefits@gmail.com",
            "bank_account_hash": FRAUD_RING_BANK_HASH,
            "monthly_income": 4200,
            "employment": {
                "employer_name": "Midwest Distribution LLC",
                "employer_ein_hash": sha256("ein_midwest_dist_91-1234567"),
                "start_date": date(2022, 3, 1),
                "end_date": date_ago(-10),  # 10 days in the future!
                "separation_reason": "laid_off",
                "reported_salary": 52000,
            },
            "address": FRAUD_RING_ADDRESS,
            "weekly_benefit": 387.00,
            "submitted_offset_seconds": 0,
        },
        {
            "first_name": "Bob",
            "last_name": "Martinez",
            "dob": date(1979, 11, 3),
            "ssn_hash": sha256("ssn_bob_martinez_987654321"),
            "phone": "312-555-0102",
            "email": "bm_claims_2024@hotmail.com",
            "bank_account_hash": FRAUD_RING_BANK_HASH,
            "monthly_income": 3800,
            "employment": {
                "employer_name": "Midwest Distribution LLC",
                "employer_ein_hash": sha256("ein_midwest_dist_91-1234567"),
                "start_date": date(2021, 7, 15),
                "end_date": date_ago(-5),  # 5 days in the future!
                "separation_reason": "laid_off",
                "reported_salary": 47000,
            },
            "address": FRAUD_RING_ADDRESS,
            "weekly_benefit": 351.00,
            "submitted_offset_seconds": 28,
        },
        {
            "first_name": "Carol",
            "last_name": "White",
            "dob": date(1991, 8, 22),
            "ssn_hash": sha256("ssn_carol_white_555444333"),
            "phone": "312-555-0103",
            "email": "carol.white.ui@yahoo.com",
            "bank_account_hash": FRAUD_RING_BANK_HASH,
            "monthly_income": 3500,
            "employment": {
                "employer_name": "Midwest Distribution LLC",
                "employer_ein_hash": sha256("ein_midwest_dist_91-1234567"),
                "start_date": date(2023, 1, 10),
                "end_date": None,  # Missing end date!
                "separation_reason": "laid_off",
                "reported_salary": 44000,
            },
            "address": FRAUD_RING_ADDRESS,
            "weekly_benefit": 322.00,
            "submitted_offset_seconds": 44,
        },
    ],
}

PATTERN_B = {
    "name": "Income Misreporting Cluster",
    "description": "4 applicants with income inconsistent with zero-earnings certifications and uniform fake job search",
    "members": [
        {
            "first_name": "David",
            "last_name": "Kim",
            "dob": date(1982, 6, 30),
            "ssn_hash": sha256("ssn_david_kim_111222333"),
            "phone": "773-555-0201",
            "email": "davidkim82@gmail.com",
            "bank_account_hash": sha256("bank_david_kim_unique"),
            "monthly_income": 6500,
            "employment": {
                "employer_name": "TechCore Solutions Inc",
                "employer_ein_hash": sha256("ein_techcore_82-3456789"),
                "start_date": date(2020, 2, 1),
                "end_date": date_ago(45),
                "separation_reason": "laid_off",
                "reported_salary": 78000,
            },
            "address": {"street": "1200 N Lake Shore Dr", "city": "Chicago", "state": "IL", "zip_code": "60610", "lat": 41.9, "lon": -87.63},
            "weekly_benefit": 497.00,
            "cert_contacts": 3,
        },
        {
            "first_name": "Emily",
            "last_name": "Chen",
            "dob": date(1990, 3, 17),
            "ssn_hash": sha256("ssn_emily_chen_222333444"),
            "phone": "773-555-0202",
            "email": "echen.chicago@outlook.com",
            "bank_account_hash": sha256("bank_emily_chen_unique"),
            "monthly_income": 5800,
            "employment": {
                "employer_name": "Global Analytics Partners",
                "employer_ein_hash": sha256("ein_global_analytics_83-4567890"),
                "start_date": date(2019, 5, 20),
                "end_date": date_ago(30),
                "separation_reason": "laid_off",
                "reported_salary": 69000,
            },
            "address": {"street": "845 W Diversey Pkwy", "city": "Chicago", "state": "IL", "zip_code": "60614", "lat": 41.93, "lon": -87.65},
            "weekly_benefit": 456.00,
            "cert_contacts": 3,
        },
        {
            "first_name": "Frank",
            "last_name": "Torres",
            "dob": date(1975, 9, 5),
            "ssn_hash": sha256("ssn_frank_torres_333444555"),
            "phone": "773-555-0203",
            "email": "ftorres1975@comcast.net",
            "bank_account_hash": sha256("bank_frank_torres_unique"),
            "monthly_income": 7200,
            "employment": {
                "employer_name": "Apex Manufacturing Group",
                "employer_ein_hash": sha256("ein_apex_mfg_84-5678901"),
                "start_date": date(2018, 11, 1),
                "end_date": date_ago(60),
                "separation_reason": "laid_off",
                "reported_salary": 86000,
            },
            "address": {"street": "3300 S Michigan Ave", "city": "Chicago", "state": "IL", "zip_code": "60616", "lat": 41.83, "lon": -87.62},
            "weekly_benefit": 497.00,
            "cert_contacts": 3,
        },
        {
            "first_name": "Grace",
            "last_name": "Liu",
            "dob": date(1988, 12, 28),
            "ssn_hash": sha256("ssn_grace_liu_444555666"),
            "phone": "773-555-0204",
            "email": "grace.liu.ui@gmail.com",
            "bank_account_hash": sha256("bank_grace_liu_unique"),
            "monthly_income": 5200,
            "employment": {
                "employer_name": "Pinnacle Consulting Services",
                "employer_ein_hash": sha256("ein_pinnacle_85-6789012"),
                "start_date": date(2021, 4, 1),
                "end_date": date_ago(20),
                "separation_reason": "laid_off",
                "reported_salary": 62000,
            },
            "address": {"street": "2100 N Halsted St", "city": "Chicago", "state": "IL", "zip_code": "60614", "lat": 41.92, "lon": -87.65},
            "weekly_benefit": 420.00,
            "cert_contacts": 3,
        },
    ],
}

PATTERN_C_STATES = ["TX", "CA", "NY", "FL", "WA"]
PATTERN_C = {
    "name": "Device Fingerprint Cluster",
    "description": "5 applicants from different states using the same device and IP",
    "members": [
        {
            "first_name": fn, "last_name": ln,
            "dob": date(1983 + i, (i + 1) * 2, 10 + i),
            "ssn_hash": sha256(f"ssn_cluster_c_{i}"),
            "phone": f"555-555-0{300 + i}",
            "email": f"cluster_c_{i}@tempmail.com",
            "bank_account_hash": sha256(f"bank_cluster_c_{i}_unique"),
            "monthly_income": 3000 + i * 200,
            "state": PATTERN_C_STATES[i],
            "employment": {
                "employer_name": f"Employer {chr(65 + i)} Corp",
                "employer_ein_hash": sha256(f"ein_cluster_c_{i}"),
                "start_date": date(2020 + i % 3, 3, 1),
                "end_date": date_ago(15 + i * 5),
                "separation_reason": "laid_off",
                "reported_salary": 40000 + i * 3000,
            },
            "weekly_benefit": 300.00 + i * 15,
            "device_fingerprint": DEVICE_CLUSTER_FP,
            "ip_hash": DEVICE_CLUSTER_IP_HASH,
        }
        for i, (fn, ln) in enumerate([
            ("James", "Wright"),
            ("Maria", "Gonzalez"),
            ("Kevin", "Brown"),
            ("Sarah", "Davis"),
            ("Michael", "Wilson"),
        ])
    ],
}

PATTERN_D = {
    "name": "Deceased Applicant",
    "description": "Application filed using the identity of a deceased person",
    "member": {
        "first_name": "Harold",
        "last_name": "Graves",
        "dob": date(1935, 3, 15),
        "is_deceased": True,
        "ssn_hash": sha256("ssn_harold_graves_deceased_666777888"),
        "phone": "555-555-0400",
        "email": "harold.graves.1935@gmail.com",
        "bank_account_hash": sha256("bank_harold_graves_suspicious"),
        "monthly_income": 2800,
        "device_fingerprint": DEVICE_CLUSTER_FP,
        "employment": {
            "employer_name": "RetireRight Consulting",
            "employer_ein_hash": sha256("ein_retireright_86-7890123"),
            "start_date": date(2023, 1, 1),
            "end_date": date_ago(10),
            "separation_reason": "laid_off",
            "reported_salary": 33000,
        },
        "address": {"street": "900 Cemetery Rd", "city": "Decatur", "state": "IL", "zip_code": "62521", "lat": 39.84, "lon": -88.95},
        "weekly_benefit": 280.00,
    },
}
