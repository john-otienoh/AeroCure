"""
AeroCure FastAPI application.

Routes:
  GET  /                         → dashboard HTML
  POST /api/inbound-sms          → receive simulated nurse SMS
  GET  /api/cases                → list all cases (JSON)
  GET  /api/cases/{id}           → single case detail
  POST /api/cases/{id}/update    → dispatcher status update
  GET  /api/airstrips            → all airstrips with coordinates
  GET  /api/notifications/{id}   → notifications for a case
  GET  /api/stats                → dashboard summary stats
"""

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

import airstrip_data as AD
from case_service import process_inbound_sms, update_case_status
from database import get_db, init_db
from models import Case, CaseStatus, Notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)-8s]  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("aerocure")


# ── App lifecycle ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("✅  AeroCure started — DB initialised")
    logger.info("    Dashboard → http://localhost:8000")
    logger.info("    SMS test  → python nurse_console.py")
    yield


app = FastAPI(
    title="AeroCure",
    description="Emergency Air Medical Evacuation Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# templates = Jinja2Templates(directory="templates")
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    with open("templates/index.html") as f:
        return f.read()

# ── Dashboard ─────────────────────────────────────────────────────────────────

# @app.get("/", response_class=HTMLResponse)
# async def dashboard(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})


# ── Inbound SMS ───────────────────────────────────────────────────────────────

class InboundSMSRequest(BaseModel):
    message: str
    phone: str = "+254700000000"   # sender's phone number


@app.post("/api/inbound-sms")
async def inbound_sms(payload: InboundSMSRequest, db: Session = Depends(get_db)):
    """
    Simulates receiving a nurse SMS.
    In production, Africa's Talking calls this webhook directly.
    """
    result = process_inbound_sms(payload.message, payload.phone, db)
    if not result.success:
        return JSONResponse(status_code=400, content={
            "success": False,
            "error":   result.error,
            "message": result.nurse_message,
        })
    return {
        "success":      True,
        "case_id":      result.case_id,
        "confirmation": result.nurse_message,
    }


# ── Cases ─────────────────────────────────────────────────────────────────────

@app.get("/api/cases")
async def list_cases(
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(Case).order_by(Case.created_at.desc())
    if status:
        q = q.filter(Case.status == status)
    return [c.to_dict() for c in q.limit(limit).all()]


@app.get("/api/cases/{case_id}")
async def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(404, detail=f"Case {case_id} not found")
    return case.to_dict()


class UpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = ""
    changed_by: str = "DASHBOARD"


@app.post("/api/cases/{case_id}/update")
async def update_case(
    case_id: str,
    body: UpdateRequest,
    db: Session = Depends(get_db),
):
    try:
        case = update_case_status(case_id, body.status, body.notes or "",
                                  body.changed_by, db)
        return case.to_dict()
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


# ── Airstrips ─────────────────────────────────────────────────────────────────

@app.get("/api/airstrips")
async def list_airstrips():
    return [
        {
            "code":    a.code,
            "name":    a.name,
            "county":  a.county,
            "lat":     a.lat,
            "lng":     a.lng,
            "has_agent": a.agent_phone is not None,
        }
        for a in AD.all_airstrips()
    ]


# ── Notifications ─────────────────────────────────────────────────────────────

@app.get("/api/notifications/{case_id}")
async def get_notifications(case_id: str, db: Session = Depends(get_db)):
    notifs = (db.query(Notification)
              .filter(Notification.case_id == case_id)
              .order_by(Notification.sent_at.asc())
              .all())
    return [n.to_dict() for n in notifs]


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    cases = db.query(Case).all()
    by_status = {}
    for s in CaseStatus:
        by_status[s.value] = sum(1 for c in cases
                                 if (c.status.value if isinstance(c.status, CaseStatus)
                                     else c.status) == s.value)
    active = sum(1 for c in cases
                 if (c.status.value if isinstance(c.status, CaseStatus)
                     else c.status) not in ("COMPLETED", "CANCELLED"))
    active_with_eta = [c for c in cases
                       if c.eta_minutes and (c.status.value if isinstance(c.status, CaseStatus)
                                             else c.status) not in ("COMPLETED", "CANCELLED")]
    avg_eta = (int(sum(c.eta_minutes for c in active_with_eta) / len(active_with_eta))
               if active_with_eta else None)
    return {
        "total":    len(cases),
        "active":   active,
        "avg_eta":  avg_eta,
        "by_status": by_status,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
