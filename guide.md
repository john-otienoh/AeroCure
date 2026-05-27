# 🚑✈️ AEROCURE — Complete 72-Hour MVP Build Guide
### Emergency Medical Airlift Coordination via SMS + Voice (Africa's Talking APIs)
> Python Stack | Stepwise Roadmap | Non-Technical Flow | Tools & Resources

---

## 🧠 What Is AeroCure? (Plain English, No Tech Jargon)

Imagine a nurse in a remote clinic in Turkana. A patient just arrived with a severe snakebite.
The nearest hospital that can treat them is in Nairobi — 600km away by road. The only option is an air ambulance.

**Right now, here is what the nurse has to do:**
1. Find a satellite phone or hope mobile signal works
2. Scroll through a WhatsApp contact list to find the AMREF dispatcher
3. Call, explain everything verbally, hope the dispatcher is awake and writes it down correctly
4. Call the airstrip agent separately to warn them
5. Call the hospital separately to prepare
6. Wait, with no idea if anyone is coming or when

**This takes 2–4 hours on average. The patient often doesn't survive.**

---

**AeroCure changes this to one SMS.**

The nurse types: `EVAC 4 TURKANA` and sends it to a shortcode number.

That single SMS automatically:
- Calls the AMREF dispatch office and reads out the emergency details in a voice call
- Sends a text to the airstrip agent at Turkana airstrip
- Sends a text to the receiving hospital in Nairobi
- Sends a text to the patient's registered next of kin
- Sends the nurse a confirmation with a case ID and estimated aircraft arrival time

The nurse can then check updates anytime by dialing a USSD code like `*384*EVAC#`.

The dispatcher has a computer screen (dashboard) showing all active cases, where aircraft are, and who has been contacted.

**That is AeroCure. One SMS. Five actions. Lives saved.**

---

## 🗺️ How The System Works — Step by Step (Simple Version)

```
NURSE (Feature Phone)
        |
        | Sends SMS: "EVAC 4 TURKANA"
        |
        ▼
[AeroCure Server — The Brain]
        |
        |── Creates a Case (like a ticket number: EVAC-2025-001)
        |── Figures out: condition = Snakebite, location = Turkana Airstrip
        |
        |── CALLS dispatch centre (automated robot voice reads the emergency)
        |── TEXTS airstrip agent at Turkana
        |── TEXTS receiving hospital in Nairobi
        |── TEXTS patient's next of kin
        |── TEXTS nurse back: "Case EVAC-2025-001 created. Aircraft ETA: 90 min"
        |
        ▼
[Dispatch Dashboard — What the operator sees]
        |
        |── List of all active emergencies
        |── Map showing pickup airstrip and hospital
        |── One-click to send update SMS to everyone
        |── Tracks how long each case has been open
        |
        ▼
NURSE dials *384*EVAC# → types case ID → sees latest status update
```

---

## 📋 Project Pieces (What You Are Building)

| Piece | What It Does | How Hard |
|---|---|---|
| **SMS Receiver** | Listens for incoming EVAC SMS, reads it, triggers actions | ⭐⭐ |
| **SMS Parser** | Reads "EVAC 4 TURKANA", extracts condition + location | ⭐⭐ |
| **Voice Caller** | Calls dispatch, robot voice reads emergency details | ⭐⭐ |
| **SMS Blaster** | Sends texts to 4 people at once | ⭐ |
| **USSD Handler** | Lets nurse check case status by dialing a code | ⭐⭐⭐ |
| **Database** | Stores all cases, contacts, airstrips | ⭐⭐ |
| **Dashboard** | Web page showing all active cases with map | ⭐⭐⭐ |
| **Airtime Reward** | Sends nurse KES 5 airtime when case completes | ⭐ |

---

## 🧰 Your Complete Python Toolbox

### Core Language & Framework
```
Python 3.11+          — the programming language
FastAPI               — builds your web server (handles webhooks from AT)
Uvicorn               — runs your FastAPI server
```

### Database
```
PostgreSQL            — stores all data (cases, airstrips, contacts)
SQLAlchemy            — Python library to talk to PostgreSQL
Alembic               — manages database structure changes
psycopg2-binary       — connects Python to PostgreSQL
```

### Africa's Talking
```
africastalking        — official Python SDK for AT APIs
                        pip install africastalking
```

### Utilities
```
python-dotenv         — loads secret keys from a .env file safely
pydantic              — validates incoming data shapes
httpx                 — sends HTTP requests
Jinja2                — builds HTML templates for the dashboard
```

### Frontend (simple, no React needed)
```
HTML + CSS + JavaScript  — plain, no framework
Leaflet.js (CDN)         — interactive map (loaded from internet, no install)
Chart.js (CDN)           — charts for the dashboard
```

### Infrastructure
```
Supabase              — free PostgreSQL database in the cloud (easiest setup)
Railway               — hosts your Python server for free
ngrok                 — tunnels your local server to internet (for AT webhooks during dev)
GitHub                — stores your code
```

### Dev Tools
```
Postman               — tests your API endpoints without writing code
VS Code               — code editor
Python-decouple       — alternative to dotenv for config
```

---

## 📦 Install Everything At Once

Create a file called `requirements.txt`:

```txt
fastapi==0.111.0
uvicorn==0.29.0
sqlalchemy==2.0.30
alembic==1.13.1
psycopg2-binary==2.9.9
africastalking==1.2.7
python-dotenv==1.0.1
pydantic==2.7.1
httpx==0.27.0
jinja2==3.1.4
```

