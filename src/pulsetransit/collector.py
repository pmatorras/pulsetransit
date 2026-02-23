# collector.py
import urllib.request
import json
from datetime import datetime, timezone
from pulsetransit.db import get_connection, init_db


def fetch_json(dataset, rows=5000):
    url = f"http://datos.santander.es/api/rest/datasets/{dataset}.json?rows={rows}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read()).get("resources", [])

def collect_estimaciones(conn):
    collected_at = datetime.now(timezone.utc).isoformat()
    rows = fetch_json("control_flotas_estimaciones")
    inserted = 0
    for item in rows:
        fech_actual = item.get("ayto:fechActual")
        tiempo1 = item.get("ayto:tiempo1")
        # Compute predicted arrival = fechActual + tiempo1 seconds
        predicted_arrival = None
        if fech_actual and tiempo1 is not None:
            try:
                from datetime import timedelta
                t = datetime.fromisoformat(fech_actual.replace("Z", "+00:00"))
                predicted_arrival = (t + timedelta(seconds=int(tiempo1))).isoformat()
            except Exception:
                pass
        try:
            conn.execute("""
                INSERT OR IGNORE INTO estimaciones
                (collected_at, parada_id, linea, fech_actual, tiempo1, tiempo2,
                 distancia1, distancia2, destino1, destino2, predicted_arrival)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                collected_at,
                item.get("ayto:paradaId"),
                item.get("ayto:etiqLinea"),
                fech_actual,
                tiempo1,
                item.get("ayto:tiempo2"),
                item.get("ayto:distancia1"),
                item.get("ayto:distancia2"),
                item.get("ayto:destino1"),
                item.get("ayto:destino2"),
                predicted_arrival
            ))
            inserted += conn.execute("SELECT changes()").fetchone()[0]
        except Exception as e:
            print(f"  estimaciones insert error: {e}")
    conn.commit()
    print(f"[{collected_at}] estimaciones: {inserted} new rows from {len(rows)} fetched")

def collect_posiciones(conn):
    collected_at = datetime.now(timezone.utc).isoformat()
    rows = fetch_json("control_flotas_posiciones")
    inserted = 0
    for item in rows:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO posiciones
                (collected_at, instante, vehiculo, linea, lat, lon, velocidad, estado)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                collected_at,
                item.get("ayto:instante"),
                item.get("ayto:vehiculo"),
                item.get("ayto:linea"),
                item.get("wgs84_pos:lat"),
                item.get("wgs84_pos:long"),
                item.get("ayto:velocidad"),
                item.get("ayto:estado"),
            ))
            inserted += conn.execute("SELECT changes()").fetchone()[0]
        except Exception as e:
            print(f"  posiciones insert error: {e}")
    conn.commit()
    print(f"[{collected_at}] posiciones: {inserted} new rows from {len(rows)} fetched")

if __name__ == "__main__":
    import sys
    conn = get_connection()
    init_db(conn)
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    if mode in ("estimaciones", "both"):
        collect_estimaciones(conn)
    if mode in ("posiciones", "both"):
        collect_posiciones(conn)
    conn.close()
