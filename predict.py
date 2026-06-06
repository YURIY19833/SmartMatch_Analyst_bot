import psycopg2
import joblib
import pandas as pd

# Тянем настройки подключения прямо из твоего рабочего конфига, который использует get_data.py
from db_config import DB_CONFIG


def get_team_features(team_name, cur):
    """Достает метрики команды из вьюхи v_team_analytics (регистронезависимо)"""
    query = """
        SELECT avg_goals_scored, avg_goals_conceded, win_rate, 
               avg_goals_scored_home, avg_goals_conceded_home,
               avg_goals_scored_away, avg_goals_conceded_away
        FROM v_team_analytics 
        WHERE LOWER(team) = LOWER(%s);
    """
    cur.execute(query, (team_name,))
    row = cur.fetchone()

    # Если пользователь забыл написать "FC" в конце, пробуем добавить автоматически
    if not row and not team_name.lower().endswith("fc"):
        cur.execute(query, (team_name + " FC",))
        row = cur.fetchone()

    if not row:
        raise ValueError(
            f"❌ Команда '{team_name}' не найдена в базе данных. Проверь название."
        )

    return {
        "avg_scored": row[0],
        "avg_conceded": row[1],
        "win_rate": row[2],
        "avg_scored_home": row[3],
        "avg_conceded_home": row[4],
        "avg_scored_away": row[5],
        "avg_conceded_away": row[6],
    }


def predict_match(home_team, away_team):
    try:
        model = joblib.load("football_model.pkl")
    except FileNotFoundError:
        return "❌ Ошибка: файл модели 'football_model.pkl' не найден."

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        home_features = get_team_features(home_team, cur)
        away_features = get_team_features(away_team, cur)
    except psycopg2.OperationalError as e:
        return (
            f"❌ Ошибка подключения к базе данных. Проверь db_config.py.\nДетали: {e}"
        )
    except ValueError as e:
        return str(e)
    finally:
        if "cur" in locals():
            cur.close()
        if "conn" in locals():
            conn.close()

    # Формируем датафрейм в порядке, который ожидает модель
    match_data = pd.DataFrame(
        [
            {
                "home_pts_form": home_features["win_rate"] * 3,
                "away_pts_form": away_features["win_rate"] * 3,
                "home_gd_form": home_features["avg_scored_home"]
                - home_features["avg_conceded_home"],
                "away_gd_form": away_features["avg_scored_away"]
                - away_features["avg_conceded_away"],
            }
        ]
    )

    if hasattr(model, "feature_names_in_"):
        match_data = match_data[model.feature_names_in_]

    prediction = model.predict(match_data)[0]
    probabilities = model.predict_proba(match_data)[0]

    prob_home_win = probabilities[1] * 100
    prob_other = probabilities[0] * 100

    result = f"\nАНАЛИЗ МАТЧА: {home_team} vs {away_team}\n"
    result += "---\n"
    result += f"Вероятность победы {home_team} (хозяева): {prob_home_win:.1f}%\n"
    result += f"Вероятность X2 (ничья или победа {away_team}): {prob_other:.1f}%\n"
    result += "---\n"

    if prediction == 1:
        result += f"Рекомендация: ставка на победу хозяев ({home_team})\n"
    else:
        result += "Рекомендация: ставка на не-проигрыш гостей (X2)\n"

    return result


if __name__ == "__main__":
    print("🤖 Инференс-движок успешно подключен к db_config!")
    print("Для выхода из программы в любой момент введи 'exit'.\n")

    while True:
        print("🟢 Свежий прогноз:")
        home = input("Введите команду хозяев (например, liverpool): ").strip()
        if home.lower() == "exit":
            break

        away = input("Введите команду гостей (например, chelsea): ").strip()
        if away.lower() == "exit":
            break

        if not home or not away:
            print("⚠️ Названия команд не могут быть пустыми!")
            continue

        print(predict_match(home, away))
        print("-" * 50)
