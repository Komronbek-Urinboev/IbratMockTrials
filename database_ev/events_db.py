import sqlite3

DB_PATH = "database_ev/events.db"


def init_events_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city_ru TEXT,
            city_en TEXT,
            city_uz TEXT,
            date TEXT,
            time TEXT,
            location_ru TEXT,
            location_en TEXT,
            location_uz TEXT,
            group_ru TEXT,
            group_en TEXT,
            group_uz TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_event(city_ru, city_en, city_uz, date, time,
              location_ru, location_en, location_uz,
              group_ru, group_en, group_uz):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO events (
            city_ru, city_en, city_uz, date, time,
            location_ru, location_en, location_uz,
            group_ru, group_en, group_uz
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (city_ru, city_en, city_uz, date, time,
          location_ru, location_en, location_uz,
          group_ru, group_en, group_uz))

    event_id = cur.lastrowid  # <-- берём ID добавленного события
    conn.commit()
    conn.close()
    return event_id  # <-- возвращаем ID


def get_events():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM events ORDER BY date, time")
    events = cur.fetchall()
    conn.close()
    return [dict(row) for row in events]


def delete_event(event_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM events WHERE id = ?", (event_id,))
    deleted = cur.rowcount  # <-- проверка, удалилось ли что-то
    conn.commit()
    conn.close()
    return deleted > 0
