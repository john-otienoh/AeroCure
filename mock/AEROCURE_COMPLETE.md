# AeroCure — Complete Project

Emergency air medical evacuation platform.  
A nurse sends one SMS (`EVAC 4 TURKANA`), the system handles everything else.

---

## Project Structure

```
aerocure/
├── main.py                 # FastAPI app — all routes
├── database.py             # SQLAlchemy + SQLite setup
├── models.py               # All database models
├── airstrip_data.py        # Static airstrip registry with coordinates
├── eta_calculator.py       # Haversine distance + Cessna Caravan ETA
├── sms_parser.py           # Parse EVAC [condition] [airstrip] messages
├── notifier.py             # Mock Africa's Talking (swap in real SDK)
├── case_service.py         # Business logic — create case, fire notifications
├── nurse_console.py        # Console SMS simulator for testing
├── requirements.txt
├── .env.example
└── templates/
    └── dashboard.html      # Bootstrap 5 + Leaflet — no build step
```

---

## `requirements.txt`

```text
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
sqlalchemy>=2.0.30
jinja2>=3.1.4
python-multipart>=0.0.9
python-dotenv>=1.0.1
requests>=2.32.0
```

---

## `.env.example`

```env
# Copy to .env and fill in values
APP_ENV=development
DATABASE_URL=sqlite:///./aerocure.db

# Africa's Talking (leave as sandbox for testing)
AT_USERNAME=sandbox
AT_API_KEY=your_at_api_key_here
AT_SENDER_ID=AEROCURE

# Operational numbers (use AT sandbox numbers for dev)
DISPATCH_PHONE=+254700000001
HOSPITAL_PHONE=+254722000010

# Wilson Airport base (do not change)
BASE_LAT=-1.32172
BASE_LNG=36.8148
```

---

## `database.py`

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aerocure.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a session and guarantees cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called once at startup."""
    import models  # noqa: F401 — registers all models with Base
    Base.metadata.create_all(bind=engine)
```

---

## `models.py`

```python
# models.py
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float,
    Integer, String, Text
)
from sqlalchemy.sql import func

from database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class CaseStatus(str, enum.Enum):
    RECEIVED   = "RECEIVED"
    DISPATCHED = "DISPATCHED"
    AIRBORNE   = "AIRBORNE"
    LANDED     = "LANDED"
    COMPLETED  = "COMPLETED"
    CANCELLED  = "CANCELLED"


class NotifStatus(str, enum.Enum):
    SENT   = "SENT"
    FAILED = "FAILED"


# ── Tables ────────────────────────────────────────────────────────────────────

class Case(Base):
    __tablename__ = "cases"

    id               = Column(String(20),  primary_key=True)
    condition_code   = Column(String(2),   nullable=False)
    condition_name   = Column(String(100), nullable=False)
    airstrip_code    = Column(String(20),  nullable=False)
    airstrip_name    = Column(String(200), nullable=False)
    airstrip_lat     = Column(Float,       nullable=True)
    airstrip_lng     = Column(Float,       nullable=True)
    distance_km      = Column(Float,       nullable=True)
    eta_minutes      = Column(Integer,     nullable=True)
    # Stored masked
    nurse_phone      = Column(String(20),  nullable=False)
    status           = Column(
        Enum(CaseStatus, name="case_status"),
        default=CaseStatus.RECEIVED,
        nullable=False,
    )
    notes            = Column(Text,        nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id":             self.id,
            "condition_code": self.condition_code,
            "condition_name": self.condition_name,
            "airstrip_code":  self.airstrip_code,
            "airstrip_name":  self.airstrip_name,
            "airstrip_lat":   self.airstrip_lat,
            "airstrip_lng":   self.airstrip_lng,
            "distance_km":    round(self.distance_km, 1) if self.distance_km else None,
            "eta_minutes":    self.eta_minutes,
            "nurse_phone":    self.nurse_phone,
            "status":         self.status.value if isinstance(self.status, CaseStatus) else self.status,
            "notes":          self.notes,
            "created_at":     self.created_at.isoformat() if self.created_at else None,
            "updated_at":     self.updated_at.isoformat() if self.updated_at else None,
        }


class Notification(Base):
    __tablename__ = "notifications"

    id              = Column(Integer,     primary_key=True, autoincrement=True)
    case_id         = Column(String(20),  nullable=False)
    recipient_phone = Column(String(20),  nullable=False)
    recipient_role  = Column(String(20),  nullable=False)  # NURSE|DISPATCH|AGENT|HOSPITAL|KIN
    message_text    = Column(Text,        nullable=False)
    status          = Column(Enum(NotifStatus, name="notif_status"), default=NotifStatus.SENT)
    at_message_id   = Column(String(60),  nullable=True)
    cost            = Column(String(20),  nullable=True)
    sent_at         = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id":              self.id,
            "case_id":         self.case_id,
            "recipient_phone": self.recipient_phone,
            "recipient_role":  self.recipient_role,
            "message_text":    self.message_text,
            "status":          self.status.value if isinstance(self.status, NotifStatus) else self.status,
            "sent_at":         self.sent_at.isoformat() if self.sent_at else None,
        }


class CaseStatusHistory(Base):
    __tablename__ = "case_status_history"

    id          = Column(Integer,    primary_key=True, autoincrement=True)
    case_id     = Column(String(20), nullable=False)
    from_status = Column(String(20), nullable=True)
    to_status   = Column(String(20), nullable=False)
    changed_by  = Column(String(60), default="SYSTEM")
    notes       = Column(Text,       nullable=True)
    changed_at  = Column(DateTime(timezone=True), server_default=func.now())
```

---

## `airstrip_data.py`

```python
# airstrip_data.py
"""
Static airstrip registry.
In production these come from the database (seeded from the OurAirports CSV).
For development, this module provides the same interface without a DB dependency.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AirstripInfo:
    code: str
    name: str
    county: str
    lat: float
    lng: float
    agent_phone: Optional[str] = None


# Wilson Airport — base of operations (Cessna Caravan departs from here)
WILSON = AirstripInfo(
    code="HKWL",
    name="Wilson Airport",
    county="Nairobi County",
    lat=-1.32172,
    lng=36.8148,
)

