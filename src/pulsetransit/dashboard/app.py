# -*- coding: utf-8 -*-
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
from pulsetransit.cfg.config import LANG

def render_interactive_map(stops, shapes, trips, routes, highlight_stop_id=None, lang_code='es'):
    """Render map and handle click interactions"""
    fig = build_map(
        stops=stops, 
        shapes=shapes, 
        trips=trips, 
        routes=routes,
        highlight_stop_id=highlight_stop_id,
        lang_code=lang_code
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

def display_stop_schedule(active_stop_id, stops, t):
    """Display schedule for a given stop"""
    st.subheader(t["scheduled_departures"])
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
        display.columns = [t["line"], t["destination"], t["time"], t["in"]]

        st.dataframe(display, width='stretch', hide_index=True)
    else:
        st.info("No upcoming departures found for this stop.")

# Get language from query params
query_params = st.query_params
default_lang = query_params.get("lang", "es")  # Default to Spanish
if default_lang not in ["en", "es"]:
    default_lang = "es"

#Page config and language selector
st.set_page_config(page_title="PulseTransit - Santander TUS", layout="wide", page_icon="🚌")

# Language selector in header (Meteomat style)
col1, col2 = st.columns([6, 1])
with col2:
    default_idx = 0 if default_lang == "en" else 1
    lang = st.selectbox("🌐", ["🇬🇧 EN", "🇪🇸 ES"], index=default_idx, label_visibility="collapsed", key="lang_selector")
    lang_code = "en" if "EN" in lang else "es"

    # Update URL when language changes
    if lang_code != default_lang:
        st.query_params["lang"] = lang_code

# Get translations for current language
t = LANG[lang_code]

with col1:
    st.title(f"🚌 {t['title']}")
    st.markdown(f"**{t['subtitle']}** · Santander, España")

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
tab_browse, tab_plan = st.tabs([f"📅 {t["browse_tab"]}", f"🚏 {t["plan_tab"]}"])

with tab_browse:
    # SEARCH ABOVE MAP
    stops["search_label"] = stops["stop_id"].astype(str) + " - " + stops["stop_name"]
    stop_options = [""] + stops["search_label"].tolist()
    st.info(f"👆 {t["click_info"]}")

    selected_stop_label = st.selectbox(
        t["search_stop"],
        options=stop_options,
        index=None,
        placeholder=t["search_placeholder"],
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
        if active_stop_id: display_stop_schedule(active_stop_id, stops, t)

        # Map schedules on mobile
        render_interactive_map(stops, shapes, trips, routes, highlight_stop_id=active_stop_id, lang_code=lang_code)

    else:
        # Desktop: Full-width map until stop is selected
        if active_stop_id:
            # Stop selected: 2-column layout
            col1, col2 = st.columns([2, 1])

            with col1:
                render_interactive_map(stops, shapes, trips, routes, highlight_stop_id=active_stop_id, lang_code=lang_code)

            with col2:
                display_stop_schedule(active_stop_id, stops, t)

        else:
            render_interactive_map(stops, shapes, trips, routes, highlight_stop_id=None , lang_code=lang_code)

with tab_plan:
    st.subheader(t["plan_trip"])

    # Query time
    query_time = st.time_input(
        t["query_time"],
        value=datetime.now().time(),
        help="Show schedules for this time of day"
    )

    st.info(t["coming_soon"])
