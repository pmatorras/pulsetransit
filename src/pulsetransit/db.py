# src/pulsetransit/db.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "tus.db"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS estimaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collected_at TEXT NOT NULL,
            parada_id INTEGER,
            linea TEXT,
            fech_actual TEXT,
            tiempo1 INTEGER,
            tiempo2 INTEGER,
            distancia1 INTEGER,
            distancia2 INTEGER,
            destino1 TEXT,
            destino2 TEXT,
            predicted_arrival TEXT,
            UNIQUE(parada_id, linea, fech_actual)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posiciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collected_at TEXT NOT NULL,
            instante TEXT NOT NULL,
            vehiculo INTEGER,
            linea INTEGER,
            lat REAL,
            lon REAL,
            velocidad INTEGER,
            estado INTEGER,
            UNIQUE(vehiculo, instante)
        )
    """)
    conn.commit()
