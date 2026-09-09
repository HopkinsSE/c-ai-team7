########################### AI USE ################################
## Used Claude to help build bar chart.
## Used Claude help create dropdown.
## Used Claude to fix hover tooltip to display in the correct format.
## Used Claude to debug and troubleshoot small syntax errors.
## Reviewed and tested by all team members.
###################################################################
import pandas as pd
import dash
from dash import html, dcc, Input, Output, callback
import plotly.express as px
from pathlib import Path
import gunicorn

# Registers as home page of the multi-page app
dash.register_page(__name__, path="/", name="HOME")

# Look for the CSV in this folder first, then one level up — makes the app portable
# regardless of whether this file lives in a /pages subfolder or the project root
THIS_DIR = Path(__file__).resolve().parent
CANDIDATE_PATHS = [
    THIS_DIR / "team_stats_2021_2026.csv",
    THIS_DIR.parent / "team_stats_2021_2026.csv",
]
CSV_PATH = next((p for p in CANDIDATE_PATHS if p.exists()), CANDIDATE_PATHS[0])

df = pd.read_csv(CSV_PATH)

# Prefer short team abbreviations for cleaner axis labels; fall back to full name if missing
# Build the season list for the slider/dropdown and default to the most recent season
TEAM_COL = "TEAM_ABBREVIATION" if "TEAM_ABBREVIATION" in df.columns else "TEAM_NAME"

SEASONS = sorted(df["SEASON"].unique())
DEFAULT_SEASON = SEASONS[-1]

# Shared container styling for the page card (used on layout below)
box_style = {
    "margin": "25px auto",
    "padding": "25px",
    "border":"2px solid black",
    "max-width":"1500px",
    "width": "90%",
    "backgroundColor":"#ffa826c1",
    "borderRadius":"4px"
}

# Page layout: title, glossary intro paragraph, season selector, and the chart placeholder
# the callback below fills in `rankings-bar-chart`
layout = html.Div([
    html.H2("NBA Team Power Rankings"),
    html.P([
        f"Every team's story starts with two questions: can you score, and can you stop the other team from scoring. This site breaks down NBA team performance using the numbers that matter most — not just wins and losses, but the underlying efficiency that drives them. We look at five seasons of team data to answer one question: what actually separates the good teams from the great ones? A few terms you'll see throughout:",
           html.Br(), html.Br(),
            f"Offensive Rating  — Points scored per 100 possessions.",
            html.Br(),
            f"Defensive Rating  — Points allowed per 100 possessions.",
            html.Br(),
            f"Net Rating — Difference between Offensive Rating and Defensive Rating.",
            html.Br(),
            f"Effective Field Goal Percentage — Shooting efficiency stat that adjusts regular field goal percentage to account for three pointers being worth more than two point field goals.",
            html.Br(),
            f"Pace — Number of possessions a team uses per 48 minutes."]
),
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

#filters df down to the selected season and sorts by Net Rating descending
def update_rankings_chart(season):
    season_df = df[df["SEASON"] == season].sort_values("NET_RATING", ascending=False)

# Bar chart colored on a red-to-green scale centered at 0, since Net Rating is naturally
# a "better/worse than average" stat — custom_data stages fields for the hover tooltip
    fig = px.bar(
        season_df,
        x=TEAM_COL,
        y="NET_RATING",
        color="NET_RATING",
        color_continuous_scale = "RdYlGn",
        color_continuous_midpoint = 0,
        custom_data=["TEAM_NAME", "WIN_PCT", "W", "L"],        labels={"NET_RATING": "Net Rating", TEAM_COL: "Team"},
        title=f"NBA Team Net Rating -- {season} Regular Season",
)
    # Hide default tick labels/title — team identity is shown via logos instead (see below)
    fig.update_xaxes(categoryorder="total descending",
                     title=None, showticklabels=False,)
    fig.update_yaxes(title="Net Rating")
    fig.update_traces(
        # Custom hover box: team name, net rating, win %, and record
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Net Rating: %{y:.1f}<br>"
            "Win %: %{customdata[1]:.1%}<br>"
            "Wins: %{customdata[2]}<br>"
            "Losses: %{customdata[3]}<extra></extra>"
        )
    )
    # Hide the color scale bar, add bottom margin for the logo row, and set consistent fonts
    fig.update_layout(
        coloraxis_showscale=False,
        margin=dict(t=60, b=140),
        height=650,
        font=dict(family="Inter, Arial, sans-serif", color="#001238", size=16),
        title_font=dict(family="Oswald, Arial, sans-serif", size=26, color="#001238")
    )
    # Place each team's logo below its bar in place of a text tick label (loops row-by-row
# since add_layout_image only accepts one image per call)
    for _, row in season_df.iterrows():
        logo_url = row.get("LOGO_URL")
        if pd.notna(logo_url) and str(logo_url).strip():
            fig.add_layout_image(
                dict(
                    source=logo_url,
                    xref="x", yref="paper",
                    x=row[TEAM_COL], y=-0.03,
                    sizex=0.9, sizey=0.12,
                    xanchor="center", yanchor="top",
                    layer="above",
                )
            )
    # Manual x-axis label, since the built-in axis title was disabled above
    fig.add_annotation(
    text="Team",
    xref="paper", yref="paper",
    x=0.5, y=-0.19,
    xanchor="center", yanchor="top",
    showarrow=False,
    font=dict(family="Inter, Arial, sans-serif", size=20, color="#001238"),
    )
    return fig