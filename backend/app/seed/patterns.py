"""
Fraud pattern definitions. Each pattern is a self-contained dict the seed orchestrator reads.
"""
import hashlib
from datetime import datetime, timedelta, date


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def days_ago(n: int) -> datetime:
    return datetime.utcnow() - timedelta(days=n)


def date_ago(n: int) -> date:
    return (datetime.utcnow() - timedelta(days=n)).date()


# ── Shared constants ──────────────────────────────────────────────────────────

FRAUD_RING_A_BANK   = sha256("routing_021000089_acct_987654321_ring_A")
FRAUD_RING_A_IP     = sha256("192.168.99.1_ring_A")
FRAUD_RING_A_DEVICE = sha256("device_ring_A_botfarm")
FRAUD_RING_A_ADDR   = {"street": "742 Evergreen Terrace", "city": "Springfield", "state": "IL", "zip_code": "62701", "lat": 39.78, "lon": -89.65}
FRAUD_RING_A_AT     = days_ago(3)

FRAUD_RING_E_BANK   = sha256("routing_021000089_acct_111222333_ring_E")
FRAUD_RING_E_IP     = sha256("10.20.30.40_ring_E")
FRAUD_RING_E_DEVICE = sha256("device_ring_E_burner_phone")
FRAUD_RING_E_ADDR   = {"street": "18 Maple Commons Blvd", "city": "Aurora", "state": "IL", "zip_code": "60505", "lat": 41.76, "lon": -88.32}
FRAUD_RING_E_AT     = days_ago(5)

BOTFARM_IP     = sha256("185.220.101.45_tor_exit")
BOTFARM_DEVICE = sha256("device_botfarm_headless_chrome")
BOTFARM_AT     = days_ago(1)

DEVICE_CLUSTER_FP   = sha256("device_botfarm_cluster_002")
DEVICE_CLUSTER_IP   = sha256("10.0.0.55_cluster_C")

EMPLOYER_COLLUSION_EIN = sha256("ein_shady_staffing_77-9999999")
EMPLOYER_COLLUSION_AT  = days_ago(7)

DUP_SSN_HASH = sha256("ssn_duplicate_identity_theft_999888777")


# ── Pattern A: Fraud Ring (3 people, shared bank + address + device + bulk timing + still employed) ──

PATTERN_A = {
    "name": "Fraud Ring Alpha",
    "members": [
        {
            "first_name": "Alice", "last_name": "Johnson",
            "dob": date(1985, 4, 12),
            "ssn_hash": sha256("ssn_alice_johnson_123456789"),
            "phone": "312-555-0101", "email": "alice.j.benefits@gmail.com",
            "bank_account_hash": FRAUD_RING_A_BANK, "monthly_income": 4200,
            "address": FRAUD_RING_A_ADDR, "weekly_benefit": 387.00,
            "submitted_offset_seconds": 0,
            "employment": {"employer_name": "Midwest Distribution LLC", "employer_ein_hash": sha256("ein_midwest_dist_91-1234567"), "start_date": date(2022, 3, 1), "end_date": date_ago(-10), "separation_reason": "laid_off", "reported_salary": 52000},
        },
        {
            "first_name": "Bob", "last_name": "Martinez",
            "dob": date(1979, 11, 3),
            "ssn_hash": sha256("ssn_bob_martinez_987654321"),
            "phone": "312-555-0102", "email": "bm_claims_2024@hotmail.com",
            "bank_account_hash": FRAUD_RING_A_BANK, "monthly_income": 3800,
            "address": FRAUD_RING_A_ADDR, "weekly_benefit": 351.00,
            "submitted_offset_seconds": 28,
            "employment": {"employer_name": "Midwest Distribution LLC", "employer_ein_hash": sha256("ein_midwest_dist_91-1234567"), "start_date": date(2021, 7, 15), "end_date": date_ago(-5), "separation_reason": "laid_off", "reported_salary": 47000},
        },
        {
            "first_name": "Carol", "last_name": "White",
            "dob": date(1991, 8, 22),
            "ssn_hash": sha256("ssn_carol_white_555444333"),
            "phone": "312-555-0103", "email": "carol.white.ui@yahoo.com",
            "bank_account_hash": FRAUD_RING_A_BANK, "monthly_income": 3500,
            "address": FRAUD_RING_A_ADDR, "weekly_benefit": 322.00,
            "submitted_offset_seconds": 44,
            "employment": {"employer_name": "Midwest Distribution LLC", "employer_ein_hash": sha256("ein_midwest_dist_91-1234567"), "start_date": date(2023, 1, 10), "end_date": None, "separation_reason": "laid_off", "reported_salary": 44000},
        },
    ],
}


