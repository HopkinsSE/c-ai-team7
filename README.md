# c-ai-team7
# Team 7
# Jasmine Dickerson, Solomon Sledge, Sam Hopkins

## Project Overview
Our project is a dashboard app that contains content regarding data from the NBA, measuring the play history of each team across five seasons.  The problem was whether different efficiency metrics contained in the dataset correlated with the win percentage for each team, the question being if playing “efficient basketball” can win NBA games.  This dashboard was created for casual sports fans who are interested in the nuances of data collected by the NBA, as well as aspiring NBA analysts, who need to have advanced metrics summarized in a beginner-friendly format.  This project delivers valuable insights of the play history for each team in the NBA, and allows the user to visualize the win percentage of each team based on various efficiency measurements. 


## How to Run


### Local Setup


1. Clone the repo:
```bash
   git clone https://github.com/HopkinsSE/c-ai-team7.git
   cd c-ai-team7
```


2. Create and activate a virtual environment:
```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
```


3. Install dependencies:
```bash
   pip install -r requirements.txt
```


4. Run the app:
```bash
   python app.py
```


5. Open your browser to `http://127.0.0.1:8050`


### Live Deployment (Render)


- Live app: **https://c-ai-team7.onrender.com/**
- Hosted as a Web Service on Render, connected to this GitHub repo (auto-deploys on push to `main`)
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:server`
- Environment: Python 3.14.3


## Data Sources & Data Dictionary
 
### Data Sources
 
**1. NBA Stats API, via the `nba_api` Python package**
- Endpoint used: `leaguedashteamstats` (both `"Base"` and `"Advanced"` measure types), regular season only, per-game mode.
- Retrieved by running `csv_save.py` once and saving the result to `team_stats_2021_2026.csv` — the app itself does not call the API live; it reads from this static file.
- Seasons covered: 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 (5 seasons x 30 teams = 150 rows, no missing values).
- `nba_api` is an open-source, unofficial wrapper around stats.nba.com's endpoints — no API key or login required, but it isn't an officially licensed NBA data feed.
**2. Team reference data, compiled by the team**
- A hardcoded list in `csv_save.py` (`TEAM_META`) pairing each team's ID, 3-letter abbreviation, conference, and primary brand color, saved to `team_meta.csv` (30 rows, one per team).
- Logo image URLs are constructed from a predictable NBA CDN pattern (`https://cdn.nba.com/logos/nba/{TEAM_ID}/global/L/logo.svg`) and are fetched live by the browser when a chart renders — they are not downloaded/stored anywhere in the repo.
**3. Hardcoded division mapping (in code, not a file)**
- `pages/page1.py` and `pages/page2.py` each define a `DIVISION_MAP` dictionary assigning each team to its NBA division (Atlantic, Central, Southeast, Northwest, Pacific, Southwest). This isn't pulled from any API — the team-stats data doesn't include division, so it was typed in manually since NBA divisions are fixed/unchanging.
**Note on `finalproj_test.py`:** an early scratch script the team used to confirm the `nba_api` data was pulling correctly before building `csv_save.py`. It isn't imported or called anywhere in the running app and isn't part of the production data pipeline.
 
### Data Dictionary
 
**`team_stats_2021_2026.csv`** — 150 rows (30 teams x 5 seasons), no missing values
 
| Column | Type | Description | Example |
|---|---|---|---|
| `SEASON` | string | Season label | `"2021-22"` |
| `TEAM_ID` | integer | NBA's official numeric team ID | `1610612756` |
| `TEAM_NAME` | string | Full team name | `"Phoenix Suns"` |
| `GP` | integer | Games played that season | `82` |
| `W` | integer | Wins | `64` |
| `L` | integer | Losses | `18` |
| `WIN_PCT` | float | Win percentage (renamed from the API's `W_PCT`) | `0.78` |
| `NET_RATING` | float | Points scored minus points allowed per 100 possessions | `7.5` |
| `OFF_RATING` | float | Points scored per 100 possessions | `114.2` |
| `DEF_RATING` | float | Points allowed per 100 possessions | `106.8` |
| `PACE` | float | Possessions per 48 minutes | `100.26` |
| `EFG_PCT` | float | Effective field goal % (weights 3-pt makes) | `0.549` |
| `TEAM_ABBREVIATION` | string | 3-letter team code — merged in from `team_meta.csv` | `"PHX"` |
| `CONFERENCE` | string | `"East"` or `"West"` — merged in from `team_meta.csv` | `"West"` |
| `PRIMARY_COLOR` | string | Team's primary hex color — merged in from `team_meta.csv` | `"#1D1160"` |
| `LOGO_URL` | string | Link to the team's logo image — merged in from `team_meta.csv` | see CDN pattern above |
 
**`team_meta.csv`** — 30 rows (one per team), no missing values
 
| Column | Type | Description | Example |
|---|---|---|---|
| `TEAM_ID` | integer | NBA's official numeric team ID | `1610612756` |
| `TEAM_ABBREVIATION` | string | 3-letter team code | `"PHX"` |
| `CONFERENCE` | string | `"East"` or `"West"` | `"West"` |
| `PRIMARY_COLOR` | string | Team's primary hex color | `"#1D1160"` |
| `LOGO_URL` | string | Link to the team's logo image on NBA's CDN | see above |
 
**Cleaning performed** (from `csv_save.py`): merged `Base` and `Advanced` stat pulls on `TEAM_ID`; renamed `W_PCT` to `WIN_PCT` for clarity; joined in team abbreviation/conference/color/logo from the reference table; sorted rows by season then `NET_RATING`; verified each season returned exactly 30 teams before saving.