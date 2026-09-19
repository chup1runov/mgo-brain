from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser(description="Ask the running MGO Brain service.")
    parser.add_argument("question", nargs="+")
    parser.add_argument("--url", default=os.environ.get("MGO_BRAIN_URL", "http://127.0.0.1:8080"))
    parser.add_argument("--evidence", action="store_true")
    args = parser.parse_args()

    payload = json.dumps({
        "question": " ".join(args.question),
        "language": "ru",
        "include_evidence": args.evidence,
    }, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        args.url.rstrip("/") + "/api/v1/ai/ask",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Ask MGO failed: HTTP {exc.code}: {detail}") from exc
    except OSError as exc:
        raise SystemExit(f"Ask MGO service unavailable: {exc}") from exc

    print(body.get("answer", ""))
    tools = body.get("tools_used") or []
    if tools:
        print("\nEvidence tools: " + ", ".join(tools))
    warnings = body.get("warnings") or []
    for warning in warnings:
        print("\nWarning: " + str(warning))
    if args.evidence and body.get("evidence"):
        print("\nEvidence:")
        print(json.dumps(body["evidence"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
