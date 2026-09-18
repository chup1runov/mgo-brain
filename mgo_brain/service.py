from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from .alerts import AlertManager, AlertStatus
from .analytics import HistoricalAnalytics
from .baseline import BaselineManager
from .detectors import StartDetector, TripDetector
from .faults import FaultScenario
from .health import HealthEngine
from .models import AIContext, Event, Severity, TripSummary, VehicleState
from .reports import PostTripReportEngine
from .rules import RulesEngine
from .simulator import MGOSimulator
from .store import Store


SEVERITY_RANK = {
    Severity.INFO: 0,
    Severity.WATCH: 1,
    Severity.ATTENTION: 2,
    Severity.CRITICAL: 3,
}


class MGOBrainService:
    def __init__(self, data_dir: Path):
        self.store = Store(data_dir)
        self.source = MGOSimulator(hz=5)
        self.rules = RulesEngine()
        self.alerts = AlertManager(clear_after_s=1.0)
        self.health = HealthEngine()
        self.baselines = BaselineManager()
        self.analytics = HistoricalAnalytics(self.store.trip_dir)
        self.report_engine = PostTripReportEngine()
        self.start_detector = StartDetector()
        self.trip_detector = TripDetector(self.store.trip_dir)
        self.state = VehicleState()
        self._subscribers: set[asyncio.Queue] = set()
        self.task: asyncio.Task | None = None
        self._start_baseline_eligible = True
        self._trip_baseline_eligible = True
        self._trip_worst_severity = Severity.INFO
        self._rebuild_baselines()

    def _rebuild_baselines(self):
        self.baselines.rebuild(self.store.list_starts(10000), self.store.list_trips(10000))

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
        """Process one normalized vehicle state without requiring an event loop."""
        self.state = state
        rule_events = self.rules.evaluate(state)
        severe_now = [e for e in rule_events if SEVERITY_RANK[e.severity] >= SEVERITY_RANK[Severity.ATTENTION]]

        start_was_active = self.start_detector.active is not None
        start_event = self.start_detector.update(state)
        start_is_active = self.start_detector.active is not None
        if not start_was_active and start_is_active:
            self._start_baseline_eligible = True
        if severe_now and (start_was_active or start_is_active):
            self._start_baseline_eligible = False
        if start_event:
            start_event.baseline_eligible = self._start_baseline_eligible
            start_event.id = self.store.add_start(start_event)
            start_anomalies = self.baselines.start_anomalies(start_event)
            self.baselines.add_start_event(start_event)
            event = Event(
                severity=Severity.INFO,
                code="ENGINE_START",
                message="Engine start completed.",
                data={**start_event.model_dump(mode="json"), "historical_anomalies": start_anomalies},
            )
            event.id = self.store.add_event(event)
            self._start_baseline_eligible = True

        trip_was_active = self.trip_detector.active is not None
        trip = self.trip_detector.update(state)
        trip_is_active = self.trip_detector.active is not None
        if not trip_was_active and trip_is_active:
            self._trip_baseline_eligible = True
            self._trip_worst_severity = Severity.INFO
        if trip_was_active or trip_is_active:
            for event in rule_events:
                if SEVERITY_RANK[event.severity] > SEVERITY_RANK[self._trip_worst_severity]:
                    self._trip_worst_severity = event.severity
            if severe_now:
                self._trip_baseline_eligible = False

        if trip:
            trip.baseline_eligible = self._trip_baseline_eligible
            trip.diagnostic_status = self._trip_worst_severity.value if self._trip_worst_severity != Severity.INFO else "NORMAL"
            trip.telemetry_path = self.analytics.finalize_trip(trip.telemetry_path)
            anomalies = self.baselines.trip_anomalies(trip)
            trip.id = self.store.add_trip(trip)
            report = self.report_engine.generate(trip, anomalies, trip.baseline_eligible)
            self.store.add_report(report)
            self.baselines.add_trip(trip)
            event = Event(
                severity=Severity.INFO,
                code="TRIP_COMPLETE",
                message="Trip completed.",
                data={
                    **trip.model_dump(mode="json"),
                    "report_status": report.status,
                    "historical_anomalies": anomalies,
                },
            )
            event.id = self.store.add_event(event)
            self._trip_baseline_eligible = True
            self._trip_worst_severity = Severity.INFO

        transitions = self.alerts.update(rule_events, state.timestamp)
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
        recent_trip = TripSummary.model_validate(trips[0]) if trips else None
        deviations = [{"metric": name, **metric.stats()} for name, metric in self.baselines.metrics.items()]
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

    def analytics_summary(self):
        return self.analytics.summary()

    def compare_trips(self, trip_a: int, trip_b: int) -> dict[str, Any] | None:
        a_raw = self.store.get_trip(trip_a)
        b_raw = self.store.get_trip(trip_b)
        if not a_raw or not b_raw:
            return None
        a = TripSummary.model_validate(a_raw)
        b = TripSummary.model_validate(b_raw)
        metrics = [
            "distance_km", "duration_s", "avg_speed_kmh", "max_speed_kmh",
            "max_coolant_c", "max_oil_temp_c", "min_oil_pressure_bar",
            "avg_running_voltage_v", "avg_cvt_ratio_deviation_pct", "max_cvt_temp_c",
        ]
        comparison: dict[str, Any] = {}
        for name in metrics:
            av = getattr(a, name)
            bv = getattr(b, name)
            if av is None or bv is None:
                comparison[name] = {"a": av, "b": bv, "delta": None, "delta_pct": None}
                continue
            delta = bv - av
            pct = delta / abs(av) * 100.0 if abs(av) > 1e-12 else None
            comparison[name] = {"a": av, "b": bv, "delta": delta, "delta_pct": pct}
        return {
            "trip_a": a.model_dump(mode="json"),
            "trip_b": b.model_dump(mode="json"),
            "comparison": comparison,
        }