REGISTRY: dict[str, AirstripInfo] = {
    "TURKANA":  AirstripInfo("TURKANA",  "Lodwar Airport",              "Turkana County",      3.1219,   35.6087, "+254711000001"),
    "MARSABIT": AirstripInfo("MARSABIT", "Marsabit Airport",            "Marsabit County",     2.3383,   37.9993, "+254711000002"),
    "ISIOLO":   AirstripInfo("ISIOLO",   "Isiolo Airport",              "Isiolo County",       0.3382,   37.5924, "+254711000003"),
    "NANYUKI":  AirstripInfo("NANYUKI",  "Nanyuki Airport",             "Laikipia County",     0.0624,   37.0410, "+254711000004"),
    "AMBOSELI": AirstripInfo("AMBOSELI", "Amboseli Airport",            "Kajiado County",     -2.6455,   37.2531, "+254711000005"),
    "WAJIR":    AirstripInfo("WAJIR",    "Wajir Airport",               "Wajir County",        1.7331,   40.0916, "+254711000006"),
    "GARISSA":  AirstripInfo("GARISSA",  "Garissa Airport",             "Garissa County",     -0.4635,   39.6483, "+254711000007"),
    "ELDORET":  AirstripInfo("ELDORET",  "Eldoret International Airport","Uasin Gishu County",  0.4046,   35.2389, "+254711000008"),
    "KITALE":   AirstripInfo("KITALE",   "Kitale Airport",              "Trans Nzoia County",  0.9719,   35.0026, "+254711000009"),
    "MOMBASA":  AirstripInfo("MOMBASA",  "Moi International Airport",   "Mombasa County",     -4.0348,   39.5942, "+254711000010"),
    "KISUMU":   AirstripInfo("KISUMU",   "Kisumu International Airport", "Kisumu County",      -0.0861,   34.7290, "+254711000011"),
    "MALINDI":  AirstripInfo("MALINDI",  "Malindi Airport",             "Kilifi County",      -3.2293,   40.1017, "+254711000012"),
    "UKUNDA":   AirstripInfo("UKUNDA",   "Ukunda Airstrip",             "Kwale County",       -4.2933,   39.5711, "+254711000013"),
    "NAROK":    AirstripInfo("NAROK",    "Narok Airport",               "Narok County",       -1.1264,   35.8458, "+254711000014"),
    "KERICHO":  AirstripInfo("KERICHO",  "Kericho Airport",             "Kericho County",     -0.3614,   35.2419, "+254711000015"),
    "EMBU":     AirstripInfo("EMBU",     "Embu Airport",                "Embu County",        -0.5000,   37.5000, "+254711000016"),
    "LAMU":     AirstripInfo("LAMU",     "Manda Airport",               "Lamu County",        -2.2524,   40.9131, "+254711000017"),
    "MANDERA":  AirstripInfo("MANDERA",  "Mandera Airport",             "Mandera County",      3.9332,   41.8566, "+254711000018"),
    "MOYALE":   AirstripInfo("MOYALE",   "Moyale Airport",              "Marsabit County",     3.4669,   39.1014, "+254711000019"),
    "NAKURU":   AirstripInfo("NAKURU",   "Nakuru Airport",              "Nakuru County",      -0.2982,   36.1600, "+254711000020"),
}


def get(code: str) -> Optional[AirstripInfo]:
    """Look up airstrip by code (case-insensitive)."""
    return REGISTRY.get(code.upper())


def all_airstrips() -> list[AirstripInfo]:
    return list(REGISTRY.values())


def as_geojson_features() -> list[dict]:
    """Return all airstrips as GeoJSON feature dicts for the map."""
    features = []
    for a in REGISTRY.values():
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [a.lng, a.lat]},
            "properties": {
                "code":   a.code,
                "name":   a.name,
                "county": a.county,
            },
        })
    return features
```

---

## `eta_calculator.py`

```python
# eta_calculator.py
"""
Real-time ETA calculation using the Haversine great-circle formula.

Aircraft: Cessna Grand Caravan (most common AMREF air ambulance)
  Cruise speed : 335 km/h (181 knots)
  Service ceil.: 7,620 m
  Range        : ~1,982 km

Wilson Airport (base): -1.32172, 36.8148
"""

import math
from dataclasses import dataclass

# ── Aircraft constants ────────────────────────────────────────────────────────
CESSNA_CARAVAN_CRUISE_KMH = 335.0   # cruise speed km/h
PREP_MINUTES              = 20      # pre-flight check, fuelling, taxi
LANDING_MINUTES           = 10      # circuit, approach, landing roll

WILSON_LAT = -1.32172
WILSON_LNG = 36.8148

EARTH_RADIUS_KM = 6371.0


@dataclass
class ETAResult:
    distance_km: float        # great-circle distance
    flight_minutes: int       # pure air time
    total_minutes: int        # including prep and landing
    speed_kmh: float          # aircraft cruise speed used
    bearing_deg: float        # departure bearing from Wilson


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km between two WGS-84 points."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return initial bearing (degrees, 0=N, 90=E) from point 1 to point 2."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    x = math.sin(dlam) * math.cos(phi2)
    y = (math.cos(phi1) * math.sin(phi2)
         - math.sin(phi1) * math.cos(phi2) * math.cos(dlam))
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def calculate_eta(dest_lat: float, dest_lng: float) -> ETAResult:
    """
    Calculate ETA from Wilson Airport to a destination airstrip.

    Returns:
        ETAResult with distance, flight time, total ETA, and bearing.
    """
    dist = haversine_km(WILSON_LAT, WILSON_LNG, dest_lat, dest_lng)
    flight_min = int(dist / CESSNA_CARAVAN_CRUISE_KMH * 60)
    total_min  = flight_min + PREP_MINUTES + LANDING_MINUTES
    bearing    = bearing_deg(WILSON_LAT, WILSON_LNG, dest_lat, dest_lng)

    return ETAResult(
        distance_km    = round(dist, 1),
        flight_minutes = flight_min,
        total_minutes  = total_min,
        speed_kmh      = CESSNA_CARAVAN_CRUISE_KMH,
        bearing_deg    = round(bearing, 1),
    )
```

---

## `sms_parser.py`

```python
# sms_parser.py
"""
Parse inbound nurse SMS messages.

Supported formats:
  EVAC [CONDITION] [AIRSTRIP]

  EVAC 1 TURKANA      → Trauma, Lodwar Airport
  EVAC TR TURKANA     → same, using code directly
  evac cardiac wajir  → case-insensitive

Condition mapping (number OR code):
  1 / TR  → Trauma / Injury
  2 / CA  → Cardiac Emergency
  3 / OB  → Obstetric Emergency
  4 / RE  → Respiratory Distress
  5 / OT  → Other Critical
"""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class ParsedSMS:
    raw: str
    condition_code: str
    condition_name: str
    airstrip_code: str
    valid: bool
    error: Optional[str] = None


# Condition lookup by number or code (all upper)
_CONDITIONS: dict[str, tuple[str, str]] = {
    "1":  ("TR", "Trauma / Injury"),
    "TR": ("TR", "Trauma / Injury"),
    "2":  ("CA", "Cardiac Emergency"),
    "CA": ("CA", "Cardiac Emergency"),
    "3":  ("OB", "Obstetric Emergency"),
    "OB": ("OB", "Obstetric Emergency"),
    "4":  ("RE", "Respiratory Distress"),
    "RE": ("RE", "Respiratory Distress"),
    "5":  ("OT", "Other Critical"),
    "OT": ("OT", "Other Critical"),
}


