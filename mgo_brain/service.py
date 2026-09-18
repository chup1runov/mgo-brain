from __future__ import annotations

import asyncio
from pathlib import Path

from .alerts import AlertManager, AlertStatus
from .baseline import BaselineManager
from .detectors import StartDetector, TripDetector
from .faults import FaultScenario
from .health import HealthEngine
from .models import AIContext, Event, Severity, VehicleState
from .rules import RulesEngine
from .simulator import MGOSimulator
from .store import Store


class MGOBrainService:
    def __init__(self, data_dir: Path):
        self.store = Store(data_dir)
        self.source = MGOSimulator(hz=5)
        self.rules = RulesEngine()
        self.alerts = AlertManager(clear_after_s=1.0)
        self.health = HealthEngine()
        self.baselines = BaselineManager()
        self.start_detector = StartDetector()
        self.trip_detector = TripDetector(self.store.trip_dir)
        self.state = VehicleState()
        self._subscribers: set[asyncio.Queue] = set()
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
            self.process_state(state)
            await self._publish(state)

    def process_state(self, state: VehicleState) -> None:
        """Process one normalized vehicle state.

        Kept synchronous so the diagnostic pipeline can be tested without an event loop.
        """
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

        transitions = self.alerts.update(self.rules.evaluate(state), state.timestamp)
        for transition in transitions:
            record = transition.alert
            if transition.transition == AlertStatus.ACTIVE:
                event = Event(
                    timestamp=state.timestamp,
                    severity=record.severity,
                    code=f"ALERT_ACTIVE:{record.code}",
                    message=record.message,
                    data=record.model_dump(mode="json"),
                )
            else:
                event = Event(
                    timestamp=state.timestamp,
                    severity=Severity.INFO,
                    code=f"ALERT_CLEARED:{record.code}",
                    message=f"Alert cleared: {record.code}",
                    data=record.model_dump(mode="json"),
                )
            event.id = self.store.add_event(event)

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

        active_events = [
            Event(
                timestamp=alert.last_seen,
                severity=alert.severity,
                code=alert.code,
                message=alert.message,
                data=alert.data,
            )
            for alert in self.alerts.active()
        ]
        return AIContext(
            current_state=self.state,
            active_alerts=active_events,
            recent_trip=recent_trip,
            baseline_deviations=deviations,
            maintenance_due=[],
        )

    def health_summary(self):
        active = self.alerts.active()
        summary = self.health.summary(self.state, active)
        summary.update({
            "mode": self.state.mode,
            "active_alerts": [a.model_dump(mode="json") for a in active],
            "baseline": self.baselines.summary(),
            "simulator_faults": self.source.faults.names(),
        })
        return summary

    def alert_snapshot(self):
        return self.alerts.snapshot()

    def fault_catalog(self):
        return self.source.faults.catalog()

    def enable_fault(self, fault: FaultScenario | str):
        self.source.faults.enable(fault)
        return self.fault_catalog()

    def disable_fault(self, fault: FaultScenario | str):
        self.source.faults.disable(fault)
        return self.fault_catalog()

    def clear_faults(self):
        self.source.faults.clear()
        return self.fault_catalog()
