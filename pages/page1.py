import dash
from dash import html, dcc, callback, Input, Output, ALL, MATCH, ctx, State
import dash_bootstrap_components as dbc
import requests
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

dash.register_page(__name__, path="/page1", name="Page 1")

#load data - will need to remove later
THIS_DIR = Path(__file__).resolve().parent

def _find_csv(filename):
    candidates = [THIS_DIR / filename, THIS_DIR.parent / filename]
    return next((p for p in candidates if p.exists()), candidates[0])

team_meta = pd.read_csv(_find_csv("team_meta.csv"))
team_stats = pd.read_csv(_find_csv("team_stats_2021_2026.csv"))

# Merge in TEAM_ID / CONFERENCE from team_meta so the checklist filter
# and scatter color grouping have something to work with
meta_cols_to_add = [
    c for c in team_meta.columns
    if c == "TEAM_ABBREVIATION" or c not in team_stats.columns
]
team_stats = team_stats.merge(
    team_meta[meta_cols_to_add],
    on="TEAM_ABBREVIATION",
    how="left",
)

# ---- Build dropdown options from the efficiency columns ----
METRIC_LABELS = {
    "NET_RATING": "Net Rating",
    "OFF_RATING": "Offensive Rating",
    "DEF_RATING": "Defensive Rating",
    "PACE": "Pace",
    "EFG_PCT": "Effective FG%",
}
PERCENT_METRICS = {"EFG_PCT"}
metric_options = [{"label": v, "value": k} for k, v in METRIC_LABELS.items()]

# ---- Hardcoded division map (NBA divisions are fixed, not in the data) ----
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

# ---- Sorted list of seasons for the season dropdown ----# Sorted list of season strings, e.g. ['2021-2022', '2022-2023', ...]
season_list = sorted(team_stats["SEASON"].unique())

team_lookup = (
    team_stats[["TEAM_ID", "TEAM_NAME", "TEAM_ABBREVIATION", "CONFERENCE"]]
    .drop_duplicates()
    .copy()
)
team_lookup["DIVISION"] = team_lookup["TEAM_ABBREVIATION"].map(DIVISION_MAP)

# Flag (don't crash on) any team that didn't match the hardcoded map,
# e.g. if an abbreviation is spelled differently than expected
_missing = team_lookup[team_lookup["DIVISION"].isna()]
if not _missing.empty:
    print("Warning: no division match for:", _missing["TEAM_ABBREVIATION"].tolist())

def _build_conference_header(conference_label):
    """Just the top-level 'select all teams in this conference' checkbox."""
    return dcc.Checklist(
        id={"type": "conference-select-all", "conference": conference_label},
        options=[{"label": f"{conference_label} Conference", "value": "ALL"}],
        value=["ALL"],
        className="conference-label",
    )


def _build_division_block(conference_label, division, df):
    """One division's select-all checkbox + its team checklist."""
    div_df = df[(df["CONFERENCE"] == conference_label) & (df["DIVISION"] == division)]
    div_df = div_df.sort_values("TEAM_NAME")
    options = [
        {"label": row["TEAM_NAME"], "value": row["TEAM_ID"]}
        for _, row in div_df.iterrows()
    ]
    values = div_df["TEAM_ID"].tolist()

    return html.Div(
        [
            dcc.Checklist(
                id={
                    "type": "division-select-all",
                    "conference": conference_label,
                    "division": division,
                },
                options=[{"label": division, "value": "ALL"}],
                value=["ALL"],
                className="division-label",
            ),
            dcc.Checklist(
                id={
                    "type": "division-checklist",
                    "conference": conference_label,
                    "division": division,
                },
                options=options,
                value=values,
            ),
        ]
    )


def _build_team_selector_grid(df):
    """East/West headers on top; below, 3 rows pairing one East division
    with one West division side by side (Atlantic|Northwest, Central|Pacific,
    Southeast|Southwest)."""
    conferences = sorted(df["CONFERENCE"].dropna().unique())  # ["East", "West"]

    conf_divisions = {
        conf: sorted(
            df[df["CONFERENCE"] == conf]["DIVISION"].dropna().unique(),
            key=lambda d: DIVISION_ORDER.get(d, 99),
        )
        for conf in conferences
    }
    max_rows = max(len(divs) for divs in conf_divisions.values())

    rows = [
        dbc.Row(
            [dbc.Col(_build_conference_header(conf), width=6) for conf in conferences],
            className="mb-2",
        )
    ]

    for i in range(max_rows):
        cols = []
        for conf in conferences:
            divs = conf_divisions[conf]
            if i < len(divs):
                cols.append(dbc.Col(_build_division_block(conf, divs[i], df), width=6))
            else:
                cols.append(dbc.Col(width=6))  # keeps columns aligned if uneven counts
        rows.append(dbc.Row(cols, className="mb-2"))

    return html.Div(rows)

