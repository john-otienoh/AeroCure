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
# import app.models                                    
from app.models.airports import Airstrip             
from seed.load_airports import load_airports_from_csv   

# DEFAULT_CSV = Path(__file__).parent / "airports.csv"
DEFAULT_CSV = "/home/outis/TechBoy/AeroCure/ke-airports.csv"


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


def verify() -> None:
    db = SessionLocal()
    try:
        total       = db.query(Airstrip).count()
        with_coords = db.query(Airstrip).filter(Airstrip.latitude.isnot(None)).count()
        sample      = db.query(Airstrip).limit(5).all()

        logger.info("─" * 58)
        logger.info("  Total airstrips : %d", total)
        logger.info("  With coordinates: %d", with_coords)
        logger.info("  Sample rows:")
        for s in sample:
            logger.info("    %-10s  %-40s  %s", s.iata_code, s.name, s.county or "—")
        logger.info("─" * 58)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="AeroCure Phase 1 seed")
    parser.add_argument(
        "--csv",
        default=str(DEFAULT_CSV),
        help=f"Path to airports CSV (default: {DEFAULT_CSV})",
    )
    args = parser.parse_args()

    logger.info("=" * 58)
    logger.info("AeroCure — Phase 1 Seed")
    logger.info("CSV: %s", args.csv)
    logger.info("=" * 58)

    create_tables()
    seed_airstrips(args.csv)
    verify()

    logger.info("Phase 1 seed complete")


if __name__ == "__main__":
    main()
