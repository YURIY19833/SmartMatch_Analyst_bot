import logging
import pandas as pd
import numpy as np
import psycopg2
from db_config import get_connection

logger = logging.getLogger(__name__)


def create_ml_dataset():
    try:
        conn = get_connection()
    except psycopg2.OperationalError as e:
        logger.error("Database connection error: %s", e)
        return pd.DataFrame()

    df = pd.read_sql_query("SELECT * FROM raw_matches ORDER BY match_date ASC;", conn)
    conn.close()

    df["match_date"] = pd.to_datetime(df["match_date"])
    df["target"] = np.where(df["score_1"] > df["score_2"], 1, 0)

    team_points = {}
    team_gd = {}

    home_pts_list = []
    away_pts_list = []
    home_gd_list = []
    away_gd_list = []

    for _, row in df.iterrows():
        h_team = row["team_1"]
        a_team = row["team_2"]

        h_pts_history = team_points.get(h_team, [])
        home_pts_list.append(np.mean(h_pts_history[-5:]) if len(h_pts_history) > 0 else 1.2)

        a_pts_history = team_points.get(a_team, [])
        away_pts_list.append(np.mean(a_pts_history[-5:]) if len(a_pts_history) > 0 else 1.2)

        h_gd_history = team_gd.get(h_team, [])
        home_gd_list.append(np.mean(h_gd_history[-5:]) if len(h_gd_history) > 0 else 0.0)

        a_gd_history = team_gd.get(a_team, [])
        away_gd_list.append(np.mean(a_gd_history[-5:]) if len(a_gd_history) > 0 else 0.0)

        s1, s2 = row["score_1"], row["score_2"]
        h_match_pts = 3 if s1 > s2 else (1 if s1 == s2 else 0)
        a_match_pts = 3 if s2 > s1 else (1 if s1 == s2 else 0)

        h_match_gd = s1 - s2
        a_match_gd = s2 - s1

        team_points.setdefault(h_team, []).append(h_match_pts)
        team_points.setdefault(a_team, []).append(a_match_pts)
        team_gd.setdefault(h_team, []).append(h_match_gd)
        team_gd.setdefault(a_team, []).append(a_match_gd)

    df["home_pts_form"] = home_pts_list
    df["away_pts_form"] = away_pts_list
    df["home_gd_form"] = home_gd_list
    df["away_gd_form"] = away_gd_list

    features = [
        "match_date",
        "team_1",
        "team_2",
        "home_pts_form",
        "away_pts_form",
        "home_gd_form",
        "away_gd_form",
        "target",
    ]
    final_df = df[features]

    final_df.to_csv("sports_data_cleaned.csv", index=False)
    logger.info("[SUCCESS] Cleaned dataset generated. Rows: %d", len(final_df))
    return final_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_ml_dataset()