Then run:
```bash
pip install -r requirements.txt
```

---

## 🗂️ Project Folder Structure

```
aerocure/
│
├── main.py                  ← FastAPI app entry point
├── requirements.txt         ← all Python packages
├── .env                     ← secret keys (NEVER commit to GitHub)
├── .env.example             ← safe template to share
│
├── app/
│   ├── __init__.py
│   ├── config.py            ← loads environment variables
│   ├── database.py          ← database connection setup
│   │
│   ├── models/
│   │   ├── case.py          ← Case table structure
│   │   ├── airstrip.py      ← Airstrip table structure
│   │   └── facility.py      ← Hospital/clinic table structure
│   │
│   ├── routes/
│   │   ├── sms.py           ← handles incoming SMS from AT
│   │   ├── ussd.py          ← handles USSD sessions
│   │   ├── voice.py         ← handles voice call flow
│   │   └── dashboard.py     ← serves dashboard HTML
│   │
│   ├── services/
│   │   ├── at_service.py    ← Africa's Talking functions (send SMS, call, etc.)
│   │   ├── case_service.py  ← business logic for creating/updating cases
│   │   └── notify_service.py ← sends notifications to stakeholders
│   │
│   └── templates/
│       ├── dashboard.html   ← main dashboard page
│       └── case_detail.html ← single case view
│
├── seed/
│   └── seed_data.py         ← loads airstrips, hospitals, demo cases
│
└── alembic/                 ← database migration files
    └── versions/
```

---

## 🌍 Reference Data You Need (Pre-seed this)

### Condition Codes (Patient Condition)
```python
CONDITION_CODES = {
    "1": "Trauma / Accident",
    "2": "Obstetric Emergency",
    "3": "Cardiac / Chest Pain",
    "4": "Snakebite / Poisoning",
    "5": "Paediatric Emergency",
    "6": "Other / Unknown"
}
```

### Sample Airstrip Codes
```python
AIRSTRIPS = [
    {"code": "TURKANA",   "name": "Lodwar Airstrip",         "lat": 3.1219,  "lng": 35.6087},
    {"code": "MARSABIT",  "name": "Marsabit Airport",        "lat": 2.3383,  "lng": 37.9993},
    {"code": "ISIOLO",    "name": "Isiolo Airport",          "lat": 0.3382,  "lng": 37.5924},
    {"code": "NANYUKI",   "name": "Nanyuki Airport",         "lat": 0.0624,  "lng": 37.0410},
    {"code": "MARALAL",   "name": "Maralal Airstrip",        "lat": 1.1031,  "lng": 36.6980},
    {"code": "AMBOSELI",  "name": "Amboseli Airport",        "lat": -2.6455, "lng": 37.2531},
    {"code": "WILSON",    "name": "Wilson Airport Nairobi",  "lat": -1.3217, "lng": 36.8145},
    {"code": "LAMU",      "name": "Manda Airport Lamu",      "lat": -2.2524, "lng": 40.9131},
]
```

---

# ⏱️ 72-HOUR STEPWISE ROADMAP

---

## ✅ PHASE 0 — SETUP (Hours 0–3)
> Goal: Everything installed, accounts created, keys in hand

