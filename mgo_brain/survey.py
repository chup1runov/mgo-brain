from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


_HASH_RE = re.compile(
    r"^\s*(?:\((?P<ts>\d+(?:\.\d+)?)\)\s+)?"
    r"(?P<iface>\S+)\s+"
    r"(?P<id>[0-9A-Fa-f]{3,8})#(?P<data>[0-9A-Fa-f]*)\s*$"
)

_BRACKET_RE = re.compile(
    r"^\s*(?:\((?P<ts>\d+(?:\.\d+)?)\)\s+)?"
    r"(?P<iface>\S+)\s+"
    r"(?P<id>[0-9A-Fa-f]{3,8})\s+\[(?P<dlc>\d{1,2})\]\s*"
    r"(?P<data>(?:[0-9A-Fa-f]{2}(?:\s+|$))*)"
)


@dataclass(frozen=True, slots=True)
class CANLogRecord:
    arbitration_id: int
    data: bytes
    timestamp: float | None = None
    interface: str | None = None

    @property
    def id_hex(self) -> str:
        width = 8 if self.arbitration_id > 0x7FF else 3
        return f"0x{self.arbitration_id:0{width}X}"


class SurveyAnalyzeRequest(BaseModel):
    baseline: str
    action: str
    label: str = "event"
    max_candidates: int = Field(default=25, ge=1, le=200)


class SurveyParseRequest(BaseModel):
    log: str


def parse_candump_line(line: str) -> CANLogRecord | None:
    """Parse the common candump hash and bracket formats.

    Accepted examples:
      (123.456) can0 310#00010203
      can0 310 [4] 00 01 02 03
    """

    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    match = _HASH_RE.match(stripped)
    if match:
        data_hex = match.group("data")
        if len(data_hex) % 2 or len(data_hex) > 16 or int(match.group("id"), 16) > 0x1FFFFFFF:
            return None
        return CANLogRecord(
            arbitration_id=int(match.group("id"), 16),
            data=bytes.fromhex(data_hex),
            timestamp=float(match.group("ts")) if match.group("ts") else None,
            interface=match.group("iface"),
        )

    match = _BRACKET_RE.fullmatch(stripped)
    if match:
        tokens = match.group("data").split()
        dlc = int(match.group("dlc"))
        if len(tokens) != dlc or dlc > 8 or int(match.group("id"), 16) > 0x1FFFFFFF:
            return None
        return CANLogRecord(
            arbitration_id=int(match.group("id"), 16),
            data=bytes(int(token, 16) for token in tokens[:dlc]),
            timestamp=float(match.group("ts")) if match.group("ts") else None,
            interface=match.group("iface"),
        )
    return None


def parse_candump(text: str) -> tuple[list[CANLogRecord], list[dict[str, Any]]]:
    records: list[CANLogRecord] = []
    rejected: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        record = parse_candump_line(line)
        if record is None:
            rejected.append({"line": line_no, "text": line[:200]})
        else:
            records.append(record)
    return records, rejected


def summarize_records(records: list[CANLogRecord]) -> dict[str, Any]:
    by_id: dict[int, list[CANLogRecord]] = defaultdict(list)
    for record in records:
        by_id[record.arbitration_id].append(record)

    ids = []
    for arbitration_id, group in sorted(by_id.items()):
        max_dlc = max((len(x.data) for x in group), default=0)
        byte_stats = []
        for index in range(max_dlc):
            values = Counter(x.data[index] for x in group if index < len(x.data))
            byte_stats.append({
                "index": index,
                "unique_values": len(values),
                "top": _top_value(values),
                "entropy_proxy": _entropy_proxy(values),
            })
        ids.append({
            "id": arbitration_id,
            "id_hex": _id_hex(arbitration_id),
            "frames": len(group),
            "dlc_values": sorted({len(x.data) for x in group}),
            "byte_stats": byte_stats,
        })

    return {
        "frames": len(records),
        "unique_ids": len(by_id),
        "ids": ids,
    }


