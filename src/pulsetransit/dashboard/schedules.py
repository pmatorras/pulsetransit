import pandas as pd
from pathlib import Path
from datetime import datetime, time, timedelta

GTFS_DIR = Path("data/gtfs-static")

def load_stop_times() -> pd.DataFrame:
    return pd.read_csv(GTFS_DIR / "stop_times.txt")

def load_trips() -> pd.DataFrame:
    return pd.read_csv(GTFS_DIR / "trips.txt")

def load_routes() -> pd.DataFrame:
    return pd.read_csv(GTFS_DIR / "routes.txt")

def load_calendar_dates() -> pd.DataFrame:
    return pd.read_csv(GTFS_DIR / "calendar_dates.txt")


def _parse_gtfs_time(time_str: str) -> int:
    """Convert GTFS time string (HH:MM:SS, possibly >24h) to minutes since midnight."""
    h, m, s = map(int, time_str.split(":"))
    return h * 60 + m


def get_next_departures(
    stop_id: int,
    reference_datetime: datetime,
    limit: int = 10
) -> pd.DataFrame:
    """
    Get next N scheduled departures for a stop after reference_datetime.
    
    Returns DataFrame with columns:
    - route_short_name: Line number/name
    - trip_headsign: Destination
    - departure_time: Original GTFS time string
    - minutes_until: Minutes from now until departure
    """
    # Load data
    stop_times = load_stop_times()
    trips = load_trips()
    routes = load_routes()
    calendar = load_calendar_dates()
    
    # Filter by stop
    stop_schedule = stop_times[stop_times["stop_id"] == stop_id].copy()
    
    # Join to get route and service info
    stop_schedule = stop_schedule.merge(trips, on="trip_id")
    stop_schedule = stop_schedule.merge(
        routes[["route_id", "route_short_name", "route_color"]], 
        on="route_id"
    )
    
    # Filter by service active on reference date
    date_str = reference_datetime.strftime("%Y%m%d")
    active_services = calendar[
        (calendar["date"] == int(date_str)) & (calendar["exception_type"] == 1)
    ]["service_id"].unique()
    
    stop_schedule = stop_schedule[stop_schedule["service_id"].isin(active_services)]
    
    # Convert times to minutes since midnight
    stop_schedule["departure_minutes"] = stop_schedule["departure_time"].apply(_parse_gtfs_time)
    reference_minutes = reference_datetime.hour * 60 + reference_datetime.minute
    
    # Handle overnight times: if departure > 24h, it's for "tomorrow" in GTFS terms
    # but we're querying for "today", so skip those unless we're past midnight
    stop_schedule["minutes_until"] = stop_schedule["departure_minutes"] - reference_minutes
    
    # Filter future departures only
    upcoming = stop_schedule[stop_schedule["minutes_until"] >= 0].copy()
    
    # Sort and limit
    upcoming = upcoming.sort_values("minutes_until").head(limit)
    
    return upcoming[[
        "route_short_name", 
        "trip_headsign", 
        "departure_time",
        "minutes_until"
    ]]


if __name__ == "__main__":
    # Test with a real stop
    stop_times = load_stop_times()
    sample_stop = stop_times["stop_id"].iloc[0]
    
    print(f"Testing stop_id: {sample_stop}")
    
    # Test at 10:00 AM today
    test_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    
    departures = get_next_departures(sample_stop, test_time, limit=5)
    print(f"\nNext 5 departures from stop {sample_stop} after {test_time.strftime('%H:%M')}:")
    print(departures.to_string(index=False))
