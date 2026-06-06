import requests
import psycopg2
import pandas as pd
import io
from db_config import DB_CONFIG

API_KEY = "b740a1b91b624bd9b9e6be752ce6898f"
HEADERS = {"X-Auth-Token": API_KEY}

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
        conn = psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        print(f"Ошибка подключения к БД: {e}")
        return

    cur = conn.cursor()

    # === ЧАСТЬ 1: Загрузка ТЕКУЩЕГО сезона из API (без фильтра по году работает отлично) ===
    print("Загрузка текущего сезона из API...")
    url_current = "https://api.football-data.org/v4/competitions/PL/matches"
    response = requests.get(url_current, headers=HEADERS)

    if response.status_code == 200:
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
        print(f"[API] Добавлено/обновлено актуальных матчей: {saved_api}")
    else:
        print(
            f"[ОШИБКА API] Не удалось загрузить текущий сезон: Код {response.status_code}"
        )

    # === ЧАСТЬ 2: Загрузка ИСТОРИЧЕСКИХ сезонов из бесплатного репозитория (22/23, 23/24, 24/25) ===
    csv_seasons = ["2223", "2324", "2425", "2526"]

    for season in csv_seasons:
        print(f"Загрузка архивного сезона {season} из футбольного репозитория...")
        csv_url = f"https://www.football-data.co.uk/mmz4281/{season}/E0.csv"

        res = requests.get(csv_url)
        if res.status_code != 200:
            print(f"[ОШИБКА] Не удалось скачать данные для сезона {season}")
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

        print(
            f"[АРХИВ] Для сезона {season} успешно импортировано новых матчей: {saved_csv}"
        )

    conn.commit()
    cur.close()
    conn.close()
    print("\n--- [УСПЕХ] Сбор всех данных (API + Архив) успешно завершен! ---")


if __name__ == "__main__":
    fetch_and_save()
