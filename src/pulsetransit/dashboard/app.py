import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

from pulsetransit.dashboard.map import (
    build_map,
    load_stops,
    load_shapes,
    load_trips,
    load_routes,
)
from pulsetransit.dashboard.schedules import get_next_departures

st.set_page_config(page_title="PulseTransit - Santander TUS", layout="wide")

# Load GTFS data
stops = load_stops()
shapes = load_shapes()
trips = load_trips()
routes = load_routes()

# Sidebar: Time selector + Stop search
st.sidebar.header("Settings")

query_time = st.sidebar.time_input(
    "Query time",
    value=datetime.now().time(),
    help="Show schedules for this time of day"
)

# Create searchable stop labels
stops["search_label"] = stops["stop_id"].astype(str) + " - " + stops["stop_name"]
stop_options = [""] + stops["search_label"].tolist()

selected_stop_label = st.sidebar.selectbox(
    "Search stop",
    options=stop_options,
    index=0,
    help="Type stop ID or name to search",
    placeholder="Type to search..."
)

# Parse selected stop
selected_stop_id = None
if selected_stop_label:
    selected_stop_id = int(selected_stop_label.split(" - ")[0])

# Initialize session state
if "clicked_stop_id" not in st.session_state:
    st.session_state.clicked_stop_id = None

# Determine active stop: search bar > map click
if selected_stop_id:
    active_stop_id = selected_stop_id
    st.session_state.clicked_stop_id = None  # Clear map click when searching
else:
    active_stop_id = st.session_state.clicked_stop_id

# Main layout: Map + Schedule panel
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Transit Network Map")
    
    # Build map with highlight
    fig = build_map(
        stops=stops, 
        shapes=shapes, 
        trips=trips, 
        routes=routes,
        highlight_stop_id=active_stop_id
    )
    
    # Capture click events
    selected_point = st.plotly_chart(
        fig,
        width='stretch',
        on_select="rerun",
        selection_mode="points",
        key="transit_map",
    )
    
    # Process new clicks immediately
    if selected_point and "selection" in selected_point:
        points = selected_point["selection"].get("points", [])
        if points:
            point = points[0]
            clicked_lat = point["lat"]
            clicked_lon = point["lon"]
            
            stops["dist"] = (
                (stops["stop_lat"] - clicked_lat) ** 2 +
                (stops["stop_lon"] - clicked_lon) ** 2
            )
            nearest_stop = stops.loc[stops["dist"].idxmin()]
            new_stop_id = int(nearest_stop["stop_id"])
            
            # Only update if it's a different stop
            if new_stop_id != st.session_state.clicked_stop_id:
                st.session_state.clicked_stop_id = new_stop_id
                st.rerun()  # Force immediate update

with col2:
    st.subheader("Scheduled Departures")
    
    if active_stop_id:
        stop_info = stops[stops["stop_id"] == active_stop_id].iloc[0]
        stop_name = stop_info["stop_name"]
        
        st.markdown(f"**{active_stop_id} - {stop_name}**")
        
        # Get departures
        reference_dt = datetime.combine(datetime.today(), query_time)
        departures = get_next_departures(active_stop_id, reference_dt, limit=10)
        
        if not departures.empty:
            departures["In"] = departures["minutes_until"].apply(
                lambda m: f"{m} min" if m > 0 else "Now"
            )
            display = departures[[
                "route_short_name",
                "trip_headsign",
                "departure_time",
                "In"
            ]]
            display.columns = ["Line", "Destination", "Time", "In"]
            
            st.dataframe(display, width='stretch', hide_index=True)
        else:
            st.info("No upcoming departures found for this stop.")
    else:
        st.info("👆 Click a stop on the map or use the search bar")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Data: TUS Santander GTFS • Updated: Feb 2026")
