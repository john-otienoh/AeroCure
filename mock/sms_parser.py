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