# ── Pattern B: Income Misreporting (4 people, high income + zero earnings certs + fake job search) ──

PATTERN_B = {
    "name": "Income Misreporting Cluster",
    "members": [
        {"first_name": "David", "last_name": "Kim", "dob": date(1982, 6, 30), "ssn_hash": sha256("ssn_david_kim_111222333"), "phone": "773-555-0201", "email": "davidkim82@gmail.com", "bank_account_hash": sha256("bank_david_kim_unique"), "monthly_income": 6500, "address": {"street": "1200 N Lake Shore Dr", "city": "Chicago", "state": "IL", "zip_code": "60610"}, "weekly_benefit": 497.00, "cert_contacts": 3, "employment": {"employer_name": "TechCore Solutions Inc", "employer_ein_hash": sha256("ein_techcore_82-3456789"), "start_date": date(2020, 2, 1), "end_date": date_ago(45), "separation_reason": "laid_off", "reported_salary": 78000}},
        {"first_name": "Emily", "last_name": "Chen", "dob": date(1990, 3, 17), "ssn_hash": sha256("ssn_emily_chen_222333444"), "phone": "773-555-0202", "email": "echen.chicago@outlook.com", "bank_account_hash": sha256("bank_emily_chen_unique"), "monthly_income": 5800, "address": {"street": "845 W Diversey Pkwy", "city": "Chicago", "state": "IL", "zip_code": "60614"}, "weekly_benefit": 456.00, "cert_contacts": 3, "employment": {"employer_name": "Global Analytics Partners", "employer_ein_hash": sha256("ein_global_analytics_83-4567890"), "start_date": date(2019, 5, 20), "end_date": date_ago(30), "separation_reason": "laid_off", "reported_salary": 69000}},
        {"first_name": "Frank", "last_name": "Torres", "dob": date(1975, 9, 5), "ssn_hash": sha256("ssn_frank_torres_333444555"), "phone": "773-555-0203", "email": "ftorres1975@comcast.net", "bank_account_hash": sha256("bank_frank_torres_unique"), "monthly_income": 7200, "address": {"street": "3300 S Michigan Ave", "city": "Chicago", "state": "IL", "zip_code": "60616"}, "weekly_benefit": 497.00, "cert_contacts": 3, "employment": {"employer_name": "Apex Manufacturing Group", "employer_ein_hash": sha256("ein_apex_mfg_84-5678901"), "start_date": date(2018, 11, 1), "end_date": date_ago(60), "separation_reason": "laid_off", "reported_salary": 86000}},
        {"first_name": "Grace", "last_name": "Liu", "dob": date(1988, 12, 28), "ssn_hash": sha256("ssn_grace_liu_444555666"), "phone": "773-555-0204", "email": "grace.liu.ui@gmail.com", "bank_account_hash": sha256("bank_grace_liu_unique"), "monthly_income": 5200, "address": {"street": "2100 N Halsted St", "city": "Chicago", "state": "IL", "zip_code": "60614"}, "weekly_benefit": 420.00, "cert_contacts": 3, "employment": {"employer_name": "Pinnacle Consulting Services", "employer_ein_hash": sha256("ein_pinnacle_85-6789012"), "start_date": date(2021, 4, 1), "end_date": date_ago(20), "separation_reason": "laid_off", "reported_salary": 62000}},
    ],
}


