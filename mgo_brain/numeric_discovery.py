from __future__ import annotations

import bisect
import csv
import io
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from .survey import CANLogRecord, parse_candump


class NumericDiscoveryRequest(BaseModel):
    can_log: str
    reference_csv: str
    label: str = "numeric_signal"
    max_time_gap_s: float = Field(default=0.25, gt=0, le=5)
    min_samples: int = Field(default=12, ge=4, le=10000)
    max_candidates: int = Field(default=30, ge=1, le=200)


@dataclass(frozen=True)
class ReferenceSample:
    timestamp: float
    value: float


@dataclass(frozen=True)
class FieldHypothesis:
    arbitration_id: int
    offset: int
    width: int
    endian: str
    signed: bool

    @property
    def name(self) -> str:
        sign = "s" if self.signed else "u"
        suffix = "" if self.width == 1 else self.endian
        return f"b{self.offset}:{sign}{self.width * 8}{suffix}"


def parse_reference_csv(text: str) -> tuple[list[ReferenceSample], list[dict[str, Any]]]:
    """Parse CSV with columns timestamp,value. Header is optional."""

    samples: list[ReferenceSample] = []
    rejected: list[dict[str, Any]] = []
    reader = csv.reader(io.StringIO(text))
    for line_no, row in enumerate(reader, start=1):
        if not row or all(not x.strip() for x in row):
            continue
        if line_no == 1 and row[0].strip().lower() in {"timestamp", "time", "ts"}:
            continue
        if len(row) < 2:
            rejected.append({"line": line_no, "row": row})
            continue
        try:
            samples.append(ReferenceSample(float(row[0]), float(row[1])))
        except ValueError:
            rejected.append({"line": line_no, "row": row[:4]})
    samples.sort(key=lambda x: x.timestamp)
    return samples, rejected


def discover_numeric_from_text(
    can_log: str,
    reference_csv: str,
    *,
    label: str = "numeric_signal",
    max_time_gap_s: float = 0.25,
    min_samples: int = 12,
    max_candidates: int = 30,
) -> dict[str, Any]:
    records, rejected_can = parse_candump(can_log)
    reference, rejected_reference = parse_reference_csv(reference_csv)
    report = discover_numeric(
        records,
        reference,
        label=label,
        max_time_gap_s=max_time_gap_s,
        min_samples=min_samples,
        max_candidates=max_candidates,
    )
    report["rejected"] = {
        "can": rejected_can,
        "reference": rejected_reference,
    }
    return report


def discover_numeric(
    records: list[CANLogRecord],
    reference: list[ReferenceSample],
    *,
    label: str = "numeric_signal",
    max_time_gap_s: float = 0.25,
    min_samples: int = 12,
    max_candidates: int = 30,
) -> dict[str, Any]:
    if not reference:
        return {"label": label, "reference_samples": 0, "can_frames": len(records), "candidates": []}

    ref_times = [x.timestamp for x in reference]
    by_id: dict[int, list[CANLogRecord]] = defaultdict(list)
    for record in records:
        if record.timestamp is not None:
            by_id[record.arbitration_id].append(record)

    candidates = []
    for arbitration_id, frames in by_id.items():
        max_dlc = max((len(x.data) for x in frames), default=0)
        hypotheses = []
        for offset in range(max_dlc):
            hypotheses.append(FieldHypothesis(arbitration_id, offset, 1, "na", False))
            hypotheses.append(FieldHypothesis(arbitration_id, offset, 1, "na", True))
            if offset + 1 < max_dlc:
                hypotheses.extend([
                    FieldHypothesis(arbitration_id, offset, 2, "le", False),
                    FieldHypothesis(arbitration_id, offset, 2, "be", False),
                    FieldHypothesis(arbitration_id, offset, 2, "le", True),
                    FieldHypothesis(arbitration_id, offset, 2, "be", True),
                ])

        for hypothesis in hypotheses:
            pairs = []
            raw_sequence = []
            for frame in frames:
                if frame.timestamp is None:
                    continue
                raw = _extract(frame.data, hypothesis)
                if raw is None:
                    continue
                ref = _nearest_reference(frame.timestamp, reference, ref_times, max_time_gap_s)
                if ref is None:
                    continue
                pairs.append((float(raw), ref.value))
                raw_sequence.append(int(raw))

            if len(pairs) < min_samples:
                continue
            unique_raw = len({x for x, _ in pairs})
            unique_ref = len({round(y, 9) for _, y in pairs})
            if unique_raw < 3 or unique_ref < 3:
                continue

            fit = _linear_fit(pairs)
            if fit is None:
                continue
            counter_likeness = _counter_likeness(raw_sequence, hypothesis.width)
            coverage = min(1.0, len(pairs) / max(min_samples, len(reference)))
            score = max(0.0, abs(fit["r"])) * math.sqrt(max(0.05, coverage)) * (1.0 - 0.7 * counter_likeness)
            score = round(score, 5)

            candidates.append({
                "id": arbitration_id,
                "id_hex": _id_hex(arbitration_id),
                "field": hypothesis.name,
                "offset": hypothesis.offset,
                "width": hypothesis.width,
                "endian": hypothesis.endian,
                "signed": hypothesis.signed,
                "samples": len(pairs),
                "unique_raw": unique_raw,
                "r": round(fit["r"], 6),
                "r2": round(fit["r"] ** 2, 6),
                "slope": round(fit["slope"], 9),
                "intercept": round(fit["intercept"], 9),
                "rmse": round(fit["rmse"], 6),
                "counter_likeness": round(counter_likeness, 4),
                "coverage": round(coverage, 4),
                "score": score,
                "hypothesis": f"{label} ≈ {fit['slope']:.9g} * raw + {fit['intercept']:.9g}",
            })

    candidates.sort(
        key=lambda x: (x["score"], x["r2"], -x["rmse"], x["samples"]),
        reverse=True,
    )
    return {
        "label": label,
        "reference_samples": len(reference),
        "can_frames": len(records),
        "candidates": candidates[:max_candidates],
        "warning": "Candidates are statistical hypotheses only. Confirm with repeated varied experiments before adding a DBC signal.",
    }