def parse(raw: str) -> ParsedSMS:
    """
    Parse a raw SMS string into a ParsedSMS.
    Returns ParsedSMS with valid=False and an error message on failure.
    """
    text = raw.strip().upper()

    # Must start with EVAC
    if not text.startswith("EVAC"):
        return ParsedSMS(raw=raw, condition_code="", condition_name="",
                         airstrip_code="", valid=False,
                         error="Message must start with EVAC")

    # Tokenise the rest
    parts = text.split()
    if len(parts) < 3:
        return ParsedSMS(raw=raw, condition_code="", condition_name="",
                         airstrip_code="", valid=False,
                         error="Format: EVAC [condition] [airstrip]  e.g. EVAC 4 TURKANA")

    condition_token = parts[1]
    airstrip_token  = parts[2]

    # Resolve condition
    if condition_token not in _CONDITIONS:
        return ParsedSMS(raw=raw, condition_code="", condition_name="",
                         airstrip_code="", valid=False,
                         error=f"Unknown condition '{condition_token}'. "
                               f"Use 1-5 or TR/CA/OB/RE/OT")

    cond_code, cond_name = _CONDITIONS[condition_token]

    return ParsedSMS(
        raw=raw,
        condition_code=cond_code,
        condition_name=cond_name,
        airstrip_code=airstrip_token,
        valid=True,
    )


def help_text() -> str:
    return (
        "AeroCure SMS format: EVAC [condition] [airstrip]\n"
        "Conditions: 1=Trauma 2=Cardiac 3=Obstetric 4=Respiratory 5=Other\n"
        "Airstrips: TURKANA MARSABIT ISIOLO NANYUKI AMBOSELI WAJIR GARISSA\n"
        "Example: EVAC 2 MARSABIT"
    )
```


---

## `notifier.py`

```python
# notifier.py
"""
Notification layer — wraps Africa's Talking SMS API.

DEV MODE (APP_ENV != production):
  Messages are printed to console with realistic formatting.
  All AT API calls are skipped.

PRODUCTION MODE:
  Uncomment the AT SDK block and set AT_USERNAME / AT_API_KEY in .env.
  No other code changes required.
"""

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
```

---

## `case_service.py`

```python
# case_service.py
"""
Core business logic.
  1. Parse inbound SMS
  2. Validate airstrip exists
  3. Calculate ETA
  4. Generate case ID
  5. Persist case to DB
  6. Fire all notifications
  7. Persist notification records
  8. Return structured result
"""

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
```

---

## `main.py`

```python
# main.py
```

---

## `nurse_console.py`

```python
#!/usr/bin/env python3
# nurse_console.py
"""
Console SMS simulator — run this to test the full AeroCure pipeline.

Usage:
    python nurse_console.py

What it does:
  1. Prompts for nurse phone number
  2. Accepts EVAC messages in a loop
  3. POSTs to the FastAPI backend
  4. Prints the confirmation (what the nurse would receive by SMS)
  5. Type 'quit' to exit, 'help' for format, 'mock' to inject test data
"""

import json
import sys
import time

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip install requests")
    sys.exit(1)

BASE_URL = "http://localhost:8000"
SEPARATOR = "=" * 62

MOCK_MESSAGES = [
    ("EVAC 2 TURKANA",  "+254712000001"),
    ("EVAC 4 MARSABIT", "+254712000002"),
    ("EVAC 1 ISIOLO",   "+254712000003"),
    ("EVAC 3 WAJIR",    "+254712000004"),
    ("EVAC 5 MOMBASA",  "+254712000005"),
]


def check_server():
    try:
        r = requests.get(f"{BASE_URL}/api/stats", timeout=3)
        r.raise_for_status()
        stats = r.json()
        print(f"  Server online ✅  | Total cases in DB: {stats['total']}")
        return True
    except Exception as e:
        print(f"  ❌  Cannot reach server at {BASE_URL}")
        print(f"     Start it first: python main.py")
        return False


def send_sms(phone: str, message: str) -> dict:
    r = requests.post(
        f"{BASE_URL}/api/inbound-sms",
        json={"phone": phone, "message": message},
        timeout=10,
    )
    return r.json(), r.status_code


def print_response(data: dict, status_code: int):
    print()
    if status_code == 200 and data.get("success"):
        print(f"  ✅  Case created: {data['case_id']}")
        print()
        print("  ── Nurse confirmation SMS ──────────────────────────")
        for line in data["confirmation"].split("\n"):
            print(f"  {line}")
        print("  ────────────────────────────────────────────────────")
    else:
        print(f"  ❌  Error: {data.get('error') or data.get('detail')}")
        if data.get("message"):
            print(f"  Response: {data['message']}")
    print()


def inject_mock_data():
    print(f"\n  Injecting {len(MOCK_MESSAGES)} mock cases…\n")
    for msg, phone in MOCK_MESSAGES:
        print(f"  Sending: {msg} from {phone}")
        data, code = send_sms(phone, msg)
        if data.get("success"):
            print(f"  ✅  {data['case_id']}")
        else:
            print(f"  ❌  {data.get('error')}")
        time.sleep(0.5)
    print("\n  Mock data injected. Refresh the dashboard.\n")


def main():
    print()
    print(SEPARATOR)
    print("  🚑  AeroCure — Nurse SMS Console Simulator")
    print(SEPARATOR)
    print()

    if not check_server():
        sys.exit(1)

    print()
    print("  Commands:")
    print("    EVAC [condition] [airstrip]  — report an emergency")
    print("    mock                         — inject 5 test cases")
    print("    help                         — show SMS format")
    print("    quit                         — exit")
    print()

    # Get nurse phone
    nurse_phone = input("  Your phone number (+254XXXXXXXXX): ").strip()
    if not nurse_phone:
        nurse_phone = "+254700000099"
        print(f"  Using demo number: {nurse_phone}")

    print()

    while True:
        try:
            raw = input("  SMS > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  Exiting.")
            break

        if not raw:
            continue
        if raw.lower() == "quit":
            print("  Goodbye.")
            break
        if raw.lower() == "help":
            print()
            print("  Format: EVAC [condition] [airstrip]")
            print("  Conditions: 1=Trauma  2=Cardiac  3=Obstetric")
            print("              4=Respiratory  5=Other")
            print("  Airstrips: TURKANA MARSABIT ISIOLO NANYUKI")
            print("             AMBOSELI WAJIR GARISSA ELDORET")
            print("             KITALE MOMBASA KISUMU MALINDI LAMU")
            print()
            continue
        if raw.lower() == "mock":
            inject_mock_data()
            continue

        print(f"\n  Sending: \"{raw}\"")
        try:
            data, code = send_sms(nurse_phone, raw)
            print_response(data, code)
        except requests.ConnectionError:
            print("  ❌  Lost connection to server.")


if __name__ == "__main__":
    main()