# ── Pattern C: Device/IP Cluster (5 people from different states, same device + IP + out-of-state certs) ──

PATTERN_C = {
    "name": "Device Fingerprint Cluster",
    "members": [
        {"first_name": fn, "last_name": ln, "dob": date(1983 + i, (i + 1) * 2, 10 + i), "ssn_hash": sha256(f"ssn_cluster_c_{i}"), "phone": f"555-555-0{300+i}", "email": f"cluster_c_{i}@tempmail.com", "bank_account_hash": sha256(f"bank_cluster_c_{i}_unique"), "monthly_income": 3000 + i * 200, "state": st, "weekly_benefit": 300.00 + i * 15, "device_fingerprint": DEVICE_CLUSTER_FP, "ip_hash": DEVICE_CLUSTER_IP, "employment": {"employer_name": f"Employer {chr(65+i)} Corp", "employer_ein_hash": sha256(f"ein_cluster_c_{i}"), "start_date": date(2020 + i % 3, 3, 1), "end_date": date_ago(15 + i * 5), "separation_reason": "laid_off", "reported_salary": 40000 + i * 3000}}
        for i, (fn, ln, st) in enumerate([("James", "Wright", "TX"), ("Maria", "Gonzalez", "CA"), ("Kevin", "Brown", "NY"), ("Sarah", "Davis", "FL"), ("Michael", "Wilson", "WA")])
    ],
}


# ── Pattern D: Deceased Applicants (2 people) ──

PATTERN_D = {
    "name": "Deceased Applicants",
    "members": [
        {"first_name": "Harold", "last_name": "Graves", "dob": date(1935, 3, 15), "is_deceased": True, "ssn_hash": sha256("ssn_harold_graves_deceased_666777888"), "phone": "555-555-0400", "email": "harold.graves.1935@gmail.com", "bank_account_hash": sha256("bank_harold_graves_suspicious"), "monthly_income": 2800, "device_fingerprint": DEVICE_CLUSTER_FP, "ip_hash": DEVICE_CLUSTER_IP, "address": {"street": "900 Cemetery Rd", "city": "Decatur", "state": "IL", "zip_code": "62521"}, "weekly_benefit": 280.00, "employment": {"employer_name": "RetireRight Consulting", "employer_ein_hash": sha256("ein_retireright_86-7890123"), "start_date": date(2023, 1, 1), "end_date": date_ago(10), "separation_reason": "laid_off", "reported_salary": 33000}},
        {"first_name": "Dorothy", "last_name": "Simmons", "dob": date(1928, 7, 4), "is_deceased": True, "ssn_hash": sha256("ssn_dorothy_simmons_deceased_777888999"), "phone": "555-555-0401", "email": "dorothy.simmons.claims@gmail.com", "bank_account_hash": sha256("bank_dorothy_simmons_suspicious"), "monthly_income": 1900, "device_fingerprint": BOTFARM_DEVICE, "ip_hash": BOTFARM_IP, "address": {"street": "4 Willow Lane", "city": "Peoria", "state": "IL", "zip_code": "61602"}, "weekly_benefit": 215.00, "employment": {"employer_name": "Sunrise Senior Staffing", "employer_ein_hash": sha256("ein_sunrise_87-1234567"), "start_date": date(2022, 6, 1), "end_date": date_ago(5), "separation_reason": "laid_off", "reported_salary": 22000}},
    ],
}


# ── Pattern E: Second Fraud Ring (5 people, shared bank + address + still employed, no device overlap with A) ──

