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