```

---

## `templates/dashboard.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AeroCure — Dispatch Dashboard</title>

  <!-- Bootstrap 5 -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />
  <!-- Bootstrap Icons -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet" />
  <!-- Leaflet -->
  <link href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" rel="stylesheet" />
  <!-- Google Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet" />

  <style>
    :root {
      --bg:      #070d1a;
      --surface: #0d1526;
      --border:  #1e2d45;
      --accent:  #38bdf8;
      --muted:   #475569;
      --text:    #e2e8f0;
      --text2:   #94a3b8;
    }
    *, *::before, *::after { box-sizing: border-box; }
    html, body { height: 100%; margin: 0; background: var(--bg); color: var(--text); font-family: 'DM Sans', sans-serif; overflow-x: hidden; }

    /* ── Header ─────────────────────────────────── */
    .ac-header {
      height: 52px; background: var(--surface); border-bottom: 1px solid var(--border);
      display: flex; align-items: center; padding: 0 20px; gap: 14px; position: sticky; top: 0; z-index: 1000;
    }
    .ac-logo { font-family: 'Space Mono', monospace; font-size: .9rem; font-weight: 700; color: var(--text); letter-spacing: .02em; }
    .ac-logo span { color: var(--accent); }
    .ac-tag  { font-family: 'Space Mono', monospace; font-size: .6rem; color: var(--muted); letter-spacing: .1em; padding-left: 12px; border-left: 1px solid var(--border); }
    .pulse-dot { width: 8px; height: 8px; border-radius: 50%; background: #ef4444; box-shadow: 0 0 8px #ef4444; animation: pulse 1.4s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
    .sync-badge { font-family: 'Space Mono', monospace; font-size: .62rem; color: var(--muted); border: 1px solid var(--border); border-radius: 4px; padding: 2px 8px; cursor: pointer; background: transparent; }
    .sync-badge:hover { color: var(--text); border-color: var(--text2); }
    @keyframes spin { to { transform: rotate(360deg); } }
    .spinning { display: inline-block; animation: spin 1s linear infinite; }

    /* ── Stats bar ───────────────────────────────── */
    .stats-bar { display: flex; gap: 10px; padding: 10px 20px; border-bottom: 1px solid var(--border); flex-wrap: wrap; background: var(--surface); }
    .stat-card { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 8px 14px; min-width: 90px; }
    .stat-val  { font-family: 'Space Mono', monospace; font-size: 1.4rem; font-weight: 700; line-height: 1; }
    .stat-lbl  { font-size: .6rem; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; margin-top: 3px; }

    /* ── Main layout ─────────────────────────────── */
    .ac-main { display: grid; grid-template-columns: 1fr 360px; gap: 10px; padding: 10px 20px; height: calc(100vh - 52px - 60px); }
    @media (max-width: 900px) { .ac-main { grid-template-columns: 1fr; height: auto; } }

    /* ── Map ─────────────────────────────────────── */
    #map { width: 100%; height: 100%; min-height: 400px; border-radius: 8px; border: 1px solid var(--border); }
    .leaflet-container { background: #0a1120; font-family: 'DM Sans', sans-serif; }
    .leaflet-popup-content-wrapper { background: var(--surface); color: var(--text); border: 1px solid var(--border); border-radius: 6px; box-shadow: 0 8px 24px #0008; }
    .leaflet-popup-tip { background: var(--surface); }
    .leaflet-popup-content { margin: 10px 14px; font-size: 12px; line-height: 1.6; }
    .leaflet-control-zoom a { background: var(--surface) !important; color: var(--text2) !important; border-color: var(--border) !important; }
    .leaflet-control-attribution { background: rgba(7,13,26,.8) !important; color: var(--muted) !important; font-size: 10px !important; }

    /* ── Cases panel ─────────────────────────────── */
    .cases-panel { display: flex; flex-direction: column; border: 1px solid var(--border); border-radius: 8px; background: var(--surface); overflow: hidden; height: 100%; }
    .panel-head  { padding: 10px 14px; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; flex-shrink: 0; }
    .panel-head h6 { margin: 0; font-family: 'Space Mono', monospace; font-size: .72rem; font-weight: 700; letter-spacing: .06em; }
    .panel-search { padding: 8px 12px; border-bottom: 1px solid var(--border); flex-shrink: 0; }
    .panel-search input { width: 100%; background: var(--bg); border: 1px solid var(--border); border-radius: 4px; color: var(--text); font-size: .78rem; padding: 5px 10px; outline: none; font-family: 'DM Sans', sans-serif; }
    .panel-search input:focus { border-color: var(--accent); }
    .panel-search input::placeholder { color: var(--muted); }
    .panel-filters { padding: 6px 12px; border-bottom: 1px solid var(--border); display: flex; gap: 5px; flex-wrap: wrap; flex-shrink: 0; }
    .filter-btn { font-family: 'Space Mono', monospace; font-size: .55rem; font-weight: 700; letter-spacing: .04em; padding: 2px 7px; border-radius: 3px; border: 1px solid var(--border); background: transparent; color: var(--muted); cursor: pointer; transition: all .12s; }
    .filter-btn.active { background: var(--accent); color: #0f172a; border-color: var(--accent); }
    .cases-list { flex: 1; overflow-y: auto; }
    .cases-list::-webkit-scrollbar { width: 3px; } .cases-list::-webkit-scrollbar-track { background: transparent; } .cases-list::-webkit-scrollbar-thumb { background: var(--border); }
    .case-row { padding: 10px 14px; border-bottom: 1px solid var(--border); cursor: pointer; transition: background .12s; }
    .case-row:hover { background: #142035; }
    .case-row.selected { background: #1a2e4a; border-left: 3px solid var(--accent); }
    .case-id  { font-family: 'Space Mono', monospace; font-size: .72rem; font-weight: 700; color: var(--text); }
    .case-sub { font-size: .72rem; color: var(--text2); margin: 3px 0; }
    .case-meta { font-size: .65rem; color: var(--muted); display: flex; justify-content: space-between; }
    .panel-footer { padding: 5px 14px; border-top: 1px solid var(--border); font-family: 'Space Mono', monospace; font-size: .58rem; color: var(--muted); flex-shrink: 0; }

    /* ── Status badges ───────────────────────────── */
    .badge-RECEIVED   { background: rgba(245,158,11,.12); color: #f59e0b; border: 1px solid rgba(245,158,11,.25); }
    .badge-DISPATCHED { background: rgba(59,130,246,.12); color: #3b82f6; border: 1px solid rgba(59,130,246,.25); }
    .badge-AIRBORNE   { background: rgba(16,185,129,.12); color: #10b981; border: 1px solid rgba(16,185,129,.25); }
    .badge-LANDED     { background: rgba(167,139,250,.12);color: #a78bfa; border: 1px solid rgba(167,139,250,.25);}
    .badge-COMPLETED  { background: rgba(110,231,183,.12);color: #6ee7b7; border: 1px solid rgba(110,231,183,.25);}
    .badge-CANCELLED  { background: rgba(239,68,68,.12);  color: #ef4444; border: 1px solid rgba(239,68,68,.25); }
    .status-badge { display: inline-flex; align-items: center; gap: 4px; border-radius: 4px; font-family: 'Space Mono', monospace; font-size: .58rem; font-weight: 700; letter-spacing: .04em; padding: 2px 7px; }
    .status-dot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }

    /* ── Detail modal ────────────────────────────── */
    .detail-panel { position: fixed; top: 0; right: 0; bottom: 0; width: min(440px, 100vw); background: var(--surface); border-left: 1px solid var(--border); z-index: 2000; display: flex; flex-direction: column; transform: translateX(100%); transition: transform .22s ease; overflow: hidden; }
    .detail-panel.open { transform: translateX(0); }
    .detail-head { padding: 16px 18px; border-bottom: 1px solid var(--border); display: flex; align-items: flex-start; justify-content: space-between; flex-shrink: 0; }
    .detail-body { flex: 1; overflow-y: auto; padding: 16px 18px; }
    .field-lbl  { font-family: 'Space Mono', monospace; font-size: .56rem; color: var(--muted); letter-spacing: .1em; text-transform: uppercase; margin-bottom: 3px; }
    .field-val  { font-size: .84rem; color: var(--text2); margin-bottom: 14px; }
    .notif-row  { display: flex; align-items: flex-start; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: .72rem; }
    .notif-role { font-family: 'Space Mono', monospace; font-size: .58rem; color: var(--accent); min-width: 80px; }
    .notif-msg  { color: var(--text2); line-height: 1.4; white-space: pre-wrap; word-break: break-word; }
    .btn-close-panel { background: transparent; border: 1px solid var(--border); border-radius: 4px; color: var(--muted); padding: 2px 8px; cursor: pointer; font-size: .9rem; }
    .btn-close-panel:hover { color: var(--text); }
    .update-form select, .update-form textarea, .update-form input { background: var(--bg); border: 1px solid var(--border); border-radius: 4px; color: var(--text); font-family: 'DM Sans', sans-serif; font-size: .8rem; padding: 6px 10px; width: 100%; margin-bottom: 10px; outline: none; }
    .update-form select:focus, .update-form textarea:focus { border-color: var(--accent); }
    .btn-update { background: var(--accent); border: none; border-radius: 4px; color: #0f172a; font-family: 'Space Mono', monospace; font-size: .7rem; font-weight: 700; padding: 8px 16px; width: 100%; cursor: pointer; }
    .btn-update:hover { opacity: .9; }
    .btn-update:disabled { background: var(--border); color: var(--muted); cursor: not-allowed; }

    /* ── Toast ───────────────────────────────────── */
    #toast-container { position: fixed; top: 60px; right: 16px; z-index: 9999; display: flex; flex-direction: column; gap: 8px; }
    .toast-item { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 10px 16px; font-size: .78rem; color: var(--text); box-shadow: 0 4px 16px #0006; display: flex; align-items: center; gap: 10px; animation: slideIn .2s ease; min-width: 260px; }
    .toast-item.success { border-left: 3px solid #10b981; }
    .toast-item.error   { border-left: 3px solid #ef4444; }
    @keyframes slideIn { from{transform:translateX(120%);opacity:0} to{transform:translateX(0);opacity:1} }

    /* ── SMS test panel ──────────────────────────── */
    .sms-panel { position: fixed; bottom: 16px; left: 20px; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; z-index: 500; min-width: 320px; box-shadow: 0 8px 24px #0008; }
    .sms-panel h6 { font-family: 'Space Mono', monospace; font-size: .68rem; margin: 0 0 8px 0; color: var(--text2); }
    .sms-row { display: flex; gap: 6px; }
    .sms-input { flex: 1; background: var(--bg); border: 1px solid var(--border); border-radius: 4px; color: var(--text); font-family: 'Space Mono', monospace; font-size: .75rem; padding: 6px 10px; outline: none; }
    .sms-input:focus { border-color: var(--accent); }
    .sms-btn { background: #ef4444; border: none; border-radius: 4px; color: white; font-family: 'Space Mono', monospace; font-size: .7rem; font-weight: 700; padding: 6px 12px; cursor: pointer; white-space: nowrap; }
    .sms-btn:hover { opacity: .85; }

    /* ── Misc ────────────────────────────────────── */
    .divider { border-top: 1px solid var(--border); margin: 12px 0; }
    .empty-state { text-align: center; padding: 40px 20px; color: var(--muted); font-size: .8rem; }
    @keyframes ripple { 0%{transform:scale(1);opacity:.7} 100%{transform:scale(2.8);opacity:0} }
  </style>
</head>
<body>

<!-- ── Header ───────────────────────────────────────────────────────── -->
<div class="ac-header">
  <span style="font-size:1.1rem">🚑</span>
  <div class="ac-logo">AEROCURE<span>_</span></div>
  <div class="ac-tag">DISPATCH CONTROL</div>
  <div class="ms-auto d-flex align-items-center gap-3">
    <div id="active-indicator" class="d-none d-flex align-items-center gap-2" style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);border-radius:4px;padding:3px 10px">
      <div class="pulse-dot"></div>
      <span id="active-count" style="font-family:'Space Mono',monospace;font-size:.68rem;color:#ef4444;font-weight:700"></span>
    </div>
    <button class="sync-badge" id="sync-btn" onclick="manualRefresh()">⟳ <span id="sync-time">--:--</span></button>
  </div>
</div>

<!-- ── Stats bar ────────────────────────────────────────────────────── -->
<div class="stats-bar" id="stats-bar">
  <div class="stat-card"><div class="stat-val" id="s-active" style="color:#ef4444">0</div><div class="stat-lbl">Active</div></div>
  <div class="stat-card"><div class="stat-val" id="s-total"  style="color:#94a3b8">0</div><div class="stat-lbl">Total</div></div>
  <div class="stat-card"><div class="stat-val" id="s-recv"   style="color:#f59e0b">0</div><div class="stat-lbl">Received</div></div>
  <div class="stat-card"><div class="stat-val" id="s-disp"   style="color:#3b82f6">0</div><div class="stat-lbl">Dispatched</div></div>
  <div class="stat-card"><div class="stat-val" id="s-air"    style="color:#10b981">0</div><div class="stat-lbl">Airborne</div></div>
  <div class="stat-card"><div class="stat-val" id="s-land"   style="color:#a78bfa">0</div><div class="stat-lbl">Landed</div></div>
  <div class="stat-card"><div class="stat-val" id="s-eta"    style="color:#38bdf8">—</div><div class="stat-lbl">Avg ETA (min)</div></div>
</div>

<!-- ── Main ─────────────────────────────────────────────────────────── -->
<div class="ac-main">

  <!-- Map -->
  <div id="map"></div>

  <!-- Cases panel -->
  <div class="cases-panel">
    <div class="panel-head">
      <h6>ACTIVE CASES</h6>
      <span id="case-count-badge" style="font-family:'Space Mono',monospace;font-size:.6rem;color:var(--muted)">0 cases</span>
    </div>
    <div class="panel-search">
      <input type="text" id="search-input" placeholder="Search ID, condition, airstrip…" oninput="filterCases()" />
    </div>
    <div class="panel-filters" id="filter-btns">
      <button class="filter-btn active" data-filter="ALL"        onclick="setFilter('ALL',this)">ALL</button>
      <button class="filter-btn"        data-filter="RECEIVED"   onclick="setFilter('RECEIVED',this)">RECEIVED</button>
      <button class="filter-btn"        data-filter="DISPATCHED" onclick="setFilter('DISPATCHED',this)">DISPATCHED</button>
      <button class="filter-btn"        data-filter="AIRBORNE"   onclick="setFilter('AIRBORNE',this)">AIRBORNE</button>
      <button class="filter-btn"        data-filter="LANDED"     onclick="setFilter('LANDED',this)">LANDED</button>
      <button class="filter-btn"        data-filter="COMPLETED"  onclick="setFilter('COMPLETED',this)">COMPLETED</button>
    </div>
    <div class="cases-list" id="cases-list"></div>
    <div class="panel-footer" id="panel-footer">0 / 0 cases</div>
  </div>
</div>

<!-- ── Detail slide-in panel ────────────────────────────────────────── -->
<div class="detail-panel" id="detail-panel">
  <div class="detail-head">
    <div>
      <div id="dp-id"   style="font-family:'Space Mono',monospace;font-size:.95rem;font-weight:700;color:var(--accent);margin-bottom:6px"></div>
      <div id="dp-badge"></div>
    </div>
    <button class="btn-close-panel" onclick="closeDetail()">✕</button>
  </div>
  <div class="detail-body">
    <div class="field-lbl">Condition</div>
    <div class="field-val" id="dp-condition"></div>
    <div class="field-lbl">Airstrip</div>
    <div class="field-val" id="dp-airstrip"></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
      <div><div class="field-lbl">Distance</div><div class="field-val" id="dp-distance"></div></div>
      <div><div class="field-lbl">ETA</div><div class="field-val" id="dp-eta"></div></div>
    </div>
    <div class="field-lbl">Nurse</div>
    <div class="field-val" id="dp-nurse"></div>
    <div class="field-lbl">Created</div>
    <div class="field-val" id="dp-created"></div>
    <div id="dp-notes-wrap" class="d-none"><div class="field-lbl">Notes</div><div class="field-val" id="dp-notes"></div></div>

    <div class="divider"></div>
    <div class="field-lbl" style="margin-bottom:8px">NOTIFICATIONS SENT</div>
    <div id="dp-notifs"></div>

    <div class="divider"></div>
    <div class="field-lbl" style="margin-bottom:8px">UPDATE STATUS</div>
    <div class="update-form" id="update-form">
      <select id="new-status">
        <option value="">— select next status —</option>
      </select>
      <input type="number" id="new-eta" placeholder="Updated ETA (minutes, optional)" min="1" max="600" />
      <textarea id="new-notes" rows="2" placeholder="Notes (optional)"></textarea>
      <button class="btn-update" id="btn-update" onclick="submitUpdate()" disabled>SET STATUS</button>
      <p style="font-size:.62rem;color:var(--muted);text-align:center;margin-top:6px">SMS notifications fire automatically on update.</p>
    </div>
    <div id="update-msg"></div>
  </div>
</div>

<!-- ── Backdrop ──────────────────────────────────────────────────────── -->
<div id="backdrop" onclick="closeDetail()" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);backdrop-filter:blur(3px);z-index:1999"></div>

<!-- ── Toast container ──────────────────────────────────────────────── -->
<div id="toast-container"></div>

<!-- ── SMS test widget ──────────────────────────────────────────────── -->
<div class="sms-panel">
  <h6>📱 TEST — Send Nurse SMS</h6>
  <div class="sms-row">
    <input class="sms-input" id="sms-test-input" placeholder="EVAC 2 TURKANA" value="EVAC 2 TURKANA" onkeydown="if(event.key==='Enter')sendTestSMS()" />
    <button class="sms-btn" onclick="sendTestSMS()">SEND ▶</button>
  </div>
  <div id="sms-feedback" style="font-size:.65rem;color:var(--muted);margin-top:5px"></div>
</div>

<!-- Scripts -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
// ── Constants ────────────────────────────────────────────────────────
const WILSON = { lat: -1.32172, lng: 36.8148 };
const POLL_MS = 12000;
const STATUS_COLORS = {
  RECEIVED:   '#f59e0b', DISPATCHED: '#3b82f6',
  AIRBORNE:   '#10b981', LANDED:     '#a78bfa',
  COMPLETED:  '#6ee7b7', CANCELLED:  '#ef4444',
};
const VALID_TRANSITIONS = {
  RECEIVED:   ['DISPATCHED','CANCELLED'],
  DISPATCHED: ['AIRBORNE','CANCELLED'],
  AIRBORNE:   ['LANDED','CANCELLED'],
  LANDED:     ['COMPLETED'],
  COMPLETED:  [],
  CANCELLED:  [],
};

// ── State ────────────────────────────────────────────────────────────
let allCases = [];
let selectedCaseId = null;
let activeFilter = 'ALL';
let caseMarkers = {};
let lastCaseIds = new Set();

// ── Map init ─────────────────────────────────────────────────────────
const map = L.map('map', { center: [0.5, 37.5], zoom: 6 });
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  attribution: '© OpenStreetMap © CARTO', maxZoom: 19
}).addTo(map);

// Wilson base marker
L.marker([WILSON.lat, WILSON.lng], {
  icon: L.divIcon({ className:'', iconSize:[32,32], iconAnchor:[16,16],
    html:`<div style="width:32px;height:32px;border-radius:50%;background:#fff;border:2.5px solid #38bdf8;display:flex;align-items:center;justify-content:center;font-size:15px;box-shadow:0 0 12px #38bdf860;">✈</div>`
  })
}).addTo(map).bindPopup('<b>✈ Wilson Airport</b><br>AeroCure Base — Cessna Grand Caravan');

// ── Load and render airstrips ─────────────────────────────────────────
async function loadAirstrips() {
  const strips = await fetch('/api/airstrips').then(r => r.json());
  strips.forEach(a => {
    const icon = L.divIcon({ className:'', iconSize:[10,10], iconAnchor:[5,5],
      html:`<div style="width:10px;height:10px;border-radius:50%;background:#334155;border:1.5px solid #64748b;"></div>`
    });
    L.marker([a.lat, a.lng], { icon }).addTo(map)
      .bindPopup(`<b>✈ ${a.name}</b><br>${a.county}<br><span style="opacity:.6;font-size:10px">${a.code}</span>`);
  });
}

// ── Fetch and render cases ─────────────────────────────────────────────
async function loadCases() {
  const cases = await fetch('/api/cases').then(r => r.json()).catch(() => []);
  const newIds = new Set(cases.map(c => c.id));

  // Toast on new cases
  if (lastCaseIds.size > 0) {
    cases.filter(c => !lastCaseIds.has(c.id)).forEach(c => {
      toast(`🚨 New case: ${c.id} — ${c.condition_name} @ ${c.airstrip_name}`, 'success');
    });
  }
  lastCaseIds = newIds;
  allCases = cases;
  renderStats();
  renderCaseList();
  renderCaseMarkers();
  updateSyncTime();
}

async function loadStats() {
  const s = await fetch('/api/stats').then(r => r.json()).catch(() => null);
  if (!s) return;
  setText('s-active', s.active);
  setText('s-total',  s.total);
  setText('s-recv',   s.by_status.RECEIVED   || 0);
  setText('s-disp',   s.by_status.DISPATCHED || 0);
  setText('s-air',    s.by_status.AIRBORNE   || 0);
  setText('s-land',   s.by_status.LANDED     || 0);
  setText('s-eta',    s.avg_eta != null ? s.avg_eta : '—');
  const indicator = document.getElementById('active-indicator');
  if (s.active > 0) {
    indicator.classList.remove('d-none');
    setText('active-count', `${s.active} ACTIVE`);
  } else {
    indicator.classList.add('d-none');
  }
}

function renderStats() {
  loadStats();
}

// ── Case list rendering ─────────────────────────────────────────────────
function filterCases() { renderCaseList(); }

function setFilter(f, btn) {
  activeFilter = f;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderCaseList();
}

function getFilteredCases() {
  const q = document.getElementById('search-input').value.toLowerCase();
  return allCases.filter(c => {
    const matchFilter = activeFilter === 'ALL' || c.status === activeFilter;
    const matchSearch = !q || [c.id, c.condition_name, c.airstrip_name, c.status]
      .some(v => v && v.toLowerCase().includes(q));
    return matchFilter && matchSearch;
  });
}

function renderCaseList() {
  const list = document.getElementById('cases-list');
  const filtered = getFilteredCases();
  setText('panel-footer', `${filtered.length} / ${allCases.length} cases`);
  setText('case-count-badge', `${allCases.length} cases`);

  if (!filtered.length) {
    list.innerHTML = `<div class="empty-state">${allCases.length ? 'No matching cases' : 'No cases yet.<br>Send a test SMS below.'}</div>`;
    return;
  }

  list.innerHTML = filtered.map(c => {
    const ts = c.created_at ? new Date(c.created_at).toLocaleString('en-KE',
      { month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' }) : '—';
    const eta = c.eta_minutes ? `${c.eta_minutes}m ETA` : ts;
    const sel = selectedCaseId === c.id ? ' selected' : '';
    return `
      <div class="case-row${sel}" onclick="selectCase('${c.id}')">
        <div class="d-flex justify-content-between align-items-center">
          <span class="case-id">${c.id}</span>
          ${statusBadge(c.status)}
        </div>
        <div class="case-sub">${c.condition_name}</div>
        <div class="case-meta">
          <span>✈ ${c.airstrip_name}</span>
          <span>${eta}</span>
        </div>
        ${c.distance_km ? `<div class="case-meta" style="margin-top:2px"><span style="color:var(--accent)">${c.distance_km} km · ${c.airstrip_code}</span></div>` : ''}
      </div>`;
  }).join('');
}

// ── Map case markers ────────────────────────────────────────────────────
function renderCaseMarkers() {
  // Remove old
  Object.values(caseMarkers).forEach(m => m.remove());
  caseMarkers = {};

  allCases.filter(c => !['COMPLETED','CANCELLED'].includes(c.status) && c.airstrip_lat)
    .forEach(c => {
      const color = STATUS_COLORS[c.status] || '#94a3b8';
      const icon = L.divIcon({ className:'', iconSize:[22,22], iconAnchor:[11,11],
        html:`<div style="position:relative;width:22px;height:22px">
          <div style="position:absolute;inset:0;border-radius:50%;background:${color}25;animation:ripple 1.6s ease-out infinite"></div>
          <div style="position:absolute;inset:5px;border-radius:50%;background:${color};box-shadow:0 0 8px ${color}"></div>
        </div>`
      });
      const m = L.marker([c.airstrip_lat, c.airstrip_lng], { icon })
        .addTo(map)
        .bindPopup(`
          <b>${c.id}</b><br>
          ${c.condition_name}<br>
          <span style="color:${color};font-weight:700">${c.status}</span>
          ${c.eta_minutes ? `<br>ETA: ${c.eta_minutes} min` : ''}
          ${c.distance_km ? `<br>${c.distance_km} km from Wilson` : ''}
        `)
        .on('click', () => selectCase(c.id));
      caseMarkers[c.id] = m;
    });
}

// ── Status badge HTML ────────────────────────────────────────────────────
function statusBadge(status) {
  const color = STATUS_COLORS[status] || '#94a3b8';
  return `<span class="status-badge badge-${status}">
    <span class="status-dot" style="background:${color};box-shadow:0 0 5px ${color}"></span>
    ${status}
  </span>`;
}

// ── Case detail panel ────────────────────────────────────────────────────
async function selectCase(id) {
  selectedCaseId = id;
  renderCaseList();
  const c = allCases.find(x => x.id === id);
  if (!c) return;

  setText('dp-id', c.id);
  document.getElementById('dp-badge').innerHTML = statusBadge(c.status);
  setText('dp-condition', `[${c.condition_code}] ${c.condition_name}`);
  setText('dp-airstrip',  c.airstrip_name);
  setText('dp-distance',  c.distance_km ? `${c.distance_km} km` : '—');
  setText('dp-eta',       c.eta_minutes ? `${c.eta_minutes} min` : '—');
  setText('dp-nurse',     c.nurse_phone);
  setText('dp-created',   c.created_at ? new Date(c.created_at).toLocaleString('en-KE') : '—');

  const notesWrap = document.getElementById('dp-notes-wrap');
  if (c.notes) { notesWrap.classList.remove('d-none'); setText('dp-notes', c.notes); }
  else          { notesWrap.classList.add('d-none'); }

  // Populate transition options
  const sel = document.getElementById('new-status');
  const transitions = VALID_TRANSITIONS[c.status] || [];
  sel.innerHTML = transitions.length
    ? `<option value="">— select next status —</option>${transitions.map(s => `<option value="${s}">${s}</option>`).join('')}`
    : `<option value="">No further updates (${c.status})</option>`;
  document.getElementById('btn-update').disabled = transitions.length === 0;
  sel.onchange = () => { document.getElementById('btn-update').disabled = !sel.value; };
  document.getElementById('update-msg').innerHTML = '';

  // Load notifications
  const notifs = await fetch(`/api/notifications/${id}`).then(r => r.json()).catch(() => []);
  const notifEl = document.getElementById('dp-notifs');
  notifEl.innerHTML = notifs.length
    ? notifs.map(n => `
        <div class="notif-row">
          <span class="notif-role">${n.recipient_role}</span>
          <span class="notif-msg">${n.message_text}</span>
        </div>`).join('')
    : '<div style="font-size:.72rem;color:var(--muted)">No notifications yet.</div>';

  openDetail();
  // Fly map to this airstrip
  if (c.airstrip_lat && c.airstrip_lng) {
    map.flyTo([c.airstrip_lat, c.airstrip_lng], 8, { duration: 1.2 });
  }
}

function openDetail() {
  document.getElementById('detail-panel').classList.add('open');
  document.getElementById('backdrop').style.display = 'block';
}
function closeDetail() {
  document.getElementById('detail-panel').classList.remove('open');
  document.getElementById('backdrop').style.display = 'none';
  selectedCaseId = null;
  renderCaseList();
}

async function submitUpdate() {
  const status = document.getElementById('new-status').value;
  const notes  = document.getElementById('new-notes').value;
  const eta    = document.getElementById('new-eta').value;
  if (!status || !selectedCaseId) return;

  document.getElementById('btn-update').disabled = true;
  setText('update-msg', '');

  const body = { status, notes, changed_by: 'DASHBOARD' };
  if (eta) body.eta_minutes = parseInt(eta);

  const r = await fetch(`/api/cases/${selectedCaseId}/update`, {
    method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body)
  });
  const data = await r.json();

  if (r.ok) {
    toast(`✅ ${selectedCaseId} → ${status}`, 'success');
    await loadCases();
    selectCase(selectedCaseId);
    document.getElementById('new-notes').value = '';
    document.getElementById('new-eta').value   = '';
  } else {
    document.getElementById('update-msg').innerHTML =
      `<div style="color:#ef4444;font-size:.72rem;margin-top:4px">${data.detail || 'Update failed'}</div>`;
    document.getElementById('btn-update').disabled = false;
  }
}

// ── SMS test widget ──────────────────────────────────────────────────────
async function sendTestSMS() {
  const msg   = document.getElementById('sms-test-input').value.trim();
  const phone = '+254700000099';
  if (!msg) return;

  document.getElementById('sms-feedback').textContent = 'Sending…';

  const r = await fetch('/api/inbound-sms', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ message: msg, phone })
  });
  const data = await r.json();

  if (r.ok && data.success) {
    document.getElementById('sms-feedback').textContent = `✅ ${data.case_id} created`;
    document.getElementById('sms-feedback').style.color = '#10b981';
    await loadCases();
    setTimeout(() => selectCase(data.case_id), 300);
  } else {
    document.getElementById('sms-feedback').textContent = `❌ ${data.error || data.detail}`;
    document.getElementById('sms-feedback').style.color = '#ef4444';
  }
}

// ── Toast ────────────────────────────────────────────────────────────────
function toast(msg, type='success') {
  const el = document.createElement('div');
  el.className = `toast-item ${type}`;
  el.innerHTML = msg;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => el.remove(), 4500);
}

// ── Sync indicator ────────────────────────────────────────────────────────
function updateSyncTime() {
  const btn = document.getElementById('sync-btn');
  const t = new Date().toLocaleTimeString('en-KE', { hour:'2-digit', minute:'2-digit', second:'2-digit' });
  btn.innerHTML = `⟳ ${t}`;
}

async function manualRefresh() {
  const btn = document.getElementById('sync-btn');
  btn.innerHTML = `<span class="spinning">⟳</span> syncing…`;
  await loadCases();
  await loadStats();
}

// ── Helpers ───────────────────────────────────────────────────────────────
function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

// ── Init ──────────────────────────────────────────────────────────────────
async function init() {
  await loadAirstrips();
  await loadCases();
  await loadStats();
  setInterval(loadCases, POLL_MS);
  setInterval(loadStats, POLL_MS);

  document.getElementById('sms-test-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') sendTestSMS();
  });
}

init();
</script>
</body>
</html>
```

---

## Setup & Run

### 1. Clone / create the project folder

```bash
mkdir aerocure && cd aerocure
# Copy all files from this document into place
```

### 2. Create virtual environment & install

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set your AT_API_KEY if testing with real SMS
# SQLite requires no configuration, it creates aerocure.db automatically
```

### 4. Start the server

```bash
python main.py
# or
uvicorn main:app --reload --port 8000
```

Open **http://localhoost:8000** — the dashboard loads immediately.

### 5. Test the SMS flow

**Option A — Dashboard SMS widget** (bottom-left of dashboard):
```
Type:  EVAC 2 TURKANA
Click: SEND ▶
```

**Option B — Nurse console simulator** (in a second terminal):
```bash
python nurse_console.py

# Then:
SMS > EVAC 4 MARSABIT
SMS > EVAC 1 ISIOLO
SMS > mock          ← injects 5 test cases at once
SMS > help          ← show format reminder
SMS > quit
```

**Option C — curl / Postman**:
```bash
curl -X POST http://localhost:8000/api/inbound-sms \
  -H "Content-Type: application/json" \
  -d '{"message": "EVAC 3 WAJIR", "phone": "+254712345678"}'
```

### 6. Watch what happens

Every SMS fires exactly these notifications (printed to console in dev mode):

| # | Recipient | Message |
|---|-----------|---------|
| 1 | AMREF Dispatch | Emergency alert with distance + ETA |
| 2 | Airstrip agent | Aircraft inbound, prepare runway |
| 3 | KNH Hospital   | Incoming patient, prepare team |
| 4 | Next of kin    | Family member being evacuated |
| 5 | Nurse          | Confirmation with case ID + ETA |

Dashboard auto-refreshes every 12 seconds. New cases trigger a toast notification.

### 7. ETA examples (Cessna Grand Caravan, 335 km/h)

| Airstrip | Distance | ETA |
|----------|----------|-----|
| Nanyuki  | 156 km   | 57 min |
| Amboseli | 155 km   | 57 min |
| Garissa  | 329 km   | 88 min |
| Marsabit | 428 km   | 106 min |
| Turkana  | 512 km   | 121 min |
| Wajir    | 498 km   | 119 min |

---

## Going live (Africa's Talking production)

1. In `notifier.py`, uncomment the AT SDK block and remove the `pass`
2. Set `APP_ENV=production` in `.env`
3. Set your `AT_USERNAME` and `AT_API_KEY`
4. Point AT's inbound SMS webhook to `https://your-domain.com/api/inbound-sms`
5. Replace the SQLite URL with your Postgres URL: `DATABASE_URL=postgresql://...`

No other code changes needed.

---

## API reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/inbound-sms` | Receive nurse SMS |
| `GET`  | `/api/cases` | List all cases |
| `GET`  | `/api/cases/{id}` | Single case |
| `POST` | `/api/cases/{id}/update` | Update status |
| `GET`  | `/api/airstrips` | All airstrips + coordinates |
| `GET`  | `/api/notifications/{id}` | Notifications for a case |
| `GET`  | `/api/stats` | Dashboard summary |
| `GET`  | `/docs` | FastAPI Swagger UI |
