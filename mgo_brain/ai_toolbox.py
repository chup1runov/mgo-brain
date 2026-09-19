from __future__ import annotations

from typing import Any, Callable

from .models import SignalQuality
from .ai_models import ToolSpec


UNUSABLE = {SignalQuality.STALE, SignalQuality.MISSING, SignalQuality.INVALID, SignalQuality.UNVERIFIED, SignalQuality.SUSPECT}


class MGOToolbox:
    """Read-only evidence tools for Ask MGO.

    These functions expose normalized/derived evidence only. No tool controls the vehicle.
    """

    def __init__(self, service):
        self.service = service

    def specs(self) -> list[ToolSpec]:
        return [
            ToolSpec(name="get_live_state", description="Current normalized vehicle state with signal quality/source."),
            ToolSpec(name="get_engine_health", description="Current engine subsystem health and related live signals."),
            ToolSpec(name="get_cvt_health", description="Current CVT health, temperatures, ratio and historical baseline."),
            ToolSpec(name="get_battery_health", description="Current electrical/battery health and start-voltage baselines."),
            ToolSpec(name="get_start_history", description="Recent engine start events and start-related baselines.", parameters={"limit": {"type": "integer", "default": 10}}),
            ToolSpec(name="get_recent_trips", description="Recent trip summaries.", parameters={"limit": {"type": "integer", "default": 5}}),
            ToolSpec(name="compare_trips", description="Compare two stored trip summaries.", parameters={"trip_a": {"type": "integer"}, "trip_b": {"type": "integer"}}),
            ToolSpec(name="get_fault_events", description="Recent persisted alerts/fault events.", parameters={"limit": {"type": "integer", "default": 30}}),
            ToolSpec(name="get_service_plan", description="Configured maintenance/service intervals."),
            ToolSpec(name="get_baselines", description="Reference and rolling baseline statistics."),
            ToolSpec(name="get_source_status", description="Configured data sources and freshness timeout."),
        ]

    def execute(self, name: str, **kwargs) -> Any:
        methods: dict[str, Callable[..., Any]] = {
            "get_live_state": self.get_live_state,
            "get_engine_health": self.get_engine_health,
            "get_cvt_health": self.get_cvt_health,
            "get_battery_health": self.get_battery_health,
            "get_start_history": self.get_start_history,
            "get_recent_trips": self.get_recent_trips,
            "compare_trips": self.compare_trips,
            "get_fault_events": self.get_fault_events,
            "get_service_plan": self.get_service_plan,
            "get_baselines": self.get_baselines,
            "get_source_status": self.get_source_status,
        }
        if name not in methods:
            raise KeyError(f"Unknown Ask MGO tool: {name}")
        return methods[name](**kwargs)

    def get_live_state(self) -> dict[str, Any]:
        state = self.service.state
        return {
            "timestamp": state.timestamp.isoformat(),
            "mode": state.mode.value,
            "signals": {
                name: {
                    "value": reading.value,
                    "unit": reading.unit,
                    "quality": reading.quality.value,
                    "source": reading.source,
                    "timestamp": reading.timestamp.isoformat(),
                }
                for name, reading in state.signals.items()
            },
        }

    def get_engine_health(self) -> dict[str, Any]:
        summary = self.service.health_summary()
        subsystem = _subsystem(summary, "ENGINE")
        names = (
            "engine.rpm",
            "engine.coolant_temp",
            "engine.oil_temp",
            "engine.oil_pressure",
            "engine.oil_warning",
            "engine.overheat_warning",
            "engine.glow_active",
            "engine.glow_current",
            "engine.starter_active",
            "engine.starter_current",
        )
        return {
            "health": subsystem,
            "signals": self._signals(names),
            "baselines": _pick(self.service.baselines.summary(), (
                "starter_duration_s", "cranking_rpm", "max_coolant_c",
                "max_oil_temp_c", "min_oil_pressure_bar",
            )),
        }

    def get_cvt_health(self) -> dict[str, Any]:
        summary = self.service.health_summary()
        return {
            "health": _subsystem(summary, "CVT"),
            "signals": self._signals((
                "transmission.gear",
                "transmission.cvt_ratio",
                "transmission.cvt_ratio_deviation",
                "transmission.cvt_temp_primary",
                "transmission.cvt_temp_secondary",
                "transmission.gearbox_temp",
                "vehicle.speed",
                "engine.rpm",
            )),
            "baselines": _pick(self.service.baselines.summary(), (
                "avg_cvt_ratio_deviation_pct", "max_cvt_temp_c",
            )),
        }

    def get_battery_health(self) -> dict[str, Any]:
        summary = self.service.health_summary()
        return {
            "health": _subsystem(summary, "ELECTRICAL"),
            "signals": self._signals((
                "electrical.battery_voltage",
                "electrical.battery_current",
                "electrical.battery_soc",
                "electrical.alternator_voltage",
                "engine.glow_current",
                "engine.starter_current",
            )),
            "baselines": _pick(self.service.baselines.summary(), (
                "min_crank_voltage_v", "avg_running_voltage_v", "starter_duration_s",
            )),
        }

    def get_start_history(self, limit: int = 10) -> dict[str, Any]:
        limit = min(max(int(limit), 1), 100)
        return {
            "starts": self.service.store.list_starts(limit),
            "baselines": _pick(self.service.baselines.summary(), (
                "starter_duration_s", "min_crank_voltage_v", "cranking_rpm",
            )),
        }

    def get_recent_trips(self, limit: int = 5) -> dict[str, Any]:
        limit = min(max(int(limit), 1), 50)
        return {"trips": self.service.store.list_trips(limit)}

    def compare_trips(self, trip_a: int, trip_b: int) -> dict[str, Any]:
        result = self.service.compare_trips(int(trip_a), int(trip_b))
        return result or {"error": "trip_not_found"}

    def get_fault_events(self, limit: int = 30) -> dict[str, Any]:
        rows = self.service.store.list_events(min(max(int(limit), 1), 200))
        selected = [
            row for row in rows
            if str(row.get("code", "")).startswith("ALERT_")
            or "FAULT" in str(row.get("code", ""))
            or "WARNING" in str(row.get("code", ""))
        ]
        return {"events": selected[:limit]}

    def get_service_plan(self) -> dict[str, Any]:
        import json
        from .main_paths import maintenance_path
        path = maintenance_path()
        return json.loads(path.read_text(encoding="utf-8"))

    def get_baselines(self) -> dict[str, Any]:
        return self.service.baselines.summary()

    def get_source_status(self) -> dict[str, Any]:
        return self.service.source_status()

    def _signals(self, names) -> dict[str, Any]:
        result = {}
        for name in names:
            reading = self.service.state.signals.get(name)
            if reading is None:
                result[name] = {"value": None, "quality": "MISSING", "source": None}
            else:
                result[name] = {
                    "value": reading.value,
                    "unit": reading.unit,
                    "quality": reading.quality.value,
                    "source": reading.source,
                    "usable": reading.usable,
                }
        return result


def _subsystem(summary: dict[str, Any], name: str) -> dict[str, Any]:
    return next(
        (item for item in summary.get("subsystems", []) if item.get("subsystem") == name),
        {"subsystem": name, "status": "UNKNOWN", "reasons": ["Subsystem not available."]},
    )


def _pick(mapping: dict[str, Any], names) -> dict[str, Any]:
    return {name: mapping[name] for name in names if name in mapping}
