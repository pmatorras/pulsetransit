# PulseTransit
![Worker Status](https://github.com/pmatorras/pulsetransit/actions/workflows/monitor.yml/badge.svg)

![Collector](https://github.com/pmatorras/pulsetransit/actions/workflows/collect.yml/badge.svg)

Real-time data pipeline for TUS (Transportes Urbanos de Santander) bus network.
Collects live vehicle positions and stop-level ETA predictions to build a 
historical dataset for delay analysis and ML-based prediction.

## Data Sources

| Endpoint | Dataset | Collection Frequency | API Behavior |
|---|---|---|---|
| `control_flotas_estimaciones` | ETA predictions per stop | Every 2 min | Returns current predictions for all stops (~450 stops, ~940 predictions) |
| `control_flotas_posiciones` | GPS breadcrumbs per vehicle | Every 60 min | Returns cumulative route history for all active vehicles (breadcrumbs every 25s since route start) |

Source: [datos.santander.es](http://datos.santander.es)

## Architecture

**Data Collection:**
- **Cloudflare Worker** (`pulsetransit-worker/`): Scheduled collection every 2 minutes (estimaciones) and hourly (posiciones), storing in Cloudflare D1 database
- **GitHub Actions (Legacy)** (`.github/workflows/collect.yml`): Legacy collector, writes to `data/tus.db` for development/testing

**Database Schema:**
- `estimaciones`: Predictions with `UNIQUE(parada_id, linea, fech_actual)` to deduplicate
- `posiciones`: GPS breadcrumbs with `UNIQUE(vehiculo, instante)` to deduplicate overlapping route histories

## Project Structure

```
src/pulsetransit/ # Legacy Python collector (backup/testing)
├── collector.py # API fetching and DB insertion
└── db.py # Schema and connection management

pulsetransit-worker/ # Cloudflare Worker (production collector)
├── src/index.js # Scheduled tasks, API fetching, health endpoint
├── schema.sql # D1 database schema
└── wrangler.jsonc # Cloudflare config and cron triggers

.github/workflows/
├── collect.yml # Manual backup collector
└── monitor.yml # Hourly worker health check

data/
└── tus.db # SQLite database (GitHub Actions/local dev)
```


## Roadmap

- [x] Data collection pipeline (GPS + ETA)
- [ ] GTFS static feed integration (stop geometries, scheduled timetables)
- [ ] Delay computation (predicted vs actual arrival)
- [ ] Weather feature enrichment (via meteomat)
- [ ] ML delay prediction model
- [ ] Live dashboard

## Setup

```bash
pip install -e .
python src/pulsetransit/collector.py both
```