import pandas as pd
import dash
from dash import Dash, html, dcc, Input, Output, callback
import plotly.express as px
from pathlib import Path

dash.register_page(__name__, path="/", name="HOME")

THIS_DIR = Path(__file__).resolve().parent
CANDIDATE_PATHS = [
    THIS_DIR / "team_stats_2021_2026.csv",
    THIS_DIR.parent / "team_stats_2021_2026.csv",
]
CSV_PATH = next((p for p in CANDIDATE_PATHS if p.exists()), CANDIDATE_PATHS[0])

df = pd.read_csv(CSV_PATH)

TEAM_COL = "TEAM_ABBREVIATION" if "TEAM_ABBREVIATION" in df.columns else "TEAM_NAME"

SEASONS = sorted(df["SEASON"].unique())
DEFAULT_SEASON = SEASONS[-1]

box_style = {
    "margin": "25px auto",
    "padding": "25px",
    "border":"2px solid black",
    "max-width":"1500px",
    "width": "90%",
    "backgroundColor":"#ffa826c1",
    "borderRadius":"4px"
}

layout = html.Div([
    html.H2("NBA Team Power Rankings"),
    html.P("[INSERT DESCRIPTION ABOUT THE SPORTS API SALARY CAP SITUTATION (FROM TEAM TO TEAM) HERE]."),
        html.Div([
                html.Label("Season", htmlFor="season-dropdown"),
        dcc.Dropdown(
            id="season-dropdown",
            options=[{"label": season, "value": season} for season in SEASONS],
            value=DEFAULT_SEASON,
            clearable=False,
        ),
    ], className="dropdown-frame", style={"margin":"30px 10px 10px 10px", "max-width":"300px"}),
    html.Div(
        dcc.Graph(id="rankings-bar-chart", style={"height":"650px"}),
        className="chart-frame",
    ),
], style=box_style)

@callback(
    Output("rankings-bar-chart", "figure"),
    Input("season-dropdown", "value"),
)
def update_rankings_chart(season):
    season_df = df[df["SEASON"] == season].sort_values("NET_RATING", ascending=False)

    fig = px.bar(
        season_df,
        x=TEAM_COL,
        y="NET_RATING",
        color="NET_RATING",
        color_continuous_scale = "RdYlGn",
        color_continuous_midpoint = 0,
        hover_data={
            "TEAM_NAME": True,
            "WIN_PCT": ":.3f",
            "W": True,
            "L": True,
            TEAM_COL: False,
        },
        labels={"NET_RATING": "Net Rating", TEAM_COL: "Team"},
        title=f"NBA Team Net Rating -- {season} Regular Season",
    )
    fig.update_xaxes(categoryorder="total descending", title="Team")
    fig.update_yaxes(title="Net Rating")
    fig.update_layout(
        coloraxis_showscale=False,
        margin=dict(t=60, b=40),
        height=650,
        font=dict(family="Inter, Arial, sans-serif", color="#001238", size=16),
        title_font=dict(family="Oswald, Arial, sans-serif", size=24, color="#001238")
    )
    return fig