from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import PostTripReport, TripSummary


class PostTripReportEngine:
    def generate(self, trip: TripSummary, anomalies: list[dict[str, Any]], eligible_for_baseline: bool) -> PostTripReport:
        findings: list[str] = []
        notable = [a for a in anomalies if a.get("status") not in {None, "NORMAL", "UNQUALIFIED"}]

        if trip.max_coolant_c is not None:
            findings.append(f"Peak coolant temperature: {trip.max_coolant_c:.1f} °C")
        if trip.min_oil_pressure_bar is not None:
            findings.append(f"Minimum running oil pressure: {trip.min_oil_pressure_bar:.2f} bar")
        if trip.max_cvt_temp_c is not None:
            findings.append(f"Peak CVT temperature: {trip.max_cvt_temp_c:.1f} °C")
        if notable:
            findings.append(f"Historical model flagged {len(notable)} metric(s) outside normal baseline behavior.")
        elif anomalies:
            findings.append("No qualified historical anomaly was detected for this trip.")
        else:
            findings.append("Historical baseline is not yet qualified for comparison.")

        anomaly_status = "ATTENTION" if any(a.get("status") == "ATTENTION" for a in notable) else "WATCH" if notable else "NORMAL"
        rank = {"NORMAL": 0, "WATCH": 1, "ATTENTION": 2, "CRITICAL": 3}
        status = trip.diagnostic_status if rank.get(trip.diagnostic_status, 0) >= rank.get(anomaly_status, 0) else anomaly_status
        if not eligible_for_baseline:
            findings.append("Trip excluded from the healthy reference baseline because a diagnostic condition occurred.")
        return PostTripReport(
            generated_at=datetime.now(timezone.utc),
            trip_id=trip.id,
            status=status,
            eligible_for_baseline=eligible_for_baseline,
            metrics={
                "distance_km": trip.distance_km,
                "duration_s": trip.duration_s,
                "avg_speed_kmh": trip.avg_speed_kmh,
                "max_speed_kmh": trip.max_speed_kmh,
                "max_coolant_c": trip.max_coolant_c,
                "max_oil_temp_c": trip.max_oil_temp_c,
                "min_oil_pressure_bar": trip.min_oil_pressure_bar,
                "avg_running_voltage_v": trip.avg_running_voltage_v,
                "avg_cvt_ratio_deviation_pct": trip.avg_cvt_ratio_deviation_pct,
                "max_cvt_temp_c": trip.max_cvt_temp_c,
            },
            anomalies=anomalies,
            findings=findings,
        )