layout = html.Div([
        html.Div([
        html.H2("Efficiency vs. Win % Explorer", className="page-title"),
                html.P(f"Talent shows up in the box score, but it doesn’t tell the full story about team success. This page includes advanced stats for every team in relation to success in a manner that tells a much deeper story."
                        f"Each dot is a team, plotted by Win % against an advanced metric of your choosing. Net Rating tends to line up closely with winning — it should, since it accounts for both ends of the floor. Other metrics tell a different story: a team can pace up and down and still lose, or shoot a high effective field goal percentage without translating it into wins."
                        f"Filter by conference, division, or individual team to see whether the pattern holds across the entire league or breaks down in specific matchups. If a team sits well off the trend line, that's usually where the interesting story is."
,
                   className="page-subtitle"),
    ],
    style={
        "backgroundColor": "#ffa826c1",
        "padding": "20px 25px",
        "borderRadius": "6px",
        "marginBottom": "20px",
    },
    ),

    # ---- Top controls row: metric dropdown + full-width season slider ----
    dbc.Row(
        [
            dbc.Col(
                html.Div(
                    [
                        html.Label("Select Efficiency Metric:"),
                        dcc.Dropdown(
                            id="metric-dropdown",
                            options=metric_options,
                            value="NET_RATING",
                            clearable=False
                        ),
                    ],
                    className="dropdown-frame",
                ),
                md=3,
            ),
            dbc.Col(
                html.Div(
                    [
                        html.Label("Select Season:"),
                        dcc.Dropdown(
                            id="page1-season-dropdown",
                            options=[{"label": season, "value": season} for season in season_list],
                            value=season_list[-1],
                            clearable=False,
                        ),
                    ],
                    className="dropdown-frame",
                ),
                md=3,
            ),
        ],
        className="mb-3",
    ),

    # ---- Team selector grid (left, scrollable) + chart (right) ----
       # ---- Team selector grid (left, scrollable) + chart (right) ----
    dbc.Row(
        [
            dbc.Col(
                [
                    html.Label("Select Teams to Display:"),
                    html.Div(
                        _build_team_selector_grid(team_lookup),
                        className="checklist-frame",
                        style={
                            "maxHeight": "650px",
                            "overflowY": "auto",
                            "overflowX": "hidden",
                            "width": "100%",
                            "boxSizing": "border-box",
                            "fontSize": "14px",
                        },
                    ),
                ],
                md=3,
            ),
                        dbc.Col(
                html.Div(
                    dcc.Graph(
                        id="efficiency-scatter",
                        style={"height": "650px", "width": "100%"},
                        config={"responsive": True},
                    ),
                    className="chart-frame",
                ),
                md=9,
            ),
        ],
        className="g-3",
    ),
], className="page1-wrap", style={"padding": "20px 30px", "maxWidth": "100%"})

