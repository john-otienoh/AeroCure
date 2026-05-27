
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
