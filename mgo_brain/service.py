from __future__ import annotations

import asyncio
from collections import deque
from pathlib import Path

from .baseline import BaselineManager
from .detectors import StartDetector, TripDetector
from .models import AIContext, Event, Severity, VehicleState
from .rules import RulesEngine
from .simulator import MGOSimulator
from .store import Store


class MGOBrainService:
    def __init__(self, data_dir: Path):
        self.store = Store(data_dir)
        self.source = MGOSimulator(hz=5)
        self.rules = RulesEngine()
        self.baselines = BaselineManager()
        self.start_detector = StartDetector()
        self.trip_detector = TripDetector(self.store.trip_dir)
        self.state = VehicleState()
        self.active_alerts: deque[Event] = deque(maxlen=50)
        self._subscribers: set[asyncio.Queue] = set()
        self._seen_rule_keys: dict[str, float] = {}
        self.task: asyncio.Task | None = None

    async def start(self):
        if self.task is None:
            self.task = asyncio.create_task(self._loop())

    async def stop(self):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

    async def _loop(self):
        async for state in self.source.stream():
            self.state = state

            start = self.start_detector.update(state)
            if start:
                start.id = self.store.add_start(start)
                self.baselines.add_start(start.starter_duration_s, start.min_crank_voltage_v)
                event = Event(severity=Severity.INFO, code="ENGINE_START", message="Engine start completed.", data=start.model_dump(mode="json"))
                event.id = self.store.add_event(event)

            trip = self.trip_detector.update(state)
            if trip:
                trip.id = self.store.add_trip(trip)
                event = Event(severity=Severity.INFO, code="TRIP_COMPLETE", message="Trip completed.", data=trip.model_dump(mode="json"))
                event.id = self.store.add_event(event)

            for event in self.rules.evaluate(state):
                key = event.code
                # Prototype de-duplication: do not persist identical rule every 200 ms.
                now_s = state.timestamp.timestamp()
                if now_s - self._seen_rule_keys.get(key, 0) >= 15:
                    event.id = self.store.add_event(event)
                    self._seen_rule_keys[key] = now_s
                    self.active_alerts.appendleft(event)

            await self._publish(state)

    async def _publish(self, state: VehicleState):
        dead = []
        payload = state.model_dump(mode="json")
        for q in self._subscribers:
            try:
                if q.full():
                    q.get_nowait()
                q.put_nowait(payload)
            except Exception:
                dead.append(q)
        for q in dead:
            self._subscribers.discard(q)

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=2)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self._subscribers.discard(q)

    def ai_context(self) -> AIContext:
        trips = self.store.list_trips(1)
        recent_trip = None
        if trips:
            from .models import TripSummary
            recent_trip = TripSummary.model_validate(trips[0])
        deviations = []
        for name, metric in self.baselines.metrics.items():
            stats = metric.stats()
            deviations.append({"metric": name, **stats})
        return AIContext(
            current_state=self.state,
            active_alerts=list(self.active_alerts)[:10],
            recent_trip=recent_trip,
            baseline_deviations=deviations,
            maintenance_due=[],
        )

    def health_summary(self):
        critical = [e for e in self.active_alerts if e.severity == Severity.CRITICAL]
        attention = [e for e in self.active_alerts if e.severity == Severity.ATTENTION]
        watch = [e for e in self.active_alerts if e.severity == Severity.WATCH]
        overall = "CRITICAL" if critical else "ATTENTION" if attention else "WATCH" if watch else "NORMAL"
        return {
            "overall": overall,
            "mode": self.state.mode,
            "active_alerts": [e.model_dump(mode="json") for e in list(self.active_alerts)[:10]],
            "baseline": self.baselines.summary(),
        }