def _build_logo_scatter(df, x_col, y_col, x_label, y_label, title, x_is_pct=False):
    """
    Builds a scatter plot where each point is a team's logo instead of a dot.
    An invisible trace drives hover tooltips; logos are layered on top via
    add_layout_image. Teams missing a logo URL fall back to a gray dot.
    """
    fig = go.Figure()
    x_fmt = "%{x:.1%}" if x_is_pct else "%{x:.1f}"
    fig.add_trace(
        go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode="markers",
            marker=dict(size=1, opacity=0),
            customdata=df["TEAM_NAME"],
            hovertemplate=(
                f"<b>%{{customdata}}</b><br>"
                f"{x_label}: {x_fmt}<br>"
                f"{y_label}: %{{y:.1%}}<extra></extra>"
            ),
            showlegend=False,
        )
    )

    x_range = df[x_col].max() - df[x_col].min()
    y_range = df[y_col].max() - df[y_col].min()
    sizex = x_range * 0.12 if x_range > 0 else 1
    sizey = y_range * 0.12 if y_range > 0 else 0.05

    has_missing_logo = False
    for _, row in df.iterrows():
        logo_url = row.get("LOGO_URL")
        if pd.notna(logo_url) and str(logo_url).strip():
            fig.add_layout_image(
                dict(
                    source=logo_url,
                    xref="x", yref="y",
                    x=row[x_col], y=row[y_col],
                    sizex=sizex, sizey=sizey,
                    xanchor="center", yanchor="middle",
                    layer="above",
                )
            )
        else:
            has_missing_logo = True
            fig.add_trace(
                go.Scatter(
                    x=[row[x_col]], y=[row[y_col]],
                    mode="markers",
                    marker=dict(size=12, color="gray", line=dict(width=1, color="white")),
                    hovertext=[row["TEAM_NAME"]],
                    hoverinfo="text",
                    showlegend=False,
                )
            )
    xaxis_settings = dict(tickformat=".0%") if x_is_pct else dict()
    
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        xaxis=xaxis_settings,
        yaxis_title=y_label,
        yaxis=dict(range=[0, 1], tickformat=".0%"),
                template="plotly_white",
        margin=dict(l=60, r=30, t=60, b=50),
        autosize=True,
        font=dict(family="Inter, Arial, sans-serif", color="#001238", size=16),
        title_font=dict(family="Oswald, Arial, sans-serif", size=26, color="#001238"),
        hoverlabel=dict(
            bgcolor="#070096",
            font_color="#ffffff",
            font_size=13,
        ),
    )

    if has_missing_logo:
        fig.add_annotation(
            text="Gray dots = logo unavailable for that team",
            xref="paper", yref="paper",
            x=0, y=1.08, showarrow=False,
            font=dict(size=11, color="gray"),
        )
    return fig

@callback(
    Output({"type": "division-select-all", "conference": MATCH, "division": MATCH}, "value"),
    Output({"type": "division-checklist", "conference": MATCH, "division": MATCH}, "value", allow_duplicate=True),
    Input({"type": "division-select-all", "conference": MATCH, "division": MATCH}, "value"),
    Input({"type": "division-checklist", "conference": MATCH, "division": MATCH}, "value"),
    State({"type": "division-checklist", "conference": MATCH, "division": MATCH}, "options"),
    prevent_initial_call=True,
)
def sync_division_select_all(select_all_value, checklist_value, options):
    all_team_ids = [opt["value"] for opt in options]
    triggered_id = ctx.triggered_id

    if triggered_id["type"] == "division-select-all":
        # The master checkbox was clicked -> select or clear every team here
        if select_all_value == ["ALL"]:
            return ["ALL"], all_team_ids
        return [], []

    # Otherwise an individual team box changed -> update the master to match
    if set(checklist_value) == set(all_team_ids):
        return ["ALL"], checklist_value
    return [], checklist_value
@callback(
    Output({"type": "division-checklist", "conference": MATCH, "division": ALL}, "value", allow_duplicate=True),
    Input({"type": "conference-select-all", "conference": MATCH}, "value"),
    State({"type": "division-checklist", "conference": MATCH, "division": ALL}, "options"),
    prevent_initial_call=True,
)
def sync_conference_select_all(conference_value, all_division_options):
    if conference_value == ["ALL"]:
        return [[opt["value"] for opt in division_options] for division_options in all_division_options]
    return [[] for _ in all_division_options]

@callback(
    Output("efficiency-scatter", "figure"),
    Input("metric-dropdown", "value"),
    Input("page1-season-dropdown", "value"),
    Input({"type": "division-checklist", "conference": ALL, "division": ALL}, "value"),
)

def update_scatter(selected_metric, selected_season, division_selections):
    selected_team_ids = [
        team_id for division_values in division_selections for team_id in division_values
    ]
    # Step 1: filter rows to just that season
    filtered = team_stats[team_stats["SEASON"] == selected_season]
    # Step 2: filter rows to just the checked teams
    filtered = filtered[filtered["TEAM_ID"].isin(selected_team_ids)]
    # Step 3: handle the empty-selection edge case
    if filtered.empty:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title = "No teams selected - check at least one team above",
            template="plotly_white",
        )
        return empty_fig
    # Step 4: build labels and the scatter plot
    x_label = METRIC_LABELS.get(selected_metric, selected_metric.replace("_", " ").title())
    y_label = "Win %"
    title = f"{x_label} vs. {y_label} - {selected_season}"
    x_is_pct = selected_metric in PERCENT_METRICS
    return _build_logo_scatter(filtered, selected_metric, "WIN_PCT", x_label, y_label, title, x_is_pct=x_is_pct)