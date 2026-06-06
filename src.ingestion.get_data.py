import os
import logging
import requests
import psycopg2
import pandas as pd
import io
from db_config import DB_CONFIG, get_connection

logger = logging.getLogger(__name__)

# Require API key from environment for security; do not fall back to hardcoded key
API_KEY = os.environ.get("FOOTBALL_API_KEY")
HEADERS = {"X-Auth-Token": API_KEY} if API_KEY else {}

DB_CONFIG = {
    "dbname": "sports_db",
    "user": "user",
    "password": "password",
    "host": "localhost",
    "port": "5432",
}

# Словарь для синхронизации названий команд из CSV-архива с форматом API
TEAM_MAPPING = {
    "Arsenal": "Arsenal FC",
    "Aston Villa": "Aston Villa FC",
    "Bournemouth": "AFC Bournemouth",
    "Brentford": "Brentford FC",
    "Brighton": "Brighton & Hove Albion FC",
    "Burnley": "Burnley FC",
    "Chelsea": "Chelsea FC",
    "Crystal Palace": "Crystal Palace FC",
    "Everton": "Everton FC",
    "Fulham": "Fulham FC",
    "Ipswich": "Ipswich Town FC",
    "Leeds": "Leeds United FC",
    "Leicester": "Leicester City FC",
    "Liverpool": "Liverpool FC",
    "Luton": "Luton Town FC",
    "Man City": "Manchester City FC",
    "Man United": "Manchester United FC",
    "Newcastle": "Newcastle United FC",
    "Nott'm Forest": "Nottingham Forest FC",
    "Sheffield United": "Sheffield United FC",
    "Southampton": "Southampton FC",
    "Tottenham": "Tottenham Hotspur FC",
    "West Ham": "West Ham United FC",
    "Wolves": "Wolverhampton Wanderers FC",
}


def fetch_and_save():
    try:
        conn = get_connection()
    except psycopg2.OperationalError as e:
        print(f"Ошибка подключения к БД: {e}")
        return

    cur = conn.cursor()

    # === ЧАСТЬ 1: Загрузка ТЕКУЩЕГО сезона из API (без фильтра по году работает отлично) ===
    logger.info("Loading current season from API...")
    url_current = "https://api.football-data.org/v4/competitions/PL/matches"
    try:
        if not API_KEY:
            logger.warning("FOOTBALL_API_KEY is not set; skipping current season API fetch.")
            response = None
        else:
            response = requests.get(url_current, headers=HEADERS, timeout=15)
    except requests.RequestException as e:
        logger.error("Network error when requesting current season: %s", e)
        response = None

    if response is not None and response.status_code == 200:
        data = response.json()
        matches = data.get("matches", [])
        saved_api = 0
        for match in matches:
            if match.get("status") != "FINISHED":
                continue
            match_date = match["utcDate"]
            team_1 = match["homeTeam"]["name"]
            team_2 = match["awayTeam"]["name"]
            score_1 = match["score"]["fullTime"]["home"]
            score_2 = match["score"]["fullTime"]["away"]

            cur.execute(
                """
                INSERT INTO raw_matches (match_date, team_1, team_2, score_1, score_2)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """,
                (match_date, team_1, team_2, score_1, score_2),
            )
            saved_api += cur.rowcount
        logger.info("[API] Added/updated current matches: %d", saved_api)
    else:
        if response is None:
            logger.warning("[API] No response from API server (network issues or skipped).")
        else:
            logger.error("[API] Failed to fetch current season: HTTP %s", response.status_code)
            # Показываем тело ответа для диагностики, если есть
            try:
                logger.debug("Response body: %s", response.text[:1000])
            except Exception:
                pass

    # === ЧАСТЬ 2: Загрузка ИСТОРИЧЕСКИХ сезонов из бесплатного репозитория (22/23, 23/24, 24/25) ===
    csv_seasons = ["2223", "2324", "2425", "2526"]

    for season in csv_seasons:
        logger.info("Downloading archive season %s from football-data.co.uk...", season)
        csv_url = f"https://www.football-data.co.uk/mmz4281/{season}/E0.csv"

        try:
            res = requests.get(csv_url, timeout=15)
        except requests.RequestException as e:
            logger.error("Network error when downloading %s: %s", season, e)
            continue
        if res.status_code != 200:
            logger.error("Failed to download season %s: HTTP %s", season, res.status_code)
            continue

        # Читаем CSV напрямую в оперативную память через Pandas
        csv_data = pd.read_csv(io.StringIO(res.text))
        saved_csv = 0

        # Фильтруем пустые строки, если они есть в конце файла
        clean_rows = csv_data.dropna(
            subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"]
        )

        for _, row in clean_rows.iterrows():
            try:
                # Превращаем дату в ISO формат, понятный для PostgreSQL
                match_date = pd.to_datetime(row["Date"], dayfirst=True).strftime(
                    "%Y-%m-%d 00:00:00"
                )
            except:
                continue

            raw_home = str(row["HomeTeam"]).strip()
            raw_away = str(row["AwayTeam"]).strip()

            # Маппим имена к стандарту API
            team_1 = TEAM_MAPPING.get(raw_home, raw_home)
            team_2 = TEAM_MAPPING.get(raw_away, raw_away)

            score_1 = int(row["FTHG"])
            score_2 = int(row["FTAG"])

            cur.execute(
                """
                INSERT INTO raw_matches (match_date, team_1, team_2, score_1, score_2)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """,
                (match_date, team_1, team_2, score_1, score_2),
            )
            saved_csv += cur.rowcount

        logger.info("[ARCHIVE] Season %s imported: %d new rows", season, saved_csv)

    conn.commit()
    cur.close()
    conn.close()
    logger.info("Data collection complete (API + Archive).")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetch_and_save()