PATTERN_E = {
    "name": "Fraud Ring Beta",
    "members": [
        {"first_name": fn, "last_name": ln, "dob": dob, "ssn_hash": sha256(f"ssn_ring_e_{i}"), "phone": f"630-555-0{500+i}", "email": f"ring_e_{i}@protonmail.com", "bank_account_hash": FRAUD_RING_E_BANK, "monthly_income": 3500 + i * 300, "address": FRAUD_RING_E_ADDR, "weekly_benefit": 310.00 + i * 20, "submitted_offset_seconds": i * 12, "employment": {"employer_name": "Aurora Logistics Group", "employer_ein_hash": sha256("ein_aurora_logistics_88-2345678"), "start_date": date(2021 + i % 2, 4 + i, 1), "end_date": date_ago(-(3 + i)), "separation_reason": "laid_off", "reported_salary": 41000 + i * 4000}}
        for i, (fn, ln, dob) in enumerate([("Nathan", "Brooks", date(1987, 2, 14)), ("Olivia", "Hayes", date(1993, 9, 3)), ("Peter", "Nguyen", date(1981, 5, 27)), ("Quinn", "Patel", date(1996, 11, 8)), ("Rachel", "Scott", date(1984, 7, 19))])
    ],
}


# ── Pattern F: Duplicate SSN / Identity Theft (2 applicants sharing one SSN) ──

PATTERN_F = {
    "name": "Duplicate SSN — Identity Theft",
    "members": [
        {"first_name": "Steven", "last_name": "Carter", "dob": date(1980, 1, 15), "ssn_hash": DUP_SSN_HASH, "phone": "217-555-0601", "email": "steven.carter.official@gmail.com", "bank_account_hash": sha256("bank_steven_carter_real"), "monthly_income": 3400, "address": {"street": "500 Main St", "city": "Champaign", "state": "IL", "zip_code": "61820"}, "weekly_benefit": 330.00, "employment": {"employer_name": "Heartland Freight Co", "employer_ein_hash": sha256("ein_heartland_89-3456789"), "start_date": date(2019, 8, 1), "end_date": date_ago(40), "separation_reason": "laid_off", "reported_salary": 41000}},
        {"first_name": "Stefan", "last_name": "Cartera", "dob": date(1980, 1, 20), "ssn_hash": DUP_SSN_HASH, "phone": "312-555-0602", "email": "s.cartera.claims@tempmail.io", "bank_account_hash": sha256("bank_stefan_cartera_fake"), "monthly_income": 2100, "address": {"street": "1717 W Fullerton Ave", "city": "Chicago", "state": "IL", "zip_code": "60614"}, "weekly_benefit": 290.00, "employment": {"employer_name": "Lakefront Staffing Inc", "employer_ein_hash": sha256("ein_lakefront_90-4567890"), "start_date": date(2020, 3, 15), "end_date": date_ago(25), "separation_reason": "laid_off", "reported_salary": 35000}},
    ],
}


# ── Pattern G: Bot Farm / Bulk Submission (8 people, same IP, all within 90 seconds) ──

PATTERN_G = {
    "name": "Bot Farm Bulk Submission",
    "members": [
        {"first_name": fn, "last_name": ln, "dob": date(1975 + i * 2, (i % 12) + 1, 10 + i), "ssn_hash": sha256(f"ssn_botfarm_g_{i}"), "phone": f"800-555-0{700+i}", "email": f"ui_claim_{i}_2024@disposable.email", "bank_account_hash": sha256(f"bank_botfarm_{i}_g"), "monthly_income": 2800 + i * 100, "state": st, "weekly_benefit": 280.00 + i * 10, "submitted_offset_seconds": i * 11, "device_fingerprint": BOTFARM_DEVICE, "ip_hash": BOTFARM_IP, "employment": {"employer_name": f"QuickHire Temp Agency", "employer_ein_hash": sha256("ein_quickhire_91-5678901"), "start_date": date(2022, i + 1, 1), "end_date": date_ago(10 + i), "separation_reason": "laid_off", "reported_salary": 32000 + i * 1500}}
        for i, (fn, ln, st) in enumerate([("Liam", "Anderson", "IL"), ("Emma", "Thompson", "IL"), ("Noah", "Jackson", "IL"), ("Ava", "White", "IL"), ("Oliver", "Harris", "IL"), ("Sophia", "Martin", "IL"), ("William", "Garcia", "IL"), ("Isabella", "Martinez", "IL")])
    ],
}


