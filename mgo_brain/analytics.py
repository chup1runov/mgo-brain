from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _duckdb():
    try:
        import duckdb  # type: ignore
    except ImportError as exc:
        raise RuntimeError("DuckDB analytics dependency is not installed. Install mgo-brain[analytics].") from exc
    return duckdb


def _sql_string(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


class HistoricalAnalytics:
    """Parquet/DuckDB layer kept separate from the real-time diagnostic path."""

    def __init__(self, trip_dir: Path):
        self.trip_dir = Path(trip_dir)
        self.trip_dir.mkdir(parents=True, exist_ok=True)

    def available(self) -> bool:
        try:
            _duckdb()
            return True
        except RuntimeError:
            return False

    def finalize_trip(self, jsonl_path: str | Path | None) -> str | None:
        if not jsonl_path:
            return None
        src = Path(jsonl_path)
        if not src.exists() or src.stat().st_size == 0:
            return None
        if not self.available():
            return str(src)

        duckdb = _duckdb()
        dst = src.with_suffix(".parquet")
        con = duckdb.connect()
        try:
            con.execute(
                f"COPY (SELECT * FROM read_json_auto({_sql_string(src)}, format='newline_delimited')) "
                f"TO {_sql_string(dst)} (FORMAT PARQUET, COMPRESSION ZSTD)"
            )
        finally:
            con.close()
        src.unlink(missing_ok=True)
        return str(dst)

    def parquet_files(self) -> list[Path]:
        return sorted(self.trip_dir.glob("*.parquet"))

    def summary(self) -> dict[str, Any]:
        files = self.parquet_files()
        if not files:
            return {"available": self.available(), "trip_files": 0, "samples": 0, "aggregates": {}}
        if not self.available():
            return {"available": False, "trip_files": len(files), "samples": None, "aggregates": {}}

        duckdb = _duckdb()
        glob = self.trip_dir / "*.parquet"
        con = duckdb.connect()
        try:
            row = con.execute(
                f"""
                SELECT
                  count(*)::BIGINT AS samples,
                  avg(try_cast(vehicle_speed_kmh AS DOUBLE)) AS avg_speed_kmh,
                  max(try_cast(vehicle_speed_kmh AS DOUBLE)) AS max_speed_kmh,
                  max(try_cast(coolant_temp_c AS DOUBLE)) AS max_coolant_c,
                  max(try_cast(oil_temp_c AS DOUBLE)) AS max_oil_temp_c,
                  min(CASE WHEN try_cast(engine_rpm AS DOUBLE) >= 400 THEN try_cast(oil_pressure_bar AS DOUBLE) END) AS min_running_oil_pressure_bar,
                  avg(CASE WHEN try_cast(engine_rpm AS DOUBLE) >= 400 THEN try_cast(battery_voltage_v AS DOUBLE) END) AS avg_running_voltage_v,
                  avg(abs(try_cast(cvt_ratio_deviation_pct AS DOUBLE))) AS avg_abs_cvt_deviation_pct,
                  max(greatest(try_cast(cvt_temp_primary_c AS DOUBLE), try_cast(cvt_temp_secondary_c AS DOUBLE))) AS max_cvt_temp_c
                FROM read_parquet({_sql_string(glob)}, union_by_name=true)
                """
            ).fetchone()
            cols = [d[0] for d in con.description]
            aggregates = dict(zip(cols, row)) if row else {}
        finally:
            con.close()
        samples = int(aggregates.pop("samples", 0) or 0)
        return {"available": True, "trip_files": len(files), "samples": samples, "aggregates": aggregates}

    def inspect_trip(self, parquet_path: str | Path) -> dict[str, Any]:
        path = Path(parquet_path)
        if path.suffix != ".parquet" or not path.exists() or not self.available():
            return {}
        duckdb = _duckdb()
        con = duckdb.connect()
        try:
            row = con.execute(
                f"""
                SELECT
                  count(*)::BIGINT AS samples,
                  avg(try_cast(vehicle_speed_kmh AS DOUBLE)) AS avg_speed_kmh,
                  max(try_cast(vehicle_speed_kmh AS DOUBLE)) AS max_speed_kmh,
                  max(try_cast(coolant_temp_c AS DOUBLE)) AS max_coolant_c,
                  max(try_cast(oil_temp_c AS DOUBLE)) AS max_oil_temp_c,
                  min(CASE WHEN try_cast(engine_rpm AS DOUBLE) >= 400 THEN try_cast(oil_pressure_bar AS DOUBLE) END) AS min_running_oil_pressure_bar,
                  avg(CASE WHEN try_cast(engine_rpm AS DOUBLE) >= 400 THEN try_cast(battery_voltage_v AS DOUBLE) END) AS avg_running_voltage_v,
                  avg(abs(try_cast(cvt_ratio_deviation_pct AS DOUBLE))) AS avg_abs_cvt_deviation_pct,
                  max(greatest(try_cast(cvt_temp_primary_c AS DOUBLE), try_cast(cvt_temp_secondary_c AS DOUBLE))) AS max_cvt_temp_c
                FROM read_parquet({_sql_string(path)})
                """
            ).fetchone()
            cols = [d[0] for d in con.description]
            return dict(zip(cols, row)) if row else {}
        finally:
            con.close()


def telemetry_row(state) -> dict[str, Any]:
    """Flatten selected canonical signals into stable analytics columns."""
    v = state.value
    return {
        "timestamp": state.timestamp.isoformat(),
        "mode": state.mode.value,
        "signal_metadata_json": json.dumps({name: {"quality": r.quality.value, "source": r.source, "timestamp": r.timestamp.isoformat()} for name, r in state.signals.items()}, separators=(",", ":")),
        "vehicle_speed_kmh": _num(v("vehicle.speed")),
        "vehicle_speed_gps_kmh": _num(v("vehicle.speed_gps")),
        "engine_rpm": _num(v("engine.rpm")),
        "coolant_temp_c": _num(v("engine.coolant_temp")),
        "oil_temp_c": _num(v("engine.oil_temp")),
        "oil_pressure_bar": _num(v("engine.oil_pressure")),
        "battery_voltage_v": _num(v("electrical.battery_voltage")),
        "battery_current_a": _num(v("electrical.battery_current")),
        "battery_soc_pct": _num(v("electrical.battery_soc")),
        "cvt_ratio": _num(v("transmission.cvt_ratio")),
        "cvt_ratio_deviation_pct": _num(v("transmission.cvt_ratio_deviation")),
        "cvt_temp_primary_c": _num(v("transmission.cvt_temp_primary")),
        "cvt_temp_secondary_c": _num(v("transmission.cvt_temp_secondary")),
        "fuel_level_pct": _num(v("fuel.level")),
        "ambient_temp_c": _num(v("environment.ambient_temp")),
    }


def write_row(file_obj, state) -> None:
    file_obj.write(json.dumps(telemetry_row(state), ensure_ascii=False) + "\n")


def _num(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
