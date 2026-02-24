import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

SANTANDER = dict(lat=43.4623, lon=-3.8099)
GTFS_DIR = Path("data/gtfs-static")

def load_stops() -> pd.DataFrame:
    return pd.read_csv(GTFS_DIR / "stops.txt")

def load_shapes() -> pd.DataFrame:
    return pd.read_csv(GTFS_DIR / "shapes.txt")

def load_routes() -> pd.DataFrame:
    return pd.read_csv(GTFS_DIR / "routes.txt")

def load_trips() -> pd.DataFrame:
    return pd.read_csv(GTFS_DIR / "trips.txt")

def _build_shape_colors(trips: pd.DataFrame, routes: pd.DataFrame) -> dict:
    """Map shape_id → (route_short_name, #rrggbb color)."""
    shape_route = trips[["shape_id", "route_id"]].drop_duplicates("shape_id")
    merged = shape_route.merge(
        routes[["route_id", "route_short_name", "route_color"]],
        on="route_id"
    )
    merged["color"] = merged["route_color"].apply(
        lambda c: f"#{c}" if pd.notna(c) and str(c).strip() else "#888888"
    )
    return merged.set_index("shape_id")[["route_short_name", "color"]].to_dict("index")

def _shapes_to_lines_colored(
    shapes: pd.DataFrame,
    shape_colors: dict,
) -> list[dict]:
    """One trace per route color group, with None separators within each."""
    color_groups: dict[str, dict] = {}
    for shape_id, group in shapes.groupby("shape_id", sort=False):
        info = shape_colors.get(shape_id, {"route_short_name": "?", "color": "#888888"})
        color = info["color"]
        name = info["route_short_name"]
        if color not in color_groups:
            color_groups[color] = {"name": f"Line {name}", "lats": [], "lons": []}
        pts = group.sort_values("shape_pt_sequence")
        color_groups[color]["lats"].extend(pts["shape_pt_lat"].tolist() + [None])
        color_groups[color]["lons"].extend(pts["shape_pt_lon"].tolist() + [None])
    return [{"color": c, **v} for c, v in color_groups.items()]

def _extract_arrow_points(shapes: pd.DataFrame, shape_colors: dict, interval: int = 15) -> list[dict]:
    """Extract evenly-spaced arrow markers along each shape."""
    arrows = []
    for shape_id, group in shapes.groupby("shape_id", sort=False):
        info = shape_colors.get(shape_id, {"route_short_name": "?", "color": "#888888"})
        pts = group.sort_values("shape_pt_sequence")
        
        # Sample every Nth point for arrows
        sampled = pts.iloc[::interval]
        if len(sampled) < 2:
            continue
        
        # Calculate bearing from current point to next point
        lats, lons, angles = [], [], []
        for i in range(len(sampled) - 1):
            lat1, lon1 = sampled.iloc[i][["shape_pt_lat", "shape_pt_lon"]]
            lat2, lon2 = sampled.iloc[i+1][["shape_pt_lat", "shape_pt_lon"]]
            
            # Simple angle calculation (good enough for small distances)
            import math
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            angle = math.degrees(math.atan2(dlon, dlat))
            
            lats.append(lat1)
            lons.append(lon1)
            angles.append(angle)
        
        arrows.append({
            "lats": lats,
            "lons": lons,
            "angles": angles,
            "color": info["color"],
            "name": info["route_short_name"],
        })
    return arrows

def build_map(
    stops: pd.DataFrame | None = None,
    shapes: pd.DataFrame | None = None,
    trips: pd.DataFrame | None = None,
    routes: pd.DataFrame | None = None,
) -> go.Figure:
    fig = go.Figure()

    if shapes is not None and trips is not None and routes is not None:
        shape_colors = _build_shape_colors(trips, routes)
        
        # Route lines
        for trace in _shapes_to_lines_colored(shapes, shape_colors):
            fig.add_trace(go.Scattermap(
                lat=trace["lats"],
                lon=trace["lons"],
                mode="lines",
                line=dict(width=3, color=trace["color"]),
                hoverinfo="skip",
                name=trace["name"],
                showlegend=True,
            ))
        
        # Direction arrows
        for arrow in _extract_arrow_points(shapes, shape_colors):
            fig.add_trace(go.Scattermap(
                lat=arrow["lats"],
                lon=arrow["lons"],
                mode="markers",
                marker=dict(
                    size=8,
                    color=arrow["color"],
                    symbol="arrow",
                    angle=arrow["angles"],
                ),
                hoverinfo="skip",
                showlegend=False,
            ))
    
    elif shapes is not None:
        # Fallback: no color info
        lats, lons = [], []
        for _, group in shapes.groupby("shape_id", sort=False):
            pts = group.sort_values("shape_pt_sequence")
            lats.extend(pts["shape_pt_lat"].tolist() + [None])
            lons.extend(pts["shape_pt_lon"].tolist() + [None])
        fig.add_trace(go.Scattermap(
            lat=lats, lon=lons, mode="lines",
            line=dict(width=3, color="#888888"),
            hoverinfo="skip", name="Routes",
        ))

    if stops is not None:
        # Dark border layer
        fig.add_trace(go.Scattermap(
            lat=stops["stop_lat"],
            lon=stops["stop_lon"],
            mode="markers",
            marker=dict(size=10, color="#333", opacity=0.8),
            hoverinfo="skip",
            showlegend=False,
        ))
        # Visible inner circle
        fig.add_trace(go.Scattermap(
            lat=stops["stop_lat"],
            lon=stops["stop_lon"],
            mode="markers",
            marker=dict(size=7, color="lightgray", opacity=1.0),
            text=stops["stop_name"],
            hovertemplate="<b>%{text}</b><br>(%{lat:.4f}, %{lon:.4f})<extra></extra>",
            name="Stops",
        ))


    fig.update_layout(
        map=dict(
            style="open-street-map",
            center=SANTANDER,
            zoom=13,
        ),
        legend=dict(bgcolor="rgba(255,255,255,0.8)", borderwidth=1),
        margin=dict(l=0, r=0, t=0, b=0),
        height=600,
    )
    return fig

if __name__ == "__main__":
    build_map(
        stops=load_stops(),
        shapes=load_shapes(),
        trips=load_trips(),
        routes=load_routes(),
    ).show()