# ── Pattern H: Employer Collusion (6 people from same shady staffing company, all claim layoff same week) ──

PATTERN_H = {
    "name": "Employer Collusion — Shady Staffing",
    "members": [
        {"first_name": fn, "last_name": ln, "dob": date(1978 + i, (i * 3 % 12) + 1, 15), "ssn_hash": sha256(f"ssn_collusion_h_{i}"), "phone": f"847-555-0{800+i}", "email": f"h_collusion_{i}@yahoo.com", "bank_account_hash": sha256(f"bank_collusion_h_{i}"), "monthly_income": 3200 + i * 200, "state": "IL", "weekly_benefit": 340.00 + i * 15, "submitted_offset_seconds": i * 8, "cert_contacts": 2, "employment": {"employer_name": "Shady Staffing Solutions LLC", "employer_ein_hash": EMPLOYER_COLLUSION_EIN, "start_date": date(2021, 6, 1), "end_date": date_ago(-(1 + i)), "separation_reason": "laid_off", "reported_salary": 38000 + i * 2000}}
        for i, (fn, ln) in enumerate([("Tyler", "Reed"), ("Ashley", "Cook"), ("Brandon", "Morgan"), ("Jessica", "Bell"), ("Ryan", "Murphy"), ("Lauren", "Rivera")])
    ],
}


# ── Pattern I: Out-of-State Seasonal Workers (5 people, registered IL, certifying from FL/AZ) ──

PATTERN_I = {
    "name": "Out-of-State Seasonal Claimants",
    "members": [
        {"first_name": fn, "last_name": ln, "dob": date(1960 + i * 3, i + 1, 20), "ssn_hash": sha256(f"ssn_outofstate_i_{i}"), "phone": f"312-555-0{900+i}", "email": f"seasonal_{i}@gmail.com", "bank_account_hash": sha256(f"bank_outofstate_{i}"), "monthly_income": 2500 + i * 300, "address": {"street": f"{100+i*10} N Michigan Ave", "city": "Chicago", "state": "IL", "zip_code": "60601"}, "weekly_benefit": 280.00 + i * 12, "out_state": "FL", "employment": {"employer_name": fn + " Seasonal Gig", "employer_ein_hash": sha256(f"ein_seasonal_{i}"), "start_date": date(2020, 5, 1), "end_date": date_ago(20 + i * 5), "separation_reason": "laid_off", "reported_salary": 30000 + i * 2000}}
        for i, (fn, ln) in enumerate([("George", "Fleming"), ("Helen", "Porter"), ("Ivan", "Steele"), ("Julia", "Marsh"), ("Karl", "Flynn")])
    ],
}


# ── Pattern J: Working While Claiming (6 people, certify zero earnings but income + fake uniform contacts) ──

PATTERN_J = {
    "name": "Working While Claiming Benefits",
    "members": [
        {"first_name": fn, "last_name": ln, "dob": date(1985 + i, i + 1, 10), "ssn_hash": sha256(f"ssn_working_j_{i}"), "phone": f"773-555-0{950+i}", "email": f"working_j_{i}@comcast.net", "bank_account_hash": sha256(f"bank_working_j_{i}"), "monthly_income": 5000 + i * 500, "state": "IL", "weekly_benefit": 400.00 + i * 20, "cert_contacts": 3, "employment": {"employer_name": f"Metro Services Group {chr(65+i)}", "employer_ein_hash": sha256(f"ein_metro_{i}"), "start_date": date(2019, i + 1, 1), "end_date": date_ago(14), "separation_reason": "laid_off", "reported_salary": 60000 + i * 5000}}
        for i, (fn, ln) in enumerate([("Marcus", "Webb"), ("Diane", "Holt"), ("Sean", "Frost"), ("Tina", "Barker"), ("Umar", "Sheikh"), ("Vera", "Cole")])
    ],
}
