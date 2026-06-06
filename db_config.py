"""Конфигурация БД для проекта.

Этот модуль не должен иметь побочных эффектов при импорте (не вызывать
`connect()` автоматически). Экспортируем `DB_CONFIG` и вспомогательную
функцию `get_connection()` для явного создания соединения.
"""

DB_CONFIG = {
	"dbname": "sports_db",
	"user": "user",
	"password": "password",
	"host": "localhost",
	"port": "5432",
}


def get_connection():
	"""Возвращает новое соединение psycopg2.

	Поведение:
	- Если задана переменная окружения `DATABASE_URL`, используется она (DSN).
	- Иначе используются параметры `DB_CONFIG`, с возможностью переопределения
	  через окружение `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.
	"""
	import os
	import psycopg2

	dsn = os.environ.get("DATABASE_URL")
	if dsn:
		return psycopg2.connect(dsn)

	# Собираем параметры, позволяя переопределения через окружение
	params = DB_CONFIG.copy()
	if os.environ.get("DB_NAME"):
		params["dbname"] = os.environ.get("DB_NAME")
	if os.environ.get("DB_USER"):
		params["user"] = os.environ.get("DB_USER")
	if os.environ.get("DB_PASSWORD"):
		params["password"] = os.environ.get("DB_PASSWORD")
	if os.environ.get("DB_HOST"):
		params["host"] = os.environ.get("DB_HOST")
	if os.environ.get("DB_PORT"):
		params["port"] = os.environ.get("DB_PORT")

	return psycopg2.connect(**params)