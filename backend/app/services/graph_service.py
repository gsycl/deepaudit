from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..models import Application, Applicant, ApplicationStatus
from ..models.financial import FinancialRecord
from ..models.metadata import SubmissionMetadata
from ..models.applicant import Address
from ..models.application import ProgramType


def build_graph(db: Session, min_risk: int = 40, program_type: str | None = None) -> dict:
    query = (
        select(Application, Applicant)
        .join(Applicant, Applicant.id == Application.applicant_id)
        .where(Application.risk_score >= min_risk)
    )
    if program_type:
        query = query.where(Application.program_type == program_type)

    rows = db.execute(query).all()

    nodes = []
    app_ids = []
    app_map = {}

    for app, applicant in rows:
        node = {
            "id": str(app.id),
            "label": f"{applicant.first_name[0]}. {applicant.last_name}",
            "full_name": f"{applicant.first_name} {applicant.last_name}",
            "risk_score": app.risk_score or 0,
            "status": app.status,
            "program_type": app.program_type,
            "is_deceased": applicant.is_deceased,
            "ai_recommendation": app.ai_recommendation,
        }
        nodes.append(node)
        app_ids.append(app.id)
        app_map[app.id] = (app, applicant)

    if not app_ids:
        return {"nodes": nodes, "edges": []}

    edges = []
    seen_pairs = set()

    def add_edge(source_id, target_id, relationship, weight=1):
        pair = tuple(sorted([str(source_id), str(target_id)]))
        key = (pair, relationship)
        if key not in seen_pairs:
            seen_pairs.add(key)
            edges.append({
                "source": str(source_id),
                "target": str(target_id),
                "relationship": relationship,
                "weight": weight,
            })

    # Shared bank account edges
    bank_rows = db.execute(
        select(FinancialRecord.bank_account_hash, FinancialRecord.applicant_id)
        .where(FinancialRecord.applicant_id.in_([app.applicant_id for app, _ in rows]))
    ).all()

    bank_to_applicants: dict[str, list] = {}
    for bank_hash, applicant_id in bank_rows:
        bank_to_applicants.setdefault(bank_hash, []).append(applicant_id)

    applicant_to_apps = {}
    for app, applicant in rows:
        applicant_to_apps.setdefault(applicant.id, []).append(app.id)

    for bank_hash, applicant_ids in bank_to_applicants.items():
        if len(applicant_ids) > 1:
            for i in range(len(applicant_ids)):
                for j in range(i + 1, len(applicant_ids)):
                    a_apps = applicant_to_apps.get(applicant_ids[i], [])
                    b_apps = applicant_to_apps.get(applicant_ids[j], [])
                    for a_app_id in a_apps:
                        for b_app_id in b_apps:
                            add_edge(a_app_id, b_app_id, "shared_bank", weight=len(applicant_ids))

    # Shared device fingerprint edges
    meta_rows = db.execute(
        select(SubmissionMetadata.device_fingerprint, SubmissionMetadata.application_id)
        .where(SubmissionMetadata.application_id.in_(app_ids))
    ).all()

    fp_to_apps: dict[str, list] = {}
    for fp, app_id in meta_rows:
        fp_to_apps.setdefault(fp, []).append(app_id)

    for fp, fp_app_ids in fp_to_apps.items():
        if len(fp_app_ids) > 1:
            for i in range(len(fp_app_ids)):
                for j in range(i + 1, len(fp_app_ids)):
                    add_edge(fp_app_ids[i], fp_app_ids[j], "shared_device", weight=len(fp_app_ids))

    # Shared IP edges
    ip_to_apps: dict[str, list] = {}
    for fp_row in meta_rows:
        pass  # already have meta_rows above — query IP hash separately

    ip_rows = db.execute(
        select(SubmissionMetadata.ip_hash, SubmissionMetadata.application_id)
        .where(SubmissionMetadata.application_id.in_(app_ids))
    ).all()

    for ip_hash, app_id in ip_rows:
        ip_to_apps.setdefault(ip_hash, []).append(app_id)

    for ip_hash, ip_app_ids in ip_to_apps.items():
        if len(ip_app_ids) > 3:
            for i in range(len(ip_app_ids)):
                for j in range(i + 1, len(ip_app_ids)):
                    add_edge(ip_app_ids[i], ip_app_ids[j], "shared_ip", weight=len(ip_app_ids))

    # Shared address edges
    addr_rows = db.execute(
        select(Address.zip_code, Address.street, Address.applicant_id)
        .where(Address.applicant_id.in_([app.applicant_id for app, _ in rows]))
        .where(Address.is_primary == True)
    ).all()

    addr_to_applicants: dict[str, list] = {}
    for zip_code, street, applicant_id in addr_rows:
        addr_key = f"{street.lower().strip()}_{zip_code}"
        addr_to_applicants.setdefault(addr_key, []).append(applicant_id)

    for addr_key, addr_applicant_ids in addr_to_applicants.items():
        if len(addr_applicant_ids) > 1:
            for i in range(len(addr_applicant_ids)):
                for j in range(i + 1, len(addr_applicant_ids)):
                    a_apps = applicant_to_apps.get(addr_applicant_ids[i], [])
                    b_apps = applicant_to_apps.get(addr_applicant_ids[j], [])
                    for a_app_id in a_apps:
                        for b_app_id in b_apps:
                            add_edge(a_app_id, b_app_id, "shared_address", weight=len(addr_applicant_ids))

    return {"nodes": nodes, "edges": edges}
