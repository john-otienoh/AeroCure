import csv
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.airports import Airstrip

logger = logging.getLogger(__name__)

EXCLUDED_TYPES = {"heliport", "closed", "balloonport"}


def _to_float(value):
    if not value:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _to_int(value):
    if not value:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _to_bool(value):
    """Convert '1'/'0' or empty to True/False/None."""
    if not value:
        return None
    return value.strip() == "1"


def load_airports_from_csv(csv_path: str):
    """
    Parse the local OurAirports CSV and return a list of Airstrip ORM
    instances for operational Kenyan airports, with **all** CSV columns
    mapped to the model fields.
    """
    airstrips = []
    skipped = 0

    with open(csv_path, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)

        for row in reader:
            airport_type = row.get("type", "").strip().lower()
            if airport_type in EXCLUDED_TYPES:
                skipped += 1
                continue

            icao = (row.get("icao_code") or row.get("ident") or "").strip()
            name = (row.get("name") or "").strip()
            if not icao or not name:
                logger.warning("Skipping row - missing icao_code or name: %s", row)
                skipped += 1
                continue

            airstrip = Airstrip(
                icao_code=icao,
                iata_code=(row.get("iata_code") or "").strip() or None,
                name=name,
                airport_type=airport_type,
                city=(row.get("municipality") or "").strip() or None,
                county=(row.get("region_name") or "").strip() or None,
                county_code=(row.get("local_region") or "").strip() or None,
                latitude=_to_float(row.get("latitude_deg")),
                longitude=_to_float(row.get("longitude_deg")),
                elevation_ft=_to_int(row.get("elevation_ft")),
                scheduled_service=_to_bool(row.get("scheduled_service")),
                agent_phone=None,   
            )
            airstrips.append(airstrip)

    logger.info("Loaded %d operational airstrips (skipped %d)", len(airstrips), skipped)
    return airstrips
