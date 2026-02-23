import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "tus.db"
MAX_AGE_HOURS = 2  # fail if no data collected in last 2 hours

def check_table(conn, table, time_col):
    row = conn.execute(f"SELECT COUNT(*), MAX({time_col}) FROM {table}").fetchone()
    count, latest = row[0], row[1]
    if not latest:
        print(f"  FAIL — {table}: no data at all")
        return False
    # Normalise timestamp
    latest_dt = datetime.fromisoformat(latest.replace("Z", "+00:00"))
    age = datetime.now(timezone.utc) - latest_dt
    ok = age < timedelta(hours=MAX_AGE_HOURS)
    status = "OK" if ok else "FAIL"
    print(f"  {status} — {table}: {count} rows, latest {latest_dt.strftime('%H:%M UTC')} ({age.seconds//60} min ago)")
    return ok

conn = sqlite3.connect(DB_PATH)
print(f"Validating at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
results = [
    check_table(conn, "estimaciones", "collected_at"),
    check_table(conn, "posiciones",   "instante"),
]
conn.close()

if not all(results):
    print("Validation FAILED")
    sys.exit(1)

print("Validation PASSED")
