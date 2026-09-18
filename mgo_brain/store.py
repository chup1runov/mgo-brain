from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Lock

from .models import Event, StartEvent, TripSummary


class Store:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "mgo_brain.sqlite3"
        self.trip_dir = self.data_dir / "trips"
        self.trip_dir.mkdir(exist_ok=True)
        self._lock = Lock()
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              timestamp TEXT NOT NULL,
              severity TEXT NOT NULL,
              code TEXT NOT NULL,
              message TEXT NOT NULL,
              data_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS starts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              started_at TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS trips (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              started_at TEXT NOT NULL,
              ended_at TEXT,
              payload_json TEXT NOT NULL
            );
            """)

    def add_event(self, event: Event) -> int:
        with self._lock, self._connect() as c:
            cur = c.execute("INSERT INTO events(timestamp,severity,code,message,data_json) VALUES(?,?,?,?,?)",
                            (event.timestamp.isoformat(), event.severity.value, event.code, event.message, json.dumps(event.data)))
            return int(cur.lastrowid)

    def add_start(self, start: StartEvent) -> int:
        with self._lock, self._connect() as c:
            cur = c.execute("INSERT INTO starts(started_at,payload_json) VALUES(?,?)",
                            (start.started_at.isoformat(), start.model_dump_json()))
            return int(cur.lastrowid)

    def add_trip(self, trip: TripSummary) -> int:
        with self._lock, self._connect() as c:
            cur = c.execute("INSERT INTO trips(started_at,ended_at,payload_json) VALUES(?,?,?)",
                            (trip.started_at.isoformat(), trip.ended_at.isoformat() if trip.ended_at else None, trip.model_dump_json()))
            return int(cur.lastrowid)

    def list_events(self, limit: int = 100) -> list[dict]:
        with self._connect() as c:
            rows = c.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) | {"data": json.loads(r["data_json"])} for r in rows]

    def list_starts(self, limit: int = 100) -> list[dict]:
        with self._connect() as c:
            rows = c.execute("SELECT * FROM starts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [json.loads(r["payload_json"]) | {"id": r["id"]} for r in rows]

    def list_trips(self, limit: int = 100) -> list[dict]:
        with self._connect() as c:
            rows = c.execute("SELECT * FROM trips ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [json.loads(r["payload_json"]) | {"id": r["id"]} for r in rows]
