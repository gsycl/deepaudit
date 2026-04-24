import json
import logging
from datetime import datetime

import anthropic

from ..config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert fraud analyst assistant for DeepAudit, a government benefits fraud detection system.
You review unemployment benefit applications pre-analyzed by an automated rules engine.

You know these fraud rules:
- RULE_001 (still_employed_check): Applicant claims layoff but employment end date is in the future or missing.
- RULE_002 (income_during_claim): Financial records show income inconsistent with zero-earnings weekly certifications.
- RULE_003 (shared_bank_account): Multiple unrelated applicants share the same bank account — strong fraud ring indicator.
- RULE_004 (shared_device_fingerprint): Multiple applications submitted from the same device — coordination signal.
- RULE_005 (shared_ip_address): High volume of applications from same IP in 30 days — bulk submission / botnet signal.
- RULE_006 (duplicate_ssn): Same Social Security Number appears on multiple applicant records — identity fraud.
- RULE_007 (out_of_state_usage): Weekly certifications submitted from a different state than the registered address.
- RULE_008 (bulk_submission_timing): Application submitted within 60 seconds of 5+ others — automated submission pattern.
- RULE_009 (fake_job_search): Job search contacts reported as exactly the same number every week — fabricated records.
- RULE_010 (deceased_applicant): Applicant is flagged as deceased — posthumous identity fraud.

Your task: Given an application summary and its fraud signals, produce a concise auditor recommendation.

IMPORTANT: Respond ONLY with valid JSON matching exactly this schema. No markdown, no explanation outside JSON:
{
  "recommendation": "approve" | "deny" | "investigate",
  "confidence": "low" | "medium" | "high",
  "headline": "<one sentence summary for the auditor, max 120 chars>",
  "explanation": "<2-4 sentences of plain English reasoning for the auditor>",
  "key_signals": ["<signal_type_1>", "<signal_type_2>"],
  "suggested_action": "<specific next step the auditor should take>"
}

Guidance:
- recommend "deny" when CRITICAL signals are present (deceased, shared bank with 3+, duplicate SSN)
- recommend "investigate" when HIGH signals are present or risk_score 50-79
- recommend "approve" only when risk_score < 30 and no triggered signals
- Be direct and actionable. Auditors are busy professionals."""


def build_user_message(application, signals, applicant) -> str:
    age = (datetime.utcnow().date() - applicant.dob).days // 365

    signal_lines = []
    for s in signals:
        signal_lines.append(f"  - [{s.rule_id}] {s.signal_type} | Severity: {s.severity} | Score: +{s.score_contribution}\n    Description: {s.description}")

    emp_summary = []
    for emp in application.employment_history:
        emp_summary.append(f"    {emp.employer_name}: {emp.separation_reason}, end={emp.end_date}")

    cert_count = len(application.weekly_certifications)
    if cert_count > 0:
        avg_contacts = sum(c.job_search_contacts for c in application.weekly_certifications) / cert_count
        work_weeks = sum(1 for c in application.weekly_certifications if c.did_work)
    else:
        avg_contacts = 0
        work_weeks = 0

    return f"""Application ID: {application.id}
Program: {application.program_type}
Submitted: {application.submitted_at.strftime('%Y-%m-%d %H:%M')}
Status: {application.status}
Risk Score: {application.risk_score}/100
Weekly Benefit Amount: ${application.weekly_benefit_amount or 0:.2f}

Applicant:
  Age: {age} years old
  State: {applicant.addresses[0].state if applicant.addresses else 'Unknown'}
  Is Deceased Flag: {applicant.is_deceased}

Employment History ({len(application.employment_history)} records):
{chr(10).join(emp_summary) if emp_summary else "  None"}

Weekly Certifications: {cert_count} weeks certified
  Weeks reporting work: {work_weeks}
  Avg job search contacts/week: {avg_contacts:.1f}

Triggered Fraud Signals ({len(signals)} total):
{chr(10).join(signal_lines) if signal_lines else "  None"}

Based on this analysis, provide your auditor recommendation."""


async def get_ai_recommendation(application, signals, applicant) -> dict:
    # TODO: Replace mock output with real Claude API call once ANTHROPIC_API_KEY is configured.
    # To enable: set ANTHROPIC_API_KEY in backend/.env and remove the early return below.
    return _mock_recommendation(application, signals)

    # --- Real Claude API call (disabled until API key is set) ---
    # if not settings.ANTHROPIC_API_KEY:
    #     return _mock_recommendation(application, signals)
    # try:
    #     client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    #     user_message = build_user_message(application, signals, applicant)
    #     response = await client.messages.create(
    #         model="claude-sonnet-4-6",
    #         max_tokens=1024,
    #         system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
    #         messages=[{"role": "user", "content": user_message}],
    #     )
    #     raw = response.content[0].text.strip()
    #     if raw.startswith("```"):
    #         raw = raw.split("```")[1]
    #         if raw.startswith("json"):
    #             raw = raw[4:]
    #     return json.loads(raw)
    # except json.JSONDecodeError as e:
    #     logger.error("Claude returned non-JSON: %s", e)
    #     return _mock_recommendation(application, signals)
    # except Exception as e:
    #     logger.error("Claude API error: %s", e)
    #     return _mock_recommendation(application, signals)


def _mock_recommendation(application, signals) -> dict:
    """
    Returns deterministic fake AI output based on the risk score and signals.
    Simulates what Claude would say so the UI is fully functional without an API key.
    """
    risk = application.risk_score or 0
    signal_types = [s.signal_type for s in signals]
    critical_signals = [s for s in signals if s.severity in ("critical",)]
    high_signals = [s for s in signals if s.severity in ("high", "critical")]

    if application.applicant.is_deceased or "deceased_applicant" in signal_types:
        return {
            "recommendation": "deny",
            "confidence": "high",
            "headline": "Application filed under a deceased individual's identity — immediate denial warranted.",
            "explanation": (
                "The applicant is flagged as deceased in the system. This application almost certainly "
                "represents identity theft or posthumous fraud. No legitimate unemployment claim can be "
                "filed on behalf of a deceased person. Immediate denial and referral to law enforcement is recommended."
            ),
            "key_signals": ["deceased_applicant", "shared_device_fingerprint"],
            "suggested_action": "Deny immediately and refer to the Office of Inspector General for identity theft investigation.",
        }

    if "duplicate_ssn" in signal_types or "shared_bank_account" in signal_types:
        return {
            "recommendation": "deny",
            "confidence": "high",
            "headline": "Multiple critical fraud signals detected — coordinated fraud ring likely.",
            "explanation": (
                f"This application carries a risk score of {risk}/100 with {len(critical_signals)} critical "
                f"and {len(high_signals)} high-severity signals. The presence of a shared bank account across "
                "multiple applicants and/or duplicate SSN records strongly indicates a coordinated fraud ring. "
                "These patterns are inconsistent with legitimate unemployment claims."
            ),
            "key_signals": [s for s in signal_types if s in ("shared_bank_account", "duplicate_ssn", "still_employed_check", "bulk_submission_timing")],
            "suggested_action": "Deny and cross-reference all applicants sharing the same bank account or SSN. Escalate to fraud investigations unit.",
        }

    if risk >= 60 or len(high_signals) >= 2:
        return {
            "recommendation": "investigate",
            "confidence": "medium",
            "headline": f"Risk score {risk}/100 with {len(high_signals)} high-severity signals — further review needed.",
            "explanation": (
                f"This application has a risk score of {risk}/100. Triggered signals include: "
                f"{', '.join(signal_types[:3]) or 'none'}. While not conclusive on their own, "
                "the combination of signals warrants manual verification before a decision is made. "
                "Contact the applicant's former employer to verify the separation date and reason."
            ),
            "key_signals": signal_types[:4],
            "suggested_action": "Place under review. Contact employer to verify separation. Request additional documentation from applicant within 10 business days.",
        }

    if risk >= 30:
        return {
            "recommendation": "investigate",
            "confidence": "low",
            "headline": f"Minor anomalies detected (risk score {risk}/100) — low-priority review.",
            "explanation": (
                f"This application has a moderate risk score of {risk}/100 with {len(signals)} minor signal(s). "
                "The anomalies detected are not individually conclusive but are worth a quick spot-check. "
                "Standard verification of employment separation should be sufficient."
            ),
            "key_signals": signal_types[:2],
            "suggested_action": "Perform standard employment verification. Approve if employer confirms separation date.",
        }

    return {
        "recommendation": "approve",
        "confidence": "high",
        "headline": f"No fraud signals detected — application appears legitimate (risk score {risk}/100).",
        "explanation": (
            "The automated rules engine found no fraud signals for this application. "
            "Employment history, certification patterns, and submission metadata are all consistent "
            "with a legitimate unemployment claim. Standard processing is recommended."
        ),
        "key_signals": [],
        "suggested_action": "Approve and process benefit payment on the standard schedule.",
    }


def apply_ai_result_to_application(application, result: dict) -> None:
    application.ai_recommendation = result.get("recommendation")
    application.ai_explanation = result.get("explanation")
    application.ai_headline = result.get("headline")
    application.ai_confidence = result.get("confidence")
    application.ai_key_signals = json.dumps(result.get("key_signals", []))
    application.ai_suggested_action = result.get("suggested_action")
    application.ai_analyzed_at = datetime.utcnow()