def compare_logs(
    baseline: list[CANLogRecord],
    action: list[CANLogRecord],
    *,
    label: str = "event",
    max_candidates: int = 25,
) -> dict[str, Any]:
    base_by = _group(baseline)
    act_by = _group(action)
    all_ids = sorted(set(base_by) | set(act_by))
    candidates = []

    for arbitration_id in all_ids:
        base_group = base_by.get(arbitration_id, [])
        act_group = act_by.get(arbitration_id, [])
        max_dlc = max(
            [len(x.data) for x in base_group + act_group] or [0]
        )
        changed_bytes = []

        for index in range(max_dlc):
            base_values = Counter(x.data[index] for x in base_group if index < len(x.data))
            act_values = Counter(x.data[index] for x in act_group if index < len(x.data))
            comparison = _compare_byte(index, base_values, act_values)
            if comparison["score"] > 0:
                changed_bytes.append(comparison)

        only_in_action = bool(act_group and not base_group)
        only_in_baseline = bool(base_group and not act_group)
        byte_score = sum(x["score"] for x in changed_bytes)
        presence_score = 6.0 if only_in_action or only_in_baseline else 0.0
        frame_balance = _balance_factor(len(base_group), len(act_group))
        total_score = round((byte_score + presence_score) * frame_balance, 3)

        if total_score <= 0:
            continue

        candidates.append({
            "id": arbitration_id,
            "id_hex": _id_hex(arbitration_id),
            "score": total_score,
            "frames_baseline": len(base_group),
            "frames_action": len(act_group),
            "only_in_action": only_in_action,
            "only_in_baseline": only_in_baseline,
            "changed_bytes": sorted(changed_bytes, key=lambda x: x["score"], reverse=True),
            "observed_dlc": sorted({len(x.data) for x in base_group + act_group}),
        })

    candidates.sort(key=lambda x: (x["score"], len(x["changed_bytes"])), reverse=True)
    candidates = candidates[:max_candidates]

    return {
        "label": label,
        "baseline": {
            "frames": len(baseline),
            "unique_ids": len(base_by),
        },
        "action": {
            "frames": len(action),
            "unique_ids": len(act_by),
        },
        "candidates": candidates,
        "draft_dbc": render_draft_dbc(candidates, label=label),
    }


def analyze_text(
    baseline_text: str,
    action_text: str,
    *,
    label: str = "event",
    max_candidates: int = 25,
) -> dict[str, Any]:
    baseline, rejected_baseline = parse_candump(baseline_text)
    action, rejected_action = parse_candump(action_text)
    report = compare_logs(
        baseline,
        action,
        label=label,
        max_candidates=max_candidates,
    )
    report["rejected"] = {
        "baseline": rejected_baseline,
        "action": rejected_action,
    }
    return report