def make_numeric_demo() -> dict[str, str]:
    """Synthetic varied-speed demo with a real u16le signal plus a counter."""

    speeds = [0, 5, 12, 25, 40, 18, 45, 30, 8, 35, 15, 48, 22, 4, 42, 10, 28, 46, 16, 32]
    can_lines = []
    ref_lines = ["timestamp,value"]
    for i, speed in enumerate(speeds):
        timestamp = 2000.0 + i * 0.2
        raw = int(speed * 20)
        lo, hi = raw & 0xFF, (raw >> 8) & 0xFF
        counter = i & 0xFF
        can_lines.append(f"({timestamp:.3f}) can0 420#{lo:02X}{hi:02X}AABBCCDDEEFF")
        can_lines.append(f"({timestamp:.3f}) can0 201#{counter:02X}00000000000000")
        ref_lines.append(f"{timestamp:.3f},{speed}")
    return {
        "can_log": "\n".join(can_lines),
        "reference_csv": "\n".join(ref_lines),
        "label": "vehicle_speed_gps",
    }


def _nearest_reference(
    timestamp: float,
    reference: list[ReferenceSample],
    ref_times: list[float],
    max_gap: float,
) -> ReferenceSample | None:
    index = bisect.bisect_left(ref_times, timestamp)
    options = []
    if index < len(reference):
        options.append(reference[index])
    if index > 0:
        options.append(reference[index - 1])
    if not options:
        return None
    best = min(options, key=lambda x: abs(x.timestamp - timestamp))
    return best if abs(best.timestamp - timestamp) <= max_gap else None


def _extract(data: bytes, h: FieldHypothesis) -> int | None:
    if h.offset + h.width > len(data):
        return None
    raw = data[h.offset : h.offset + h.width]
    if h.width == 1:
        value = raw[0]
        if h.signed and value >= 128:
            value -= 256
        return value

    byteorder = "little" if h.endian == "le" else "big"
    return int.from_bytes(raw, byteorder=byteorder, signed=h.signed)


def _linear_fit(pairs: list[tuple[float, float]]) -> dict[str, float] | None:
    n = len(pairs)
    xs = [x for x, _ in pairs]
    ys = [y for _, y in pairs]
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 1e-12 or syy <= 1e-12:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in pairs)
    slope = sxy / sxx
    intercept = my - slope * mx
    r = sxy / math.sqrt(sxx * syy)
    residuals = [y - (slope * x + intercept) for x, y in pairs]
    rmse = math.sqrt(sum(e * e for e in residuals) / n)
    return {"slope": slope, "intercept": intercept, "r": r, "rmse": rmse}


def _counter_likeness(values: list[int], width: int) -> float:
    if len(values) < 4:
        return 0.0
    modulo = 1 << (width * 8)
    steps = 0
    for a, b in zip(values, values[1:]):
        delta = (b - a) % modulo
        if delta in {0, 1}:
            steps += 1
    return steps / (len(values) - 1)


def _id_hex(arbitration_id: int) -> str:
    width = 8 if arbitration_id > 0x7FF else 3
    return f"0x{arbitration_id:0{width}X}"