### Step 0.1 — Create Africa's Talking Sandbox Account
1. Go to [africastalking.com](https://africastalking.com) → Sign up
2. Go to Sandbox → Create an app called `aerocure`
3. Note down:
   - `API_KEY`
   - `USERNAME` (usually your app name)
4. In Sandbox → SMS → set your shortcode (use the default sandbox shortcode)
5. In Sandbox → Voice → enable inbound calls
6. In Sandbox → USSD → create a service with code `*384*EVAC#`

### Step 0.2 — Create Supabase Database
1. Go to [supabase.com](https://supabase.com) → New Project
2. Name it `aerocure` → pick a strong password → region: `East Africa`
3. After setup, go to Settings → Database → copy the `Connection String (URI)`
4. Looks like: `postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres`

### Step 0.3 — Set Up ngrok (for local development)
```bash
# Install ngrok
brew install ngrok   # Mac
# OR download from ngrok.com for Windows/Linux

# Start tunnel (run this when your server is running on port 8000)
ngrok http 8000
# Copy the https URL — e.g. https://abc123.ngrok.io
# This is your webhook base URL for Africa's Talking callbacks
```

### Step 0.4 — Create Project and .env File
```bash
mkdir aerocure && cd aerocure
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env`:
```env
# Africa's Talking
AT_API_KEY=your_sandbox_api_key_here
AT_USERNAME=sandbox
AT_SENDER_ID=AEROCURE
AT_SHORTCODE=your_shortcode

# Database
DATABASE_URL=postgresql://postgres:password@db.ref.supabase.co:5432/postgres

# App
BASE_URL=https://abc123.ngrok.io
DISPATCH_PHONE=+254700000001
APP_ENV=development
```

### 📦 Phase 0 Deliverables
- [ ] Africa's Talking sandbox account active, API key in hand
- [ ] Supabase database created, connection string saved
- [ ] ngrok running and tunnel URL known
- [ ] `.env` file populated with all keys
- [ ] Virtual environment active, all packages installed
- [ ] Project folder structure created

---

## ✅ PHASE 1 — DATABASE + CORE MODELS (Hours 3–10)
> Goal: Database tables created, seed data loaded

### Step 1.1 — Database Connection (`app/database.py`)
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Step 1.2 — Case Model (`app/models/case.py`)
```python
from sqlalchemy import Column, String, DateTime, Integer, Float, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

class CaseStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    DISPATCHED = "DISPATCHED"
    AIRBORNE = "AIRBORNE"
    LANDED = "LANDED"
    COMPLETED = "COMPLETED"

class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True)           # e.g. EVAC-2025-001
    condition_code = Column(String(2), nullable=False)
    condition_name = Column(String(100), nullable=False)
    airstrip_code = Column(String(30), nullable=False)
    airstrip_name = Column(String(100), nullable=False)
    initiating_phone = Column(String(20), nullable=False)  # masked
    status = Column(Enum(CaseStatus), default=CaseStatus.RECEIVED)
    eta_minutes = Column(Integer, nullable=True)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Step 1.3 — Airstrip Model (`app/models/airstrip.py`)
```python
from sqlalchemy import Column, String, Float
from app.database import Base

class Airstrip(Base):
    __tablename__ = "airstrips"

    code = Column(String(30), primary_key=True)
    name = Column(String(100), nullable=False)
    county = Column(String(60), nullable=True)
    agent_phone = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
```

### Step 1.4 — Create Tables + Seed Data
```python
# seed/seed_data.py
from app.database import engine, SessionLocal
from app.models.case import Base as CaseBase
from app.models.airstrip import Airstrip

# Create all tables
CaseBase.metadata.create_all(bind=engine)

db = SessionLocal()

airstrips = [
    Airstrip(code="TURKANA",  name="Lodwar Airstrip",   agent_phone="+254711000001", latitude=3.1219,  longitude=35.6087),
    Airstrip(code="MARSABIT", name="Marsabit Airport",  agent_phone="+254711000002", latitude=2.3383,  longitude=37.9993),
    Airstrip(code="ISIOLO",   name="Isiolo Airport",    agent_phone="+254711000003", latitude=0.3382,  longitude=37.5924),
    Airstrip(code="NANYUKI",  name="Nanyuki Airport",   agent_phone="+254711000004", latitude=0.0624,  longitude=37.0410),
    Airstrip(code="AMBOSELI", name="Amboseli Airport",  agent_phone="+254711000005", latitude=-2.6455, longitude=37.2531),
]

db.add_all(airstrips)
db.commit()
db.close()
print("✅ Seed data loaded")
```

Run it:
```bash
python seed/seed_data.py
```

### 📦 Phase 1 Deliverables
- [ ] `cases` table created in Supabase (verify in Supabase table editor)
- [ ] `airstrips` table created and populated with 5+ airstrips
- [ ] `get_db()` dependency working
- [ ] `python seed/seed_data.py` runs without errors

---

## ✅ PHASE 2 — AFRICA'S TALKING SERVICE LAYER (Hours 10–18)
> Goal: Every AT API action wrapped in clean Python functions you can call anywhere

### Step 2.1 — AT Initialisation (`app/services/at_service.py`)
```python
import africastalking
from app.config import settings

# Initialise once
africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)

sms_service   = africastalking.SMS
voice_service = africastalking.Voice
airtime_service = africastalking.Airtime

# ── SMS ────────────────────────────────────────────────────────
def send_sms(to: str | list, message: str) -> dict:
    """Send an SMS to one number or a list of numbers."""
    recipients = to if isinstance(to, list) else [to]
    response = sms_service.send(message, recipients)
    return response

# ── VOICE ──────────────────────────────────────────────────────
def call_dispatch(case_id: str, condition: str, airstrip: str) -> dict:
    """
    Call the dispatch centre and read out emergency details using TTS.
    AT Voice API accepts an XML-like ActionScript for call flow.
    """
    # The callFrom is your AT voice number
    response = voice_service.call(
        callFrom=settings.AT_VOICE_NUMBER,
        callTo=[settings.DISPATCH_PHONE]
    )
    return response

def build_voice_response(case_id: str, condition: str, airstrip: str) -> str:
    """
    Returns the XML that AT Voice API plays when the dispatcher picks up.
    This runs at the /voice/dispatch webhook endpoint.
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="woman" playBeep="true">
        Emergency Alert. AeroCure Case ID: {case_id}.
        Patient condition: {condition}.
        Pickup location: {airstrip} Airstrip.
        Please confirm receipt and dispatch an aircraft immediately.
        This call was generated automatically by AeroCure.
    </Say>
    <Say>Press 1 to confirm receipt of this emergency.</Say>
    <GetDigits timeout="10" finishOnKey="#">
        <Say>Press 1 to confirm.</Say>
    </GetDigits>
</Response>"""

# ── AIRTIME ────────────────────────────────────────────────────
def send_airtime(phone: str, amount: str = "5", currency: str = "KES") -> dict:
    """Send KES 5 airtime reward to the initiating nurse."""
    recipients = [{"phoneNumber": phone, "amount": f"{currency} {amount}"}]
    response = airtime_service.send(recipients=recipients)
    return response
```

### Step 2.2 — Notification Service (`app/services/notify_service.py`)
```python
from app.services.at_service import send_sms, call_dispatch
from app.models.airstrip import Airstrip

HOSPITAL_PHONE = "+254722000010"   # demo: Kenyatta National Hospital duty desk
KIN_PHONE = "+254733000020"        # in real system, looked up from patient registry

def notify_all_stakeholders(case_id: str, condition: str, airstrip: Airstrip, nurse_phone: str):
    """Fire all notifications the moment a valid EVAC SMS is received."""

    # 1. Call dispatch (voice)
    call_dispatch(case_id, condition, airstrip.name)

    # 2. SMS airstrip agent
    send_sms(
        airstrip.agent_phone,
        f"[AEROCURE ALERT] Medical evacuation incoming to {airstrip.name}. "
        f"Case: {case_id} | Condition: {condition}. "
        f"Prepare airstrip immediately. Reply STATUS {case_id} for updates."
    )

    # 3. SMS receiving hospital
    send_sms(
        HOSPITAL_PHONE,
        f"[AEROCURE ALERT] Incoming air evacuation patient. "
        f"Case: {case_id} | Condition: {condition} | Origin: {airstrip.name}. "
        f"Please prepare receiving team."
    )

    # 4. SMS next of kin
    send_sms(
        KIN_PHONE,
        f"[AEROCURE] Your family member is receiving emergency medical care. "
        f"They are being evacuated by air. Case reference: {case_id}. "
        f"You will receive updates on this number."
    )

    # 5. Confirm back to nurse
    send_sms(
        nurse_phone,
        f"[AEROCURE] ✅ Case {case_id} created. "
        f"Dispatch has been called. Airstrip agent, hospital, and next of kin notified. "
        f"Estimated aircraft arrival: 90 minutes. "
        f"Check updates: dial *384*EVAC# and enter {case_id}"
    )
```

### 📦 Phase 2 Deliverables
- [ ] `at_service.py` with `send_sms()`, `call_dispatch()`, `build_voice_response()`, `send_airtime()`
- [ ] `notify_service.py` with `notify_all_stakeholders()`
- [ ] Manual test: call `send_sms()` directly in Python shell → SMS arrives in AT sandbox simulator
- [ ] Manual test: call `call_dispatch()` → call appears in AT sandbox voice simulator

---

## ✅ PHASE 3 — SMS HANDLER (Hours 18–26)
> Goal: Server receives EVAC SMS, parses it, creates a case, fires all notifications

### Step 3.1 — Case Service (`app/services/case_service.py`)
```python
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.case import Case, CaseStatus
from app.models.airstrip import Airstrip

CONDITION_CODES = {
    "1": "Trauma / Accident",
    "2": "Obstetric Emergency",
    "3": "Cardiac / Chest Pain",
    "4": "Snakebite / Poisoning",
    "5": "Paediatric Emergency",
    "6": "Other / Unknown"
}

def parse_evac_sms(body: str) -> tuple[str, str] | None:
    """
    Parse 'EVAC 4 TURKANA' → ('4', 'TURKANA')
    Returns None if format is wrong.
    """
    parts = body.strip().upper().split()
    if len(parts) != 3 or parts[0] != "EVAC":
        return None
    condition_code = parts[1]
    airstrip_code = parts[2]
    if condition_code not in CONDITION_CODES:
        return None
    return condition_code, airstrip_code

def create_case(db: Session, condition_code: str, airstrip_code: str, nurse_phone: str) -> Case | None:
    """Look up airstrip, create case record, return it."""
    airstrip = db.query(Airstrip).filter(Airstrip.code == airstrip_code).first()
    if not airstrip:
        return None  # unknown airstrip code

    # Generate case ID: EVAC-YYYYMMDD-XXXX
    case_id = f"EVAC-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

    case = Case(
        id=case_id,
        condition_code=condition_code,
        condition_name=CONDITION_CODES[condition_code],
        airstrip_code=airstrip_code,
        airstrip_name=airstrip.name,
        initiating_phone=nurse_phone[-4:].zfill(4),  # store only last 4 digits for anonymity
        status=CaseStatus.RECEIVED,
        eta_minutes=90  # default; dispatcher updates this
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case, airstrip
```

### Step 3.2 — SMS Route (`app/routes/sms.py`)
```python
from fastapi import APIRouter, Form, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.case_service import parse_evac_sms, create_case
from app.services.notify_service import notify_all_stakeholders
from app.services.at_service import send_sms

router = APIRouter()

@router.post("/sms/incoming")
async def handle_incoming_sms(
    from_: str = Form(alias="from"),
    text: str = Form(),
    db: Session = Depends(get_db)
):
    """
    Africa's Talking POSTs to this endpoint when an SMS arrives.
    AT sends fields: 'from', 'text', 'to', 'date', 'id'
    """
    nurse_phone = from_
    sms_body = text.strip()

    # Step 1: Try to parse the EVAC command
    parsed = parse_evac_sms(sms_body)

    if not parsed:
        # Invalid format — send helpful error SMS
        send_sms(
            nurse_phone,
            "❌ Invalid format. Send: EVAC [code] [airstrip]\n"
            "Codes: 1=Trauma 2=OB 3=Cardiac 4=Snakebite 5=Paediatric 6=Other\n"
            "Example: EVAC 4 TURKANA"
        )
        return {"status": "invalid_format"}

    condition_code, airstrip_code = parsed

    # Step 2: Create the case in database
    result = create_case(db, condition_code, airstrip_code, nurse_phone)

    if not result:
        send_sms(
            nurse_phone,
            f"❌ Unknown airstrip code '{airstrip_code}'. "
            f"Please check the code and resend. Reply HELP for airstrip list."
        )
        return {"status": "unknown_airstrip"}

    case, airstrip = result

    # Step 3: Fire all notifications (dispatch call + 4 SMS)
    notify_all_stakeholders(
        case_id=case.id,
        condition=case.condition_name,
        airstrip=airstrip,
        nurse_phone=nurse_phone
    )

    return {"status": "case_created", "case_id": case.id}
```

**Set this as your AT SMS webhook:**
`https://abc123.ngrok.io/sms/incoming`

### 📦 Phase 3 Deliverables
- [ ] `POST /sms/incoming` endpoint working
- [ ] Valid EVAC SMS creates a case in the database
- [ ] Invalid SMS returns helpful error message
- [ ] Unknown airstrip code returns helpful error
- [ ] `notify_all_stakeholders()` fires on valid case creation
- [ ] Test with Postman: POST to `/sms/incoming` with `from=+254700000001&text=EVAC 4 TURKANA`
- [ ] Verify case appears in Supabase table editor

---

## ✅ PHASE 4 — USSD HANDLER (Hours 26–34)
> Goal: Nurse dials *384*EVAC#, enters case ID, sees current status

### How AT USSD Works (Simple Explanation)
AT sends a POST request to your server every time the user presses a button.
Your server must reply within 5 seconds with a text response.
You tell AT either `CON` (continue — show more menus) or `END` (end — close session).

### Step 4.1 — USSD Route (`app/routes/ussd.py`)
```python
from fastapi import APIRouter, Form, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.case import Case

router = APIRouter()

@router.post("/ussd")
async def handle_ussd(
    sessionId: str = Form(),
    serviceCode: str = Form(),
    phoneNumber: str = Form(),
    text: str = Form(default=""),
    db: Session = Depends(get_db)
):
    """
    AT USSD sends sessionId, serviceCode, phoneNumber, text
    'text' accumulates all user inputs: "" → "1" → "1*EVAC-20250601-A1B2"
    """
    user_input = text.strip()
    inputs = user_input.split("*") if user_input else []
    level = len(inputs)

    # Level 0 — First dial, show main menu
    if level == 0:
        return _ussd_response("CON",
            "🚑 Welcome to AeroCure\n"
            "1. Check case status\n"
            "2. List my active cases\n"
            "3. Report case update\n"
            "0. Exit"
        )

    first_choice = inputs[0]

    # Option 1 — Check case status
    if first_choice == "1":
        if level == 1:
            return _ussd_response("CON", "Enter your Case ID:\n(e.g. EVAC-20250601-A1B2)")
        if level == 2:
            case_id = inputs[1].upper()
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                return _ussd_response("END", f"❌ Case {case_id} not found.\nCheck the ID and try again.")
            eta_text = f"ETA: {case.eta_minutes} min" if case.eta_minutes else "ETA: Pending"
            return _ussd_response("END",
                f"✅ Case: {case.id}\n"
                f"Status: {case.status.value}\n"
                f"Condition: {case.condition_name}\n"
                f"Pickup: {case.airstrip_name}\n"
                f"{eta_text}\n"
                f"Updated: {case.updated_at or case.created_at}"
            )

    # Option 2 — List active cases for this phone
    elif first_choice == "2":
        # In demo, show last 3 cases (in prod, filter by initiating phone)
        cases = db.query(Case).filter(
            Case.status.in_(["RECEIVED", "DISPATCHED", "AIRBORNE"])
        ).order_by(Case.created_at.desc()).limit(3).all()

        if not cases:
            return _ussd_response("END", "No active cases found.")

        lines = ["Active Cases:"]
        for c in cases:
            lines.append(f"• {c.id} | {c.status.value}")
        return _ussd_response("END", "\n".join(lines))

    # Option 0 — Exit
    elif first_choice == "0":
        return _ussd_response("END", "Thank you. Stay safe. 🚑")

    else:
        return _ussd_response("END", "Invalid option. Please dial again.")


def _ussd_response(action: str, message: str) -> dict:
    """Helper — AT expects plain text starting with CON or END."""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(f"{action} {message}")
```

**Set this as your AT USSD webhook:**
`https://abc123.ngrok.io/ussd`

### 📦 Phase 4 Deliverables
- [ ] `POST /ussd` endpoint returning correct CON/END responses
- [ ] Menu level 0: main menu displayed
- [ ] Menu level 1→2: case ID entry → status returned
- [ ] Test in Africa's Talking USSD simulator (Sandbox → USSD → Simulate)
- [ ] Invalid case ID returns friendly error

---

## ✅ PHASE 5 — VOICE WEBHOOK (Hours 34–38)
> Goal: When dispatch picks up the AT-initiated call, they hear the emergency details

### Step 5.1 — Voice Route (`app/routes/voice.py`)
```python
from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse
from app.services.at_service import build_voice_response

router = APIRouter()

@router.post("/voice/dispatch")
async def dispatch_call_handler(
    sessionId: str = Form(),
    isActive: str = Form(default="1"),
    dtmfDigits: str = Form(default=""),
    # AT also sends: callerNumber, destinationNumber, durationInSeconds
):
    """
    AT calls this webhook during the outbound call to dispatch.
    Returns XML telling AT what audio to play.
    """
    # For demo, use a fixed case summary
    # In production, look up case by sessionId stored at call initiation
    xml = build_voice_response(
        case_id="EVAC-2025-DEMO",
        condition="Snakebite / Poisoning",
        airstrip="Turkana (Lodwar) Airstrip"
    )
    return PlainTextResponse(xml, media_type="application/xml")
```

**Set this as your AT Voice callback URL:**
`https://abc123.ngrok.io/voice/dispatch`

### 📦 Phase 5 Deliverables
- [ ] `POST /voice/dispatch` returns valid AT Voice XML
- [ ] Test via AT Voice simulator — call plays correct TTS message
- [ ] Dispatcher hears: case ID, condition, pickup airstrip, instructions

---

## ✅ PHASE 6 — DASHBOARD (Hours 38–54)
> Goal: Web page showing all cases, a map, and ability for operator to update status

### Step 6.1 — Dashboard API Endpoints (`app/routes/dashboard.py`)
```python
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.case import Case, CaseStatus
from app.services.at_service import send_sms

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Serve the main dashboard HTML page."""
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    active_count = sum(1 for c in cases if c.status not in [CaseStatus.COMPLETED])
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "cases": cases,
        "active_count": active_count,
        "total_count": len(cases)
    })

@router.get("/api/cases")
async def get_cases(db: Session = Depends(get_db)):
    """JSON endpoint for the map and live updates."""
    cases = db.query(Case).order_by(Case.created_at.desc()).limit(50).all()
    return [
        {
            "id": c.id,
            "condition": c.condition_name,
            "airstrip": c.airstrip_name,
            "status": c.status.value,
            "eta_minutes": c.eta_minutes,
            "created_at": str(c.created_at)
        }
        for c in cases
    ]

@router.post("/api/cases/{case_id}/update")
async def update_case_status(
    case_id: str,
    status: str,
    notes: str = "",
    db: Session = Depends(get_db)
):
    """Dispatcher updates case status — triggers SMS to all stakeholders."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return {"error": "Case not found"}

    case.status = status
    case.notes = notes
    db.commit()

    # Notify stakeholders of status change
    send_sms(
        "+254700000001",  # in prod: stored nurse phone
        f"[AEROCURE UPDATE] Case {case_id} status: {status}. {notes}"
    )

    return {"status": "updated", "case_id": case_id, "new_status": status}
```

### Step 6.2 — Dashboard HTML (`app/templates/dashboard.html`)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AeroCure — Dispatch Dashboard</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #0f1729; color: #e2e8f0; }
        .header { background: #1e2d4a; padding: 16px 24px; display: flex; align-items: center; gap: 16px; border-bottom: 2px solid #e53e3e; }
        .header h1 { font-size: 1.5rem; color: #fff; }
        .header .badge { background: #e53e3e; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; }
        .stats { display: flex; gap: 16px; padding: 16px 24px; }
        .stat-card { background: #1e2d4a; border-radius: 8px; padding: 16px 24px; flex: 1; text-align: center; }
        .stat-card .number { font-size: 2rem; font-weight: bold; color: #e53e3e; }
        .stat-card .label { font-size: 0.8rem; color: #94a3b8; margin-top: 4px; }
        .main { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 0 24px 24px; }
        #map { height: 380px; border-radius: 8px; }
        .cases-panel { background: #1e2d4a; border-radius: 8px; overflow-y: auto; max-height: 380px; }
        .cases-panel h2 { padding: 16px; font-size: 1rem; border-bottom: 1px solid #2d3f5c; }
        .case-row { padding: 12px 16px; border-bottom: 1px solid #2d3f5c; cursor: pointer; }
        .case-row:hover { background: #2d3f5c; }
        .case-row .case-id { font-weight: bold; font-size: 0.9rem; }
        .case-row .case-meta { font-size: 0.78rem; color: #94a3b8; margin-top: 4px; }
        .status-badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: bold; }
        .RECEIVED { background: #744210; color: #fbd38d; }
        .DISPATCHED { background: #1a365d; color: #90cdf4; }
        .AIRBORNE { background: #1a4731; color: #9ae6b4; }
        .LANDED { background: #2d3748; color: #e2e8f0; }
        .COMPLETED { background: #276749; color: #c6f6d5; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚑 AeroCure Dispatch</h1>
        <span class="badge">{{ active_count }} ACTIVE</span>
    </div>

    <div class="stats">
        <div class="stat-card"><div class="number">{{ active_count }}</div><div class="label">Active Cases</div></div>
        <div class="stat-card"><div class="number">{{ total_count }}</div><div class="label">Total Cases</div></div>
        <div class="stat-card"><div class="number">~90</div><div class="label">Avg ETA (min)</div></div>
    </div>

    <div class="main">
        <div id="map"></div>
        <div class="cases-panel">
            <h2>Active Cases</h2>
            {% for case in cases %}
            <div class="case-row">
                <div class="case-id">{{ case.id }}
                    <span class="status-badge {{ case.status.value }}">{{ case.status.value }}</span>
                </div>
                <div class="case-meta">{{ case.condition_name }} | {{ case.airstrip_name }}</div>
                <div class="case-meta">{{ case.created_at }}</div>
            </div>
            {% endfor %}
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const map = L.map('map').setView([0.5, 37.5], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);

        // Airstrip markers (hardcoded for demo)
        const airstrips = [
            {name: "Lodwar (Turkana)", lat: 3.1219, lng: 35.6087},
            {name: "Marsabit", lat: 2.3383, lng: 37.9993},
            {name: "Isiolo", lat: 0.3382, lng: 37.5924},
            {name: "Nanyuki", lat: 0.0624, lng: 37.0410},
            {name: "Amboseli", lat: -2.6455, lng: 37.2531}
        ];

        airstrips.forEach(a => {
            L.circleMarker([a.lat, a.lng], {
                radius: 8, color: '#e53e3e', fillColor: '#e53e3e', fillOpacity: 0.8
            }).addTo(map).bindPopup(`✈️ ${a.name}`);
        });

        // Nairobi receiving hospital
        L.marker([-1.2921, 36.8219]).addTo(map)
            .bindPopup("🏥 Kenyatta National Hospital");
    </script>
</body>
</html>
```

### 📦 Phase 6 Deliverables
- [ ] `GET /` → renders dashboard HTML with real case data from DB
- [ ] `GET /api/cases` → returns JSON list of cases
- [ ] `POST /api/cases/{id}/update` → updates status + sends SMS
- [ ] Map shows all Kenyan airstrips as red markers
- [ ] Case list panel populates from database
- [ ] Status badges colour-coded by status

---

## ✅ PHASE 7 — WIRE EVERYTHING TOGETHER (Hours 54–58)
> Goal: One main.py that imports all routes and runs

### `main.py`
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import sms, ussd, voice, dashboard
from app.database import engine
from app.models import case, airstrip  # triggers table creation

# Create all tables on startup
case.Base.metadata.create_all(bind=engine)
airstrip.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AeroCure", version="1.0.0")

# Register all route groups
app.include_router(sms.router)
app.include_router(ussd.router)
app.include_router(voice.router)
app.include_router(dashboard.router)

@app.get("/health")
def health():
    return {"status": "AeroCure is running 🚑"}
```

Run locally:
```bash
uvicorn main:app --reload --port 8000
```

### 📦 Phase 7 Deliverables
- [ ] `uvicorn main:app --reload` starts without errors
- [ ] `http://localhost:8000/health` returns `{"status": "AeroCure is running 🚑"}`
- [ ] `http://localhost:8000/` shows dashboard with seeded cases
- [ ] ngrok tunnel is pointing to port 8000

---

## ✅ PHASE 8 — SEED DEMO DATA + FULL TESTING (Hours 58–64)
> Goal: Have 3 realistic walkthroughs ready for judges

### 3 Demo Scenarios To Seed and Walk Through

**Scenario A — Snakebite in Turkana**
```
SMS: "EVAC 4 TURKANA"
→ Case created: EVAC-2025-TK01
→ Voice call to dispatch plays snakebite + Turkana details
→ 4 SMS sent
→ Nurse dials *384*EVAC# → enters TK01 → sees RECEIVED status
→ Dispatcher on dashboard clicks DISPATCHED → ETA updated
→ Nurse gets SMS: "Aircraft dispatched. ETA 85 min"
```

**Scenario B — Obstetric Emergency, Isiolo**
```
SMS: "EVAC 2 ISIOLO"
→ Full notification chain fires
→ Dashboard shows AIRBORNE status
→ Hospital SMS: "Prepare OB team"
```

**Scenario C — Invalid SMS (error handling)**
```
SMS: "EVAC 9 NOWHERE"
→ Error SMS returned: "Invalid code. Codes: 1=Trauma..."
→ No case created
```

### Full End-to-End Test Checklist
```bash
# Test 1: Valid SMS
curl -X POST http://localhost:8000/sms/incoming \
  -d "from=%2B254700000001&text=EVAC+4+TURKANA"
# Expected: {"status":"case_created","case_id":"EVAC-..."}

# Test 2: Invalid SMS
curl -X POST http://localhost:8000/sms/incoming \
  -d "from=%2B254700000001&text=HELLO"
# Expected: error SMS sent

# Test 3: USSD
curl -X POST http://localhost:8000/ussd \
  -d "sessionId=abc&serviceCode=*384*EVAC%23&phoneNumber=%2B254700000001&text="
# Expected: CON welcome menu

# Test 4: Case status update
curl -X POST http://localhost:8000/api/cases/EVAC-2025-TK01/update \
  -d "status=DISPATCHED&notes=Aircraft airborne from Wilson"
# Expected: {"status":"updated",...}
```

### 📦 Phase 8 Deliverables
- [ ] 3 demo scenarios seeded and walkable
- [ ] All 4 test curl commands pass
- [ ] Dashboard reflects seeded cases correctly
- [ ] AT sandbox SMS simulator confirms messages delivered
- [ ] AT sandbox USSD simulator confirms menu flow works
- [ ] AT sandbox Voice simulator confirms call XML plays correctly

---

## ✅ PHASE 9 — DEPLOY + PITCH PREP (Hours 64–72)
> Goal: Live public URL, polished pitch, recorded demo

### Step 9.1 — Deploy to Railway
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables in Railway dashboard
# (copy from your .env file)

# Your public URL will be: https://aerocure-xxxx.railway.app
```

Update AT webhooks to the Railway URL:
- SMS: `https://aerocure-xxxx.railway.app/sms/incoming`
- USSD: `https://aerocure-xxxx.railway.app/ussd`
- Voice: `https://aerocure-xxxx.railway.app/voice/dispatch`

### Step 9.2 — Final Polish Checklist
- [ ] Dashboard loads in < 3 seconds on slow connection
- [ ] All SMS templates are in Swahili and English (add a `lang` query param)
- [ ] "Golden Hour Timer" shown on dashboard — time elapsed since case RECEIVED
- [ ] README.md explains: setup, `.env` config, seed, how to run
- [ ] GitHub repo is public with a clean commit history

### Step 9.3 — Your 5-Minute Pitch Structure

```
[0:00–0:45] — The Problem (Open with a story, not a slide)
"In 2023, a nurse in Marsabit had a patient with a ruptured appendix.
She spent 3 hours trying to reach AMREF by WhatsApp. The patient died
before the plane arrived. This happens every week across rural Kenya."

[0:45–1:30] — The Solution (One sentence)
"AeroCure lets any nurse trigger a full air evacuation coordination
chain with one SMS — no smartphone, no internet, no training required."

[1:30–3:30] — Live Demo (Most important part)
Show: Feature phone → EVAC SMS → dashboard updates → USSD status check

[3:30–4:15] — Market + Impact Numbers
"Kenya has 60+ rural airstrips. AMREF handles 4,500+ evacuations per year.
Every 30-minute reduction in coordination time is a life saved."

[4:15–5:00] — What's Next + Ask
"In 6 months: patient registry, nurse CHW enrollment via USSD,
integration with AMREF's dispatch system. We are looking for
pilot partners in Turkana and Marsabit County Health Departments."
```

### 📦 Phase 9 Deliverables
- [ ] App deployed and live at public Railway URL
- [ ] AT webhooks updated to production URL
- [ ] GitHub repo public with README
- [ ] 90-second demo video recorded (show phone + dashboard)
- [ ] 5-slide pitch deck (PDF): Problem → Solution → Demo → Numbers → Ask
- [ ] Project submitted before deadline

---

## 📊 Complete Deliverables Summary

| Phase | Hours | Key Deliverables |
|---|---|---|
| 0 — Setup | 0–3 | AT account, Supabase DB, ngrok, .env, packages |
| 1 — Database | 3–10 | Tables created, airstrip seed data loaded |
| 2 — AT Service Layer | 10–18 | send_sms, call_dispatch, send_airtime working |
| 3 — SMS Handler | 18–26 | EVAC parsed, case created, all 5 notifications fire |
| 4 — USSD Handler | 26–34 | Status check menu working in AT simulator |
| 5 — Voice Webhook | 34–38 | Dispatch call plays correct TTS details |
| 6 — Dashboard | 38–54 | Web UI with map, case list, status update |
| 7 — Integration | 54–58 | main.py runs all routes cleanly |
| 8 — Testing | 58–64 | 3 demo scenarios walkable end-to-end |
| 9 — Deploy + Pitch | 64–72 | Live URL, pitch deck, demo video, submitted |

---

## 🔗 All Resources in One Place

### Africa's Talking Docs
- [SMS API](https://developers.africastalking.com/docs/sms)
- [Voice API](https://developers.africastalking.com/docs/voice)
- [USSD API](https://developers.africastalking.com/docs/ussd)
- [Airtime API](https://developers.africastalking.com/docs/airtime)
- [Python SDK GitHub](https://github.com/AfricasTalkingLtd/africastalking-python)
- [AT Sandbox Simulator](https://simulator.africastalking.com/)

### Python & FastAPI
- [FastAPI Quickstart](https://fastapi.tiangolo.com/tutorial/)
- [SQLAlchemy ORM Docs](https://docs.sqlalchemy.org/en/20/orm/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/en/latest/)

### Infrastructure
- [Supabase — Free PostgreSQL](https://supabase.com/docs)
- [Railway — Deploy FastAPI](https://docs.railway.app/getting-started)
- [ngrok — Local Tunneling](https://ngrok.com/docs)

### Maps & Frontend
- [Leaflet.js Docs](https://leafletjs.com/reference.html)
- [OpenStreetMap Kenya Data](https://www.openstreetmap.org/)

### Domain Knowledge
- [AMREF Flying Doctors](https://flydoc.org/)
- [KCAA Airstrip Registry](https://www.kcaa.or.ke/)
- [WHO Emergency Triage Codes](https://www.who.int/emergencies/en/)
- [ICAO Annex 12 — Search & Rescue](https://www.icao.int/safety/search-and-rescue/pages/default.aspx)

### Testing
- [Postman — API Testing](https://www.postman.com/)
- [AT USSD Simulator](https://simulator.africastalking.com/ussd)

---

*AeroCure — Built for the Africa's Talking Transportation & Logistics Hackathon*
*One SMS. Five actions. Lives saved. 🚑✈️*


create full project from when a 

```markdown


The nurse types: `EVAC 4 TURKANA` and sends it to a shortcode number.

That single SMS automatically:
- Sends a text to the AMREF dispatch office with the emergency details
- Sends a text to the airstrip agent at Turkana airstrip
- Sends a text to the receiving hospital in Nairobi
- Sends a text to the patient's registered next of kin
- Sends the nurse a confirmation with a case ID and estimated aircraft arrival time based on longitude and latitude 
The nurse can then check updates anytime b
factor in real time distance to calculate the eta and distance based on different airport location coordinates i.e both lat and long assuming that my base of operation is wilson so starting pint is wilson airport -1.32172, 36.8148 and aircraft type is the cesna caravan.
The dispatcher has a computer screen (dashboard) showing all active cases, where aircraft are, and who has been contacted with a dashboard displaying real data.
for testing purposes let's use the console/userinput to get the nurse message and then, save it to the db sqlite for developement, interpret the message and return message back to the nurse then constantly update the dashboard based on the data from the db. where real data is not available use mock data use any of python fastapi / and htm, css with bootsrap css and js 
```

all the code should be stored in a single md file plus the readme and other project essentials. Any point that you need clarification before you start building don't hesitate to ask