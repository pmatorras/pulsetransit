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

# Initialize session state
if "clicked_stop_id" not in st.session_state:
    st.session_state.clicked_stop_id = None

# MOBILE DETECTION
try:
    from streamlit_js_eval import streamlit_js_eval
    screen_width = streamlit_js_eval(js_expressions='window.innerWidth', key='WIDTH')
    is_mobile = screen_width and screen_width < 768
except:
    is_mobile = False

# TABS: Browse vs Plan
tab_browse, tab_plan = st.tabs(["🚏 Browse", "📅 Plan"])

with tab_browse:
    # SEARCH ABOVE MAP
    stops["search_label"] = stops["stop_id"].astype(str) + " - " + stops["stop_name"]
    stop_options = [""] + stops["search_label"].tolist()
    st.info("👆 Click a stop on the map or use the search bar")

    selected_stop_label = st.selectbox(
        "Search stop",
        options=stop_options,
        index=None,
        placeholder="Type stop ID or name to search...",
        label_visibility='collapsed'
    )

    # Parse selected stop
    selected_stop_id = None
    if selected_stop_label:
        selected_stop_id = int(selected_stop_label.split(" - ")[0])

    # Determine active stop: search bar > map click
    if selected_stop_id:
        active_stop_id = selected_stop_id
        st.session_state.clicked_stop_id = None
    else:
        active_stop_id = st.session_state.clicked_stop_id

    # RESPONSIVE LAYOUT
    if is_mobile:
        # Mobile: Schedules FIRST, then map
        if active_stop_id:
            st.subheader("Scheduled Departures")
            stop_info = stops[stops["stop_id"] == active_stop_id].iloc[0]
            stop_name = stop_info["stop_name"]

            st.markdown(f"**{active_stop_id} - {stop_name}**")

            reference_dt = datetime.now()
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

        # -----------------------
        # Map schedules on mobile
        # -----------------------
        fig = build_map(
            stops=stops, 
            shapes=shapes, 
            trips=trips, 
            routes=routes,
            highlight_stop_id=active_stop_id
        )

        selected_point = st.plotly_chart(
            fig,
            width='stretch',
            on_select="rerun",
            selection_mode="points",
            key="transit_map",
        )

        # Process clicks
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

                if new_stop_id != st.session_state.clicked_stop_id:
                    st.session_state.clicked_stop_id = new_stop_id
                    st.rerun()

    else:
        # Desktop: Full-width map until stop is selected
        if active_stop_id:
            # Stop selected: 2-column layout
            col1, col2 = st.columns([2, 1])

            with col1:
                fig = build_map(
                    stops=stops, 
                    shapes=shapes, 
                    trips=trips, 
                    routes=routes,
                    highlight_stop_id=active_stop_id
                )

                selected_point = st.plotly_chart(
                    fig,
                    width='stretch',
                    on_select="rerun",
                    selection_mode="points",
                    key="transit_map",
                )

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

                        if new_stop_id != st.session_state.clicked_stop_id:
                            st.session_state.clicked_stop_id = new_stop_id
                            st.rerun()

            with col2:
                st.subheader("Scheduled Departures")

                stop_info = stops[stops["stop_id"] == active_stop_id].iloc[0]
                stop_name = stop_info["stop_name"]

                st.markdown(f"**{active_stop_id} - {stop_name}**")

                reference_dt = datetime.now()
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

            fig = build_map(
                stops=stops, 
                shapes=shapes, 
                trips=trips, 
                routes=routes,
                highlight_stop_id=None
            )

            selected_point = st.plotly_chart(
                fig,
                width='stretch',
                on_select="rerun",
                selection_mode="points",
                key="transit_map",
            )

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

                    if new_stop_id != st.session_state.clicked_stop_id:
                        st.session_state.clicked_stop_id = new_stop_id
                        st.rerun()

with tab_plan:
    st.subheader("Plan Your Trip")

    # Query time moved to Plan tab
    query_time = st.time_input(
        "Query time",
        value=datetime.now().time(),
        help="Show schedules for this time of day"
    )

    st.info("Trip planning features coming soon!")
