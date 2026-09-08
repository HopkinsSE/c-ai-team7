import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import requests

dash.register_page(__name__, path="/page2", name="[PAGE NAME HERE]")

layout = html.Div([
    html.H2("PAGE 2", className="page-title"),
    html.P("[ENTER A DESCRIPTION OF WHAT IS ON PAGE 2 HERE].",
           className="page-subtitle")
], className="page1-wrap"
)

import dash
from dash import html, dcc, callback, Input, Output
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

dash.register_page(__name__, path="/page2", name="Team Trends Over Time")

# ---- Load data (same pattern as page1) ----
THIS_DIR = Path(__file__).resolve().parent

def _find_csv(filename):
    candidates = [THIS_DIR / filename, THIS_DIR.parent / filename]
    return next((p for p in candidates if p.exists()), candidates[0])

team_meta = pd.read_csv(_find_csv("team_meta.csv"))
team_stats = pd.read_csv(_find_csv("team_stats_2021_2026.csv"))

# Merge in TEAM_NAME (or any display-friendly columns) from team_meta,
# same approach as page1 — only bring in columns not already present
meta_cols_to_add = [
    c for c in team_meta.columns
    if c == "TEAM_ABBREVIATION" or c not in team_stats.columns
]
team_stats = team_stats.merge(
    team_meta[meta_cols_to_add],
    on="TEAM_ABBREVIATION",
    how="left",
)

# ---- Sorted season list, used to make sure the line chart's x-axis
#      is chronological rather than alphabetical/string-sorted ----
season_list = sorted(team_stats["SEASON"].unique())

METRIC_OPTIONS = {
    "NET_RATING": ("Net Rating", False),
    "OFF_RATING": ("Offensive Rating", False),
    "DEF_RATING": ("Defensive Rating", False),
    "EFG_PCT": ("Effective FG %", True),
    "PACE": ("Pace", False),
}

metric_dropdown_options = [
    {"label": label, "value": col}
    for col, (label, _) in METRIC_OPTIONS.items()
    if col in team_stats.columns
]
default_metric = metric_dropdown_options[0]["value"] if metric_dropdown_options else None

# ---- Build dropdown options from team metadata ----
team_lookup = team_stats.drop_duplicates(subset="TEAM_ID")[
    ["TEAM_ID", "TEAM_NAME"]
]

team_dropdown_options = [
    {"label": row["TEAM_NAME"], "value": row["TEAM_ID"]}
    for _, row in team_lookup.iterrows()
]
# Default selection — first team alphabetically by label, just so the
# page never loads with an empty graph
default_team_id = sorted(
    team_dropdown_options, key=lambda opt: opt["label"]
)[0]["value"]

box_style = {
    "margin": "25px auto",
    "padding": "25px",
    "border": "2px solid black",
    "max-width": "1500px",
    "width": "90%",
    "backgroundColor": "#ffa826c1",
    "borderRadius": "4px",
}

layout = html.Div([
    html.H2("Team Trends Over Time"),
    html.P("Track a single team's win percentage across seasons to spot rebuilds, "
           "sustained success, or decline."),
        html.Div([
        html.Div([
            html.Label("Select Team", htmlFor="team-dropdown"),
            dcc.Dropdown(
                id="team-dropdown",
                options=team_dropdown_options,
                value=default_team_id,
                clearable=False,
            ),
        ], style={"flex": "1", "minWidth": "250px", "margin": "10px"}),
        html.Div([
            html.Label("Compare Win % Against", htmlFor="metric-dropdown"),
            dcc.Dropdown(
                id="metric-dropdown",
                options=metric_dropdown_options,
                value=default_metric,
                clearable=False,
            ),
        ], style={"flex": "1", "minWidth": "250px", "margin": "10px"}),
    ], style={"display": "flex", "flexWrap": "wrap"}),
    dcc.Graph(id="team-trend-line", style={"height":"600px"}),
], style=box_style)

@callback(
    Output("team-trend-line", "figure"),
    Input("team-dropdown", "value"),
    Input("metric-dropdown", "value"),
)
def update_team_trend(selected_team_id, selected_metric):
    #filter to just the selected team
    filtered = team_stats[team_stats["TEAM_ID"]==selected_team_id]
    
    if filtered.empty:
        fig = go.Figure()
        fig.update_layout(title="No data available for this team")
        return fig
    
    filtered = filtered.sort_values("SEASON")
    
    team_label = filtered["TEAM_NAME"].iloc[0] if "TEAM_NAME" in filtered.columns \
        else filtered["TEAM_ABBREVIATION"].iloc[0]
        
    metric_valid = selected_metric in filtered.columns
    metric_label, metric_is_pct = METRIC_OPTIONS.get(selected_metric, (selected_metric, False))

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=filtered["SEASON"],
            y=filtered["WIN_PCT"],
            name="Win %",
            mode="lines+markers",
            line=dict(color="#1f77b4"),
            hovertemplate="Season %{x}<br>Win %%: %{y:.1%}<extra></extra>",
        ),
        secondary_y=False,
    )

    if metric_valid:
        hover_fmt = "%{y:.1%}" if metric_is_pct else "%{y:.1f}"
        fig.add_trace(
            go.Scatter(
                x=filtered["SEASON"],
                y=filtered[selected_metric],
                name=metric_label,
                mode="lines+markers",
                line=dict(color="#d62728"),
                hovertemplate=f"Season %{{x}}<br>{metric_label}: {hover_fmt}<extra></extra>",
            ),
            secondary_y=True,
        )
        right_axis_kwargs = dict(
            title_text=metric_label,
            tickformat=".0%" if metric_is_pct else None,
        )
    else:
        right_axis_kwargs = dict(title_text="")

    fig.update_yaxes(title_text="Win %", tickformat=".0%", range=[0, 1], secondary_y=False)
    fig.update_yaxes(secondary_y=True, **right_axis_kwargs)
    fig.update_xaxes(title_text="Season")
    fig.update_layout(
        title=f"{team_label} — Win % vs {metric_label if metric_valid else 'Metric'} by Season",
        margin=dict(t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    return fig