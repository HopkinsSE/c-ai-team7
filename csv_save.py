import time
import sys
import pandas as pd
from nba_api.stats.endpoints import leaguedashteamstats

#Set up the seasons we want to pull
SEASONS = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]

#Set up the columns we want to keep from the API call
BASE_COLS = [
    "TEAM_ID", "TEAM_NAME", "GP", "W", "L", "W_PCT",
]

ADV_COLS = [
    "TEAM_ID", "OFF_RATING", "DEF_RATING", "NET_RATING", "PACE", "EFG_PCT",
]

#Retry/timeout behavior for the API calls
MAX_RETRIES = 4
RETRY_SLEEP_SECONDS = 5
BETWEEN_CALL_SLEEP_SECONDS = 1.0
TIMEOUT_SECONDS = 30

#Calls the NBA leaguedashteamstats, retries on failure/timeout/empty response
#Does it up to MAX_RETRIES (4) time before giving up and raises a RuntimeError
def fetch_with_retry(measure_type: str, season: str) -> pd.DataFrame:
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = leaguedashteamstats.LeagueDashTeamStats(
                season=season,
                season_type_all_star="Regular Season",
                per_mode_detailed="PerGame",
                measure_type_detailed_defense=measure_type,
                timeout=TIMEOUT_SECONDS,
            )
            df = resp.get_data_frames()[0]
            if df.empty:
                raise ValueError("Empty response")
            return df
        except Exception as e:
            last_err = e
            print(f"[{season}] | {measure_type} attempt {attempt}/{MAX_RETRIES}"
                  f" failed: {e!r}"
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_SLEEP_SECONDS)
    raise RuntimeError(
        f"Failed to fetch {measure_type} stats for {season} after"
        f"{MAX_RETRIES}. Last error: {last_err!r}")

#Fetchs and merges the Base and Advanced stats for one season into a single
#30-row-per-season dataframe
def fetch_season(season: str) -> pd.DataFrame:
    print(f"Fetching {season}")
    base_df = fetch_with_retry("Base", season)
    time.sleep(BETWEEN_CALL_SLEEP_SECONDS)
    adv_df = fetch_with_retry("Advanced", season)
    time.sleep(BETWEEN_CALL_SLEEP_SECONDS)

    base_df = base_df[[c for c in BASE_COLS if c in base_df.columns]].copy()
    adv_df = adv_df[[c for c in ADV_COLS if c in adv_df.columns]].copy()

    merged = base_df.merge(adv_df, on="TEAM_ID", how="inner")
    merged.insert(0, "SEASON", season)
    #Renames W_PCT -> WIN_PCT for readability

    merged.rename(columns={"W_PCT":"WIN_PCT"}, inplace=True)
    #Prints warning if less than 30 teams come back to warn against bad data
    if len(merged) != 30:
        print(f"WARNING: expected 30 teams for {season}, got {len(merged)}. Check data.")
    return merged

#Create Static team reference table (abbreviation, conference, brand color).
#Written to team_meta.csv and also merged into the season stats file 
#so the dashboard has colors/logos/conference without extra lookups.
TEAM_META = [
    (1610612737, "ATL", "East", "#E03A3E"),
    (1610612738, "BOS", "East", "#007A33"),
    (1610612751, "BKN", "East", "#000000"),
    (1610612766, "CHA", "East", "#1D1160"),
    (1610612741, "CHI", "East", "#CE1141"),
    (1610612739, "CLE", "East", "#860038"),
    (1610612742, "DAL", "West", "#00538C"),
    (1610612743, "DEN", "West", "#0E2240"),
    (1610612765, "DET", "East", "#C8102E"),
    (1610612744, "GSW", "West", "#1D428A"),
    (1610612745, "HOU", "West", "#CE1141"),
    (1610612754, "IND", "East", "#002D62"),
    (1610612746, "LAC", "West", "#C8102E"),
    (1610612747, "LAL", "West", "#552583"),
    (1610612763, "MEM", "West", "#5D76A9"),
    (1610612748, "MIA", "East", "#98002E"),
    (1610612749, "MIL", "East", "#00471B"),
    (1610612750, "MIN", "West", "#0C2340"),
    (1610612740, "NOP", "West", "#0C2340"),
    (1610612752, "NYK", "East", "#006BB6"),
    (1610612760, "OKC", "West", "#007AC1"),
    (1610612753, "ORL", "East", "#0077C0"),
    (1610612755, "PHI", "East", "#006BB6"),
    (1610612756, "PHX", "West", "#1D1160"),
    (1610612757, "POR", "West", "#E03A3E"),
    (1610612758, "SAC", "West", "#5A2D81"),
    (1610612759, "SAS", "West", "#C4CED4"),
    (1610612761, "TOR", "East", "#CE1141"),
    (1610612762, "UTA", "West", "#002B5C"),
    (1610612764, "WAS", "East", "#002B5C"),
]

#Write team metadata, fetch each season
def write_team_meta():
    meta_df = pd.DataFrame(
        TEAM_META, columns=["TEAM_ID", "TEAM_ABBREVIATION", "CONFERENCE", "PRIMARY_COLOR"])
    #Built from NBA.com's public CDN path pattern to grab logos
    meta_df["LOGO_URL"] = meta_df["TEAM_ID"].apply(
        lambda tid: f"https://cdn.nba.com/logos/nba/{tid}/global/L/logo.svg"
    )
    meta_df.to_csv("team_meta.csv", index=False)
    print(f"Saved {len(meta_df)} rows to team_meta.csv")
    return meta_df

def main():
    meta_df = write_team_meta()
 
    all_seasons = []
    for season in SEASONS:
        try:
            all_seasons.append(fetch_season(season))
        except RuntimeError as e:
            print(f"ERROR: giving up on {season}: {e}", file=sys.stderr)
 
    if not all_seasons:
        print("No data was fetched successfully. Exiting.", file=sys.stderr)
        sys.exit(1)
 
    full = pd.concat(all_seasons, ignore_index=True)
 
    # Reorder columns nicely
    ordered_cols = [
        "SEASON", "TEAM_ID", "TEAM_NAME", "GP", "W", "L", "WIN_PCT",
        "NET_RATING", "OFF_RATING", "DEF_RATING", "PACE", "EFG_PCT",
    ]
    ordered_cols = [c for c in ordered_cols if c in full.columns]
    full = full[ordered_cols].sort_values(["SEASON", "NET_RATING"], ascending=[True, False])
 
    # Join in abbreviation/conference/color for convenience.
    full = full.merge(
        meta_df[["TEAM_ID", "TEAM_ABBREVIATION", "CONFERENCE", "PRIMARY_COLOR", "LOGO_URL"]],
        on="TEAM_ID",
        how="left",
    )
 #Saves to team_stats_2021_2026.csv for final use
    out_path = "team_stats_2021_2026.csv"
    full.to_csv(out_path, index=False)
    print(f"\nSaved {len(full)} rows to {out_path}")
    print(full.head(10).to_string(index=False))
 
 
if __name__ == "__main__":
    main()