def render_draft_dbc(candidates: list[dict[str, Any]], *, label: str) -> str:
    """Create a safe DBC skeleton with messages only.

    No SG_ signal definitions are emitted because endian/bit layout cannot be
    inferred safely from a two-state comparison.
    """

    lines = [
        'VERSION "MGO Brain CAN Survey draft"',
        "",
        "NS_ :",
        "",
        "BS_:",
        "",
        "BU_: MGO_BFI",
        "",
    ]
    for item in candidates[:20]:
        arbitration_id = int(item["id"])
        max_index = max(
            [x["index"] for x in item.get("changed_bytes", [])] or [7]
        )
        observed = item.get("observed_dlc", [])
        if len(observed) != 1:
            continue  # A variable/unknown length is not an established DBC message.
        dlc = observed[0]
        name = f"MGO_{arbitration_id:03X}" if arbitration_id <= 0x7FF else f"MGO_{arbitration_id:08X}"
        dbc_id = arbitration_id | (0x80000000 if arbitration_id > 0x7FF else 0)
        lines.append(f"BO_ {dbc_id} {name}: {dlc} MGO_BFI")
        changed = ",".join(str(x["index"]) for x in item.get("changed_bytes", [])) or "presence-only"
        comment = (
            f"Survey candidate for {label}; score={item['score']}; "
            f"changed_bytes={changed}; no signal layout decoded."
        ).replace('"', "'").replace("\n", " ").replace("\r", " ").replace("\\", "/")
        lines.append(f'CM_ BO_ {dbc_id} "{comment}";')
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def sample_pair() -> dict[str, str]:
    baseline_lines = []
    action_lines = []
    for i in range(20):
        ts = 1000 + i * 0.05
        counter = i & 0xFF
        baseline_lines.extend([
            f"({ts:.3f}) can0 120#1122334455667788",
            f"({ts:.3f}) can0 201#{counter:02X}00000000000000",
            f"({ts:.3f}) can0 310#0000000000000000",
        ])
        action_lines.extend([
            f"({ts + 2:.3f}) can0 120#1122334455667788",
            f"({ts + 2:.3f}) can0 201#{(counter + 20) & 0xFF:02X}00000000000000",
            f"({ts + 2:.3f}) can0 310#0001000000000000",
        ])
    return {
        "baseline": "\n".join(baseline_lines),
        "action": "\n".join(action_lines),
        "label": "driver_door_open",
    }


def _group(records: list[CANLogRecord]) -> dict[int, list[CANLogRecord]]:
    out: dict[int, list[CANLogRecord]] = defaultdict(list)
    for record in records:
        out[record.arbitration_id].append(record)
    return out


def _compare_byte(index: int, base: Counter[int], action: Counter[int]) -> dict[str, Any]:
    if not base and not action:
        return {
            "index": index,
            "score": 0.0,
        }

    base_top = _top_value(base)
    action_top = _top_value(action)
    base_share = base_top["share"] if base_top else 0.0
    action_share = action_top["share"] if action_top else 0.0
    modal_changed = bool(
        base_top
        and action_top
        and base_top["value"] != action_top["value"]
    )

    # Stable-before/stable-after toggles are the strongest evidence.
    stability = min(base_share, action_share)
    toggle_score = 5.0 * stability if modal_changed else 0.0

    # Distribution shift catches fields that change but are not perfectly stable.
    all_values = set(base) | set(action)
    distance = 0.0
    base_n = sum(base.values()) or 1
    action_n = sum(action.values()) or 1
    for value in all_values:
        distance += abs(base[value] / base_n - action[value] / action_n)
    distance *= 0.5

    # Penalize bytes that are already noisy in both recordings.
    noise = (_entropy_proxy(base) + _entropy_proxy(action)) / 2.0
    distribution_score = 2.0 * distance * max(0.15, 1.0 - noise)
    score = round(toggle_score + distribution_score, 3)

    return {
        "index": index,
        "score": score,
        "baseline_top": base_top,
        "action_top": action_top,
        "distribution_distance": round(distance, 3),
        "noise": round(noise, 3),
        "modal_changed": modal_changed,
    }


def _top_value(counter: Counter[int]) -> dict[str, Any] | None:
    if not counter:
        return None
    value, count = counter.most_common(1)[0]
    total = sum(counter.values())
    return {
        "value": value,
        "hex": f"{value:02X}",
        "count": count,
        "share": round(count / total, 3),
    }


def _entropy_proxy(counter: Counter[int]) -> float:
    if not counter:
        return 0.0
    total = sum(counter.values())
    if total <= 1 or len(counter) <= 1:
        return 0.0
    # Simple 0..1 variability proxy; sufficient for ranking survey noise.
    top_count = counter.most_common(1)[0][1]
    return min(1.0, 1.0 - top_count / total)


def _balance_factor(a: int, b: int) -> float:
    if a == 0 or b == 0:
        return 1.0
    return min(a, b) / max(a, b)


def _id_hex(arbitration_id: int) -> str:
    width = 8 if arbitration_id > 0x7FF else 3
    return f"0x{arbitration_id:0{width}X}"
