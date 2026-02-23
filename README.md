# PulseTransit

![Collector](https://github.com/pmatorras/pulsetransit/actions/workflows/collect.yml/badge.svg)
![Validate](https://github.com/pmatorras/pulsetransit/actions/workflows/validate.yml/badge.svg)


Real-time data pipeline for TUS (Transportes Urbanos de Santander) bus network.
Collects live vehicle positions and stop-level ETA predictions to build a 
historical dataset for delay analysis and ML-based prediction.

## Data Sources

| Endpoint | Dataset | Frequency |
|---|---|---|
| `control_flotas_estimaciones` | ETA predictions per stop | Every 5 min |
| `control_flotas_posiciones` | GPS breadcrumbs per vehicle | Every 20 min |

Source: [datos.santander.es](http://datos.santander.es)

## Project Structure

```
src/pulsetransit/
├── collector.py # API fetching + DB insertion
└── db.py # Schema and connection management
.github/workflows/
└── collect.yml # GitHub Actions scheduled collection
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
