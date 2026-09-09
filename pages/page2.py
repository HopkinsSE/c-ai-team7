import dash
from dash import html, dcc, callback, Input, Output, ALL, MATCH, ctx, State
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import plotly.express as px

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

DIVISION_MAP = {
    "ATL": "Southeast", "BOS": "Atlantic", "BKN": "Atlantic", "CHA": "Southeast",
    "CHI": "Central", "CLE": "Central", "DAL": "Southwest", "DEN": "Northwest",
    "DET": "Central", "GSW": "Pacific", "HOU": "Southwest", "IND": "Central",
    "LAC": "Pacific", "LAL": "Pacific", "MEM": "Southwest", "MIA": "Southeast",
    "MIL": "Central", "MIN": "Northwest", "NOP": "Southwest", "NYK": "Atlantic",
    "OKC": "Northwest", "ORL": "Southeast", "PHI": "Atlantic", "PHX": "Pacific",
    "POR": "Northwest", "SAC": "Pacific", "SAS": "Southwest", "TOR": "Atlantic",
    "UTA": "Northwest", "WAS": "Southeast",
}
DIVISION_ORDER = {
    "Atlantic": 1, "Central": 2, "Southeast": 3,
    "Northwest": 4, "Pacific": 5, "Southwest": 6,
}

MAX_TEAMS = 5
TEAM_COLORS = px.colors.qualitative.Safe  # colorblind-safe palette

metric_dropdown_options = [
    {"label": label, "value": col}
    for col, (label, _) in METRIC_OPTIONS.items()
    if col in team_stats.columns
]
default_metric = metric_dropdown_options[0]["value"] if metric_dropdown_options else None

team_lookup = team_stats.drop_duplicates(subset="TEAM_ID")[
    ["TEAM_ID", "TEAM_NAME", "TEAM_ABBREVIATION"]
].copy()
team_lookup["DIVISION"] = team_lookup["TEAM_ABBREVIATION"].map(DIVISION_MAP)

_missing = team_lookup[team_lookup["DIVISION"].isna()]
if not _missing.empty:
    print("Warning: no division match for:", _missing["TEAM_ABBREVIATION"].tolist())

division_order_sorted = sorted(
    team_lookup["DIVISION"].dropna().unique(),
    key=lambda d: DIVISION_ORDER.get(d, 99),
)

# Default selection — first 2 teams alphabetically, just so the
# page never loads with an empty graph
default_team_ids = [
    row["TEAM_ID"] for _, row in team_lookup.sort_values("TEAM_NAME").head(2).iterrows()
]

box_style = {
    "margin": "25px auto",
    "padding": "25px",
    "border": "2px solid black",
    "max-width": "1500px",
    "width": "90%",
    "backgroundColor": "#ffa826c1",
    "borderRadius": "4px",
}

def _build_division_checklist(division, df):
    div_df = df[df["DIVISION"] == division].sort_values("TEAM_NAME")
    options = [
        {"label": row["TEAM_NAME"], "value": row["TEAM_ID"]}
        for _, row in div_df.iterrows()
    ]
    all_team_ids = [opt["value"] for opt in options]
    preselected = [opt["value"] for opt in options if opt["value"] in default_team_ids]
    select_all_value = ["ALL"] if set(preselected) == set(all_team_ids) else []

    return html.Div([
        dcc.Checklist(
            id={"type": "p2-division-select-all", "division": division},
            options=[{"label": division, "value": "ALL"}],
            value=select_all_value,
            className="division-label",
            style={"marginTop": "8px"},
        ),
        dcc.Checklist(
            id={"type": "p2-division-checklist", "division": division},
            options=options,
            value=preselected,
            labelStyle={"display": "block", "padding": "2px 0 2px 10px"},
        ),
    ])

def _build_team_selector_grid(df):
    return html.Div([
        _build_division_checklist(division, df)
        for division in division_order_sorted
    ])

layout = html.Div([
     html.H2("Team Performance Across Seasons", className="page-title"),
        html.P("Track a single team's win percentage across seasons to spot rebuilds, "
           "sustained success, or decline."),
    html.Div([
        html.Div([
            html.Label("Select Teams to Display (up to 5):"),
    html.Div(
        _build_team_selector_grid(team_lookup),
        className="checklist-frame",
        style={
            "maxHeight":"500px",
            "overflowY":"auto",
            "overflowX":"hidden",
            "width":"100%",
            "boxSizing":"border-box",
            "fontSize":"14px",
        },
    ),
                html.Div(id="team-limit-warning", style={"color":"#b00020", "fontSize":"0.9rem", "marginTop":"5px"}),
        ], style={"flex":"1","minWidth":"250px", "margin":"10px"}),
               html.Div([
            html.Label("Compare Win % Against", htmlFor="metric-dropdown"),
            dcc.Dropdown(
                id="metric-dropdown",
                options=metric_dropdown_options,
                value=default_metric,
                clearable=False,
            ),
        ], className="dropdown-frame", style={"flex": "1", "minWidth": "250px", "margin": "10px"}),
    ], style={"display": "flex", "flexWrap": "wrap"}),
    html.Div(
        dcc.Graph(id="team-trend-line", style={"height":"850px"}),
        className="chart-frame",
    ),
], style=box_style)

@callback(
    Output({"type": "p2-division-select-all", "division": MATCH}, "value"),
    Output({"type": "p2-division-checklist", "division": MATCH}, "value", allow_duplicate=True),
    Input({"type": "p2-division-select-all", "division": MATCH}, "value"),
    Input({"type": "p2-division-checklist", "division": MATCH}, "value"),
    State({"type": "p2-division-checklist", "division": MATCH}, "options"),
    prevent_initial_call=True,
)
def sync_division_select_all(select_all_value, checklist_value, options):
    all_team_ids = [opt["value"] for opt in options]
    triggered_id = ctx.triggered_id

    if triggered_id["type"] == "p2-division-select-all":
        # Master checkbox was clicked -> select or clear every team in this division
        if select_all_value == ["ALL"]:
            return ["ALL"], all_team_ids
        return [], []

    # Otherwise an individual team box changed -> update the master to match
    if set(checklist_value) == set(all_team_ids):
        return ["ALL"], checklist_value
    return [], checklist_value

@callback(
    Output("team-trend-line", "figure"),
    Output("team-limit-warning", "children"),
    Input({"type": "p2-division-checklist", "division": ALL}, "value"),
    Input("metric-dropdown", "value"),
)

def update_team_trend(division_selections, selected_metric):
    selected_team_ids = [team_id for division_values in division_selections for team_id in division_values]
    warning_msg = ""
    if not selected_team_ids:
        fig = go.Figure()
        fig.update_layout(title="Select at least one team")
        return fig, warning_msg

    if len(selected_team_ids) > MAX_TEAMS:
        warning_msg = f"Showing the first {MAX_TEAMS} teams selected — uncheck one to add another."
        selected_team_ids = selected_team_ids[:MAX_TEAMS]

    metric_valid = selected_metric in team_stats.columns
    metric_label, metric_is_pct = METRIC_OPTIONS.get(selected_metric, (selected_metric, False))

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
    )

    for i, team_id in enumerate(selected_team_ids):
        filtered = team_stats[team_stats["TEAM_ID"] == team_id].sort_values("SEASON")
        if filtered.empty:
            continue

        team_label = filtered["TEAM_NAME"].iloc[0] if "TEAM_NAME" in filtered.columns \
            else filtered["TEAM_ABBREVIATION"].iloc[0]
        color = TEAM_COLORS[i % len(TEAM_COLORS)]

        # Top panel: Win %
        fig.add_trace(
            go.Scatter(
                x=filtered["SEASON"],
                y=filtered["WIN_PCT"],
                name=team_label,
                legendgroup=str(team_id),
                mode="lines+markers",
                line=dict(color=color),
                hovertemplate=f"{team_label}<br>Season %{{x}}<br>Win %: %{{y:.1%}}<extra></extra>",
            ),
            row=1, col=1,
        )

        # Bottom panel: selected metric
        if metric_valid:
            hover_fmt = "%{y:.1%}" if metric_is_pct else "%{y:.1f}"
            fig.add_trace(
                go.Scatter(
                    x=filtered["SEASON"],
                    y=filtered[selected_metric],
                    name=team_label,
                    legendgroup=str(team_id),
                    showlegend=False,  # avoid duplicate legend entry per team
                    mode="lines+markers",
                    line=dict(color=color),
                    hovertemplate=f"{team_label}<br>Season %{{x}}<br>{metric_label}: {hover_fmt}<extra></extra>",
                ),
                row=2, col=1,
            )

    fig.update_yaxes(title_text="Win %", tickformat=".0%", range=[0, 1], row=1, col=1)
    fig.update_yaxes(
        title_text=metric_label if metric_valid else "",
        tickformat=".0%" if metric_is_pct else None,
        row=2, col=1,
    )
    fig.update_xaxes(title_text="Season", row=2, col=1)

    fig.update_layout(
        title=f"Win % vs {metric_label if metric_valid else 'Metric'} by Season",
        margin=dict(t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        font=dict(family="Inter, Arial, sans-serif", color="#001238", size=16),
        title_font=dict(family="Oswald, Arial, sans-serif", size=26, color="#001238"),
    )

    return fig, warning_msg