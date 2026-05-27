
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

import airstrip_data as AD
import notifier as N
import sms_parser as P
from eta_calculator import calculate_eta
from models import Case, CaseStatus, CaseStatusHistory, Notification, NotifStatus

logger = logging.getLogger(__name__)

DISPATCH_PHONE = __import__("os").getenv("DISPATCH_PHONE", "+254700000001")
HOSPITAL_PHONE = __import__("os").getenv("HOSPITAL_PHONE", "+254722000010")

# Hardcoded demo next-of-kin (in production: looked up from patient registry)
KIN_PHONE = "+254733000020"


@dataclass
class InboundSMSResult:
    success: bool
    case_id: Optional[str]
    nurse_message: str       # The confirmation SMS text sent back to the nurse
    error: Optional[str] = None


def _generate_case_id(db: Session) -> str:
    """EVAC-YYYY-NNNN — sequential, never reuses."""
    year  = datetime.now(tz=timezone.utc).year
    count = db.query(Case).count() + 1
    return f"EVAC-{year}-{count:04d}"


def _mask_phone(phone: str) -> str:
    """Mask middle digits: +254712345678 → +254XXXXXX678"""
    if len(phone) >= 4:
        return phone[:-3].replace(phone[1:-3], "X" * (len(phone) - 4)) + phone[-3:]
    return phone


def process_inbound_sms(raw_message: str, nurse_phone: str, db: Session) -> InboundSMSResult:
    """
    Full pipeline for one inbound nurse SMS.
    Called from the FastAPI endpoint and the console simulator.
    """
    # 1 ── Parse ──────────────────────────────────────────────────────────────
    parsed = P.parse(raw_message)
    if not parsed.valid:
        logger.warning("Parse failed: %s | msg=%r", parsed.error, raw_message)
        return InboundSMSResult(
            success=False, case_id=None,
            nurse_message=f"[AEROCURE] Invalid message: {parsed.error}\n{P.help_text()}",
            error=parsed.error,
        )

    # 2 ── Validate airstrip ───────────────────────────────────────────────────
    airstrip = AD.get(parsed.airstrip_code)
    if not airstrip:
        codes = ", ".join(sorted(AD.REGISTRY.keys()))
        msg = f"[AEROCURE] Unknown airstrip '{parsed.airstrip_code}'.\nKnown: {codes}"
        return InboundSMSResult(success=False, case_id=None, nurse_message=msg,
                                error=f"Unknown airstrip: {parsed.airstrip_code}")

    # 3 ── Calculate ETA ────────────────────────────────────────────────────────
    eta = calculate_eta(airstrip.lat, airstrip.lng)
    logger.info("ETA %s → %s km, %d min", airstrip.code, eta.distance_km, eta.total_minutes)

    # 4 ── Create case ─────────────────────────────────────────────────────────
    case_id      = _generate_case_id(db)
    masked_phone = _mask_phone(nurse_phone)

    case = Case(
        id             = case_id,
        condition_code = parsed.condition_code,
        condition_name = parsed.condition_name,
        airstrip_code  = airstrip.code,
        airstrip_name  = airstrip.name,
        airstrip_lat   = airstrip.lat,
        airstrip_lng   = airstrip.lng,
        distance_km    = eta.distance_km,
        eta_minutes    = eta.total_minutes,
        nurse_phone    = masked_phone,
        status         = CaseStatus.RECEIVED,
    )
    db.add(case)

    # Initial status history row
    db.add(CaseStatusHistory(
        case_id     = case_id,
        from_status = None,
        to_status   = CaseStatus.RECEIVED.value,
        changed_by  = "SMS",
        notes       = f"Created from SMS: {raw_message}",
    ))
    db.commit()
    db.refresh(case)

    # 5 ── Send notifications and log them ────────────────────────────────────
    notifications = [
        (DISPATCH_PHONE, "DISPATCH",
         N.msg_dispatch(case_id, parsed.condition_name, airstrip.name,
                        eta.distance_km, eta.total_minutes)),
        (airstrip.agent_phone or "+254700000099", "AGENT",
         N.msg_agent(case_id, parsed.condition_name, airstrip.name, eta.total_minutes)),
        (HOSPITAL_PHONE, "HOSPITAL",
         N.msg_hospital(case_id, parsed.condition_name, airstrip.name, eta.total_minutes)),
        (KIN_PHONE, "NEXT_OF_KIN",
         f"[AEROCURE] Your family member is being evacuated by air. "
         f"Case ref: {case_id}. Updates will follow on this number."),
        (nurse_phone, "NURSE",
         N.msg_nurse_confirm(case_id, parsed.condition_name, airstrip.name,
                             eta.distance_km, eta.total_minutes)),
    ]

    nurse_confirm_text = ""
    for phone, role, text in notifications:
        result = N.send_sms(phone, role, text)
        db.add(Notification(
            case_id         = case_id,
            recipient_phone = _mask_phone(phone),
            recipient_role  = role,
            message_text    = text,
            status          = NotifStatus.SENT if result.success else NotifStatus.FAILED,
            at_message_id   = result.at_message_id,
            cost            = result.cost,
        ))
        if role == "NURSE":
            nurse_confirm_text = text

    db.commit()
    logger.info("Case %s created | airstrip=%s | eta=%d min | distance=%.1f km",
                case_id, airstrip.code, eta.total_minutes, eta.distance_km)

    return InboundSMSResult(
        success=True,
        case_id=case_id,
        nurse_message=nurse_confirm_text,
    )


def update_case_status(case_id: str, new_status: str,
                       notes: str, changed_by: str, db: Session) -> Case:
    """Update status with validation and audit trail."""
    VALID_TRANSITIONS = {
        "RECEIVED":   ["DISPATCHED", "CANCELLED"],
        "DISPATCHED": ["AIRBORNE",   "CANCELLED"],
        "AIRBORNE":   ["LANDED",     "CANCELLED"],
        "LANDED":     ["COMPLETED"],
        "COMPLETED":  [],
        "CANCELLED":  [],
    }

    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    current = case.status.value if isinstance(case.status, CaseStatus) else case.status
    allowed = VALID_TRANSITIONS.get(current, [])
    if new_status not in allowed:
        raise ValueError(f"Cannot transition {current} → {new_status}. Allowed: {allowed}")

    old_status = current
    case.status = CaseStatus(new_status)
    if notes:
        case.notes = notes

    db.add(CaseStatusHistory(
        case_id     = case_id,
        from_status = old_status,
        to_status   = new_status,
        changed_by  = changed_by,
        notes       = notes,
    ))
    db.commit()
    db.refresh(case)
    return case
