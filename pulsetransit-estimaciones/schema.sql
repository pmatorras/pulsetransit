CREATE TABLE IF NOT EXISTS estimaciones (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  collected_at TEXT NOT NULL,
  parada_id   INTEGER,
  linea       TEXT,
  fech_actual TEXT,
  tiempo1     INTEGER,
  tiempo2     INTEGER,
  distancia1  INTEGER,
  distancia2  INTEGER,
  destino1    TEXT,
  destino2    TEXT,
  predicted_arrival TEXT,
  UNIQUE(parada_id, linea, fech_actual)
);

CREATE INDEX IF NOT EXISTS idx_est_parada  ON estimaciones(parada_id);
CREATE INDEX IF NOT EXISTS idx_est_linea   ON estimaciones(linea);
CREATE INDEX IF NOT EXISTS idx_est_arrival ON estimaciones(predicted_arrival);
