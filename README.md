# PulseTransit
![Santander TUS Worker](https://github.com/pmatorras/pulsetransit/actions/workflows/monitor.yml/badge.svg)


Real-time data pipeline for TUS (Transportes Urbanos de Santander) bus network.
Collects live vehicle positions and stop-level ETA predictions to build a 
historical dataset for delay analysis and ML-based prediction.

## Data Sources

### Real-time Data (datos.santander.es API)

- **`posiciones`**: GPS positions of buses (lat/lon, timestamp, line, vehicle ID)
- **`estimaciones_parada`**: Real-time ETAs for each bus-stop pair
- ~~**`pasos_parada`**: Historical passages (stale since June 2025, not used)~~

### Static Data (NAP - National Access Point)

GTFS static files from [nap.transportes.gob.es](https://nap.transportes.gob.es/Files/Detail/1391):

- **`stops.txt`**: Stop coordinates and metadata (for proximity calculation)
- **`shapes.txt`**: Detailed route geometries (for GPS map-matching and visualization)
- **`routes.txt`**: Route names, colors, and metadata
- **`trips.txt`**: Trip patterns and service IDs
- **`stop_times.txt`**: Stop sequences and route structure
- **`calendar_dates.txt`**: Service exceptions (holidays, special schedules)

**Note**: GTFS files are stored in `data/gtfs-static/` (not tracked in git due to size).


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
