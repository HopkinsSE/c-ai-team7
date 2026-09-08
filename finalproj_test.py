import nba_api
import time
import pandas as pd
from nba_api.stats.endpoints import leaguedashteamstats

seasons = ['2022-23', '2023-24', '2024-25', '2025-26']

all_seasons = []

for season in seasons:
    stats = leaguedashteamstats.LeagueDashTeamStats(
        season=season,
        season_type_all_star='Regular Season',
        measure_type_detailed_defense='Advanced'
    )
    df = stats.get_data_frames()[0]
    df['SEASON'] = season
    all_seasons.append(df)
    time.sleep(0.6)

    combined = pd.concat(all_seasons, ignore_index=True)
    print(combined.shape)

    print(combined)