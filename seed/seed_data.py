import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)-8s]  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("seed")

from app.database import Base, engine, SessionLocal
import app.models
from app.models.airports import Airstrip
from app.models.condition import Condition
from app.models.hospital import Hospital
from app.models.ops import Operator, OperatorRole
from seed.load_airports import load_airports_from_csv

DEFAULT_CSV = "/home/outis/TechBoy/AeroCure/ke-airports.csv"
# DEFAULT_CSV = Path(__file__).parent / "ke-airports.csv"

CONDITIONS = [
    Condition(code="TR", name="Trauma / Injury",       priority=1, is_active=True,
              description="Physical trauma, road accident, falls, burns."),
    Condition(code="CA", name="Cardiac Emergency",     priority=1, is_active=True,
              description="Suspected MI, cardiac arrest, severe arrhythmia."),
    Condition(code="OB", name="Obstetric Emergency",   priority=1, is_active=True,
              description="Complicated labour, eclampsia, postpartum haemorrhage."),
    Condition(code="RE", name="Respiratory Distress",  priority=2, is_active=True,
              description="Severe asthma, pneumonia, hypoxia."),
    Condition(code="OT", name="Other Critical",        priority=3, is_active=True,
              description="Any other life-threatening condition not listed above."),
]

HOSPITALS = [
    Hospital(name="Kenyatta National Hospital",           phone="+254722000010",
             county="Nairobi County",    latitude=-1.3005, longitude=36.8075,
             is_default=True,  is_active=True),
    Hospital(name="Moi Teaching & Referral Hospital",     phone="+254722000011",
             county="Uasin Gishu County",latitude=0.5082,  longitude=35.2697,
             is_default=False, is_active=True),
    Hospital(name="Coast General Teaching & Referral",    phone="+254722000012",
             county="Mombasa County",    latitude=-4.0526, longitude=39.6639,
             is_default=False, is_active=True),
]

OPERATORS = [
    Operator(username="admin", full_name="AeroCure Admin",
             password_hash="$2b$12$REPLACE_WITH_REAL_BCRYPT_HASH",
             role=OperatorRole.ADMIN, is_active=True),
]

def _upsert(db, model, rows: list, pk_field: str = "code") -> int:
    """
    Idempotent upsert for small reference tables:
    skip rows whose PK already exists, insert the rest.
    """
    existing_pks = {getattr(r, pk_field) for r in db.query(model).all()}
    new_rows = [r for r in rows if getattr(r, pk_field) not in existing_pks]
    if new_rows:
        db.bulk_save_objects(new_rows)
        db.commit()
    return len(new_rows)

def create_tables() -> None:
    logger.info("Creating database tables (if not exist)…")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables ready")


def seed_airstrips(csv_path: str) -> None:
    airstrips = load_airports_from_csv(csv_path)

    if not airstrips:
        logger.error("No airstrips loaded — check CSV path")
        sys.exit(1)

    db = SessionLocal()
    try:
        existing = db.query(Airstrip).count()
        if existing:
            logger.info("Clearing %d existing airstrip rows…", existing)
            db.query(Airstrip).delete(synchronize_session=False)
            db.commit()

        db.bulk_save_objects(airstrips)
        db.commit()
        logger.info("Inserted %d airstrips", db.query(Airstrip).count())

    except Exception:
        db.rollback()
        logger.exception("Seed failed — transaction rolled back")
        raise
    finally:
        db.close()

def seed_reference_data() -> None:
    db = SessionLocal()
    try:
        inserted = _upsert(db, Condition, CONDITIONS, pk_field="code")
        logger.info("Conditions: %d new rows (skipped existing)", inserted)

        inserted = _upsert(db, Hospital, HOSPITALS, pk_field="name")
        logger.info("Hospitals:  %d new rows (skipped existing)", inserted)

        inserted = _upsert(db, Operator, OPERATORS, pk_field="username")
        logger.info("Operators:  %d new rows (skipped existing)", inserted)
    except Exception:
        db.rollback()
        logger.exception("Reference seed failed — rolled back")
        raise
    finally:
        db.close()

def verify() -> None:
    db = SessionLocal()
    try:
        total       = db.query(Airstrip).count()
        with_coords = db.query(Airstrip).filter(Airstrip.latitude.isnot(None)).count()
        sample      = db.query(Airstrip).limit(5).all()

        logger.info("─" * 58)
        logger.info("  Airstrips total     : %d", total)
        logger.info("  With coordinates    : %d", with_coords)
        logger.info("  Conditions          : %d", db.query(Condition).count())
        logger.info("  Hospitals           : %d", db.query(Hospital).count())
        logger.info("  Operators           : %d", db.query(Operator).count())
        logger.info("  Sample airstrips:")
        for s in sample:
            logger.info(
                "    %-10s  %-6s  %-40s  %s",
                s.icao_code, s.iata_code or "—", s.name, s.county or "—",
            )
        logger.info("─" * 58)
    finally:
        db.close()

def main() -> None:
    parser = argparse.ArgumentParser(description="AeroCure Phase 1 seed")
    parser.add_argument("--csv", default=str(DEFAULT_CSV),
                        help="Path to Kenya airports CSV")
    parser.add_argument("--skip-airports", action="store_true",
                        help="Skip CSV reload (re-seed reference tables only)")
    args = parser.parse_args()

    logger.info("=" * 58)
    logger.info("AeroCure — Phase 1 Seed")
    logger.info("=" * 58)

    create_tables()

    if not args.skip_airports:
        seed_airstrips(args.csv)

    seed_reference_data()
    verify()

    logger.info("Phase 1 seed complete")


if __name__ == "__main__":
    main()
