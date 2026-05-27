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
