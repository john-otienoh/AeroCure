import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

IS_DEV = os.getenv("APP_ENV", "development") != "production"

# ── Africa's Talking SDK (production) ────────────────────────────────────────
# Uncomment when going live:
#
# import africastalking
# africastalking.initialize(os.getenv("AT_USERNAME"), os.getenv("AT_API_KEY"))
# _sms = africastalking.SMS
# _SENDER = os.getenv("AT_SENDER_ID", "AEROCURE")
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class SMSResult:
    success: bool
    phone: str
    role: str
    at_message_id: Optional[str] = None
    cost: Optional[str] = None
    error: Optional[str] = None


def _mock_send(phone: str, role: str, message: str) -> SMSResult:
    """Print a realistic AT-style delivery log to console."""
    ts = datetime.now().strftime("%H:%M:%S")
    border = "─" * 60
    print(f"\n{border}")
    print(f"  📱 SMS [{role}] → {phone}")
    print(f"  ⏰ {ts}")
    print(f"  ─────────────────────────────────────────────────────")
    for line in message.split("\n"):
        print(f"  {line}")
    print(f"{border}\n")
    return SMSResult(success=True, phone=phone, role=role,
                     at_message_id=f"mock-{ts.replace(':','')}",
                     cost="KES 0.0000")


def _live_send(phone: str, role: str, message: str) -> SMSResult:
    """Send via Africa's Talking SDK."""
    # Uncomment and remove pass when going live:
    # try:
    #     resp = _sms.send(message, [phone], _SENDER)
    #     data = resp["SMSMessageData"]["Recipients"][0]
    #     return SMSResult(
    #         success=data["status"] == "Success",
    #         phone=phone, role=role,
    #         at_message_id=data.get("messageId"),
    #         cost=data.get("cost"),
    #     )
    # except Exception as exc:
    #     logger.error("AT send failed to %s: %s", phone, exc)
    #     return SMSResult(success=False, phone=phone, role=role, error=str(exc))
    pass


def send_sms(phone: str, role: str, message: str) -> SMSResult:
    """
    Send one SMS.  Routes to mock (dev) or AT SDK (production).
    """
    if IS_DEV:
        return _mock_send(phone, role, message)
    return _live_send(phone, role, message)


# ── Pre-built message templates ───────────────────────────────────────────────

def msg_dispatch(case_id: str, condition: str, airstrip: str,
                 distance_km: float, eta_min: int) -> str:
    return (
        f"[AEROCURE DISPATCH ALERT]\n"
        f"Case: {case_id}\n"
        f"Condition: {condition}\n"
        f"Pickup: {airstrip}\n"
        f"Distance: {distance_km:.0f} km from Wilson\n"
        f"ETA: ~{eta_min} min\n"
        f"Dispatch aircraft IMMEDIATELY."
    )


def msg_agent(case_id: str, condition: str, airstrip: str, eta_min: int) -> str:
    return (
        f"[AEROCURE ALERT] Aircraft inbound to {airstrip}.\n"
        f"Case: {case_id} | Condition: {condition}\n"
        f"ETA: ~{eta_min} min from Wilson Airport.\n"
        f"Prepare airstrip. Clear runway. Await aircraft."
    )


def msg_hospital(case_id: str, condition: str, airstrip: str, eta_min: int) -> str:
    return (
        f"[AEROCURE ALERT] Incoming evacuation patient.\n"
        f"Case: {case_id} | Condition: {condition}\n"
        f"Origin: {airstrip}. ETA to Nairobi: ~{eta_min} min.\n"
        f"Please prepare receiving team."
    )


def msg_nurse_confirm(case_id: str, condition: str, airstrip: str,
                      distance_km: float, eta_min: int) -> str:
    return (
        f"[AEROCURE] Case {case_id} created.\n"
        f"Condition: {condition}\n"
        f"Airstrip: {airstrip}\n"
        f"Distance: {distance_km:.0f} km\n"
        f"Aircraft ETA: ~{eta_min} min\n"
        f"Dispatch, agent, hospital notified.\n"
        f"Track case: dial *384*96# and enter {case_id}"
    )
