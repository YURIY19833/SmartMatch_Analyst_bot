import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib


def train_football_model():
    try:
        df = pd.read_csv("sports_data_cleaned.csv")
    except FileNotFoundError:
        print("[ОШИБКА] Сначала запусти build_features.py")
        return

    print(f"Загружено {len(df)} матчей для обучения модели.")

    X = df[["home_pts_form", "away_pts_form", "home_gd_form", "away_gd_form"]]
    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("Обучение откалиброванной модели Random Forest (борьба с переобучением)...")
    # Ограничиваем глубину до 4, ставим минимальное количество объектов в листе = 3
    model = RandomForestClassifier(
        n_estimators=250, max_depth=4, min_samples_leaf=3, random_state=42
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print("\n=============================================")
    print(f" СТАБИЛЬНАЯ ТОЧНОСТЬ МОДЕЛИ (Accuracy): {accuracy:.2%}")
    print("=============================================")
    print("\nДетальный отчет по классам:")
    print(classification_report(y_test, y_pred))

    joblib.dump(model, "football_model.pkl")
    print("\n[УСПЕХ] Новая откалиброванная модель сохранена в football_model.pkl!")


if __name__ == "__main__":
    train_football_model()
