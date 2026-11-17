#!/usr/bin/env python3
"""Offline experiment harness for v3 adaptive routing. Not a DSH runtime collector.

Input events are normalized, synthetic or exported with consent. No raw prompts.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import uuid


def load(path):
    rows = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError(f"{path}:{n}: must be JSON object")
        rows.append(obj)
    return rows


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("occurred_at/as_of must be ISO8601 with timezone")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("time must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def audit(events):
    """Normalize double-published tool results; last feedback revision wins chronologically."""
    unique = {}
    calls = {}
    feedback = {}
    conflicts = []
    unattributed = 0
    for e in sorted(events, key=lambda x: timestamp(x["occurred_at"])):
        eid = e.get("event_id")
        if not isinstance(eid, str) or not eid:
            raise ValueError("every event needs stable event_id")
        canonical = json.dumps(e, sort_keys=True, ensure_ascii=False)
        if eid in unique:
            if unique[eid] != canonical:
                raise ValueError(f"conflicting duplicate event_id {eid}")
            continue
        unique[eid] = canonical
        kind = e.get("event_type")
        if kind in ("tools/result", "session/tool-result"):
            key = e.get("call_key")
            if not key:
                unattributed += 1
                continue
            status = e.get("outcome")
            if status not in ("ok", "error", "denied", "cancelled"):
                raise ValueError(f"invalid tool outcome {status}")
            if key in calls and calls[key]["outcome"] != status:
                conflicts.append(key)
            elif key not in calls or kind == "tools/result":
                calls[key] = {"outcome": status, "source": kind}
        elif kind in ("feedback/message-put", "feedback/message-delete"):
            key = (e.get("session_id"), e.get("message_id"))
            if not all(isinstance(v, str) and v for v in key):
                raise ValueError("feedback requires session_id and message_id")
            rev = e.get("revision")
            if not isinstance(rev, int) or rev < 0:
                raise ValueError("feedback revision must be a nonnegative integer")
            if key in feedback and rev <= feedback[key]["revision"]:
                if rev == feedback[key]["revision"]:
                    raise ValueError(f"ambiguous equal revision for {key}")
                continue
            if kind == "feedback/message-put" and e.get("rating") not in ("positive", "negative"):
                raise ValueError("feedback put needs positive/negative rating")
            feedback[key] = {"revision": rev, "rating": e.get("rating") if kind.endswith("put") else None,
                             "deleted": kind.endswith("delete")}
    return {"unique_events": len(unique), "tool_calls": len(calls),
            "call_conflicts": sorted(set(conflicts)), "unattributed_tool_events": unattributed,
            "feedback_current": {f"{k[0]}:{k[1]}": v for k, v in sorted(feedback.items())}}


def rank(query, events, min_evidence=5, max_weight=0.15, threshold=0.2):
    """Time-aware B1/B2 ranking with strict content gate and bounded history shift."""
    cutoff = timestamp(query["as_of"])
    intent = query["intent"]
    candidates = query["candidates"]
    if not isinstance(candidates, list) or len({c["key"] for c in candidates}) != len(candidates):
        raise ValueError("candidate list must have unique keys")
    stats = defaultdict(lambda: [0, 0])
    credited = set()
    for e in events:
        if e.get("event_type") != "task/evaluated" or e.get("evidence_scope") != "verified" or e.get("attribution") != "direct":
            continue
        if timestamp(e["occurred_at"]) >= cutoff or e.get("intent") != intent:
            continue  # no future leakage, no cross-intent feedback
        if e.get("task_outcome") not in ("success", "failed"):
            continue
        key = (e.get("capability_key"), e.get("release_digest"))
        credit_id = (e.get("task_id"), *key)
        if not e.get("task_id") or credit_id in credited:
            continue
        credited.add(credit_id)
        stats[key][0] += 1
        stats[key][1] += int(e["task_outcome"] == "success")
    scored = []
    for c in candidates:
        relevance = float(c["relevance"])
        if not 0 <= relevance <= 1:
            raise ValueError("relevance must be 0..1")
        if relevance < threshold or c.get("authorized") is False:
            continue  # history can never override content / authorization gate
        seen, successes = stats[(c["key"], c.get("release_digest"))]
        posterior = (successes + 1) / (seen + 2)  # Beta(1,1) posterior mean
        delta = max(-max_weight, min(max_weight, max_weight * 2 * (posterior - 0.5))) if seen >= min_evidence else 0.
        scored.append({"key": c["key"], "content": relevance,
                       "experience_delta": round(delta, 6), "score": round(relevance + delta, 6),
                       "evidence_count": seen, "success_count": successes,
                       "state": "verified" if seen >= min_evidence else "candidate"})
    b1 = sorted(scored, key=lambda x: (-x["content"], x["key"]))
    b2 = sorted(scored, key=lambda x: (-x["score"], x["key"]))
    return {"id": query["id"], "b1": [x["key"] for x in b1], "b2": [x["key"] for x in b2],
            "details": b2, "abstained": not bool(scored)}


def quality(queries, results, k):
    metrics = {}
    for policy in ("b1", "b2"):
        recall = mrr = forbidden = 0.
        for q, result in zip(queries, results):
            selected = result[policy][:k]
            relevant = set(q.get("relevant", []))
            blocked = set(q.get("forbidden", []))
            recall += len(relevant.intersection(selected)) / len(relevant) if relevant else float(not selected)
            mrr += next((1/i for i, name in enumerate(selected, 1) if name in relevant), 0)
            forbidden += bool(blocked.intersection(selected))
        metrics[policy] = {"recall_at_k": round(recall/len(queries), 6),
                           "mrr_at_k": round(mrr/len(queries), 6),
                           "forbidden_at_k": round(forbidden/len(queries), 6)}
    return metrics


def evaluate(events, queries, *, k=3, min_evidence=5, max_weight=0.15, threshold=0.2):
    if not queries or k < 1 or min_evidence < 1 or not 0 <= max_weight <= 0.15 or not 0 <= threshold <= 1:
        raise ValueError("invalid experiment arguments")
    ids = [q.get("id") for q in queries]
    if len(set(ids)) != len(ids) or not all(isinstance(i, str) and i for i in ids):
        raise ValueError("query IDs must be unique and nonempty")
    results = [rank(q, events, min_evidence, max_weight, threshold) for q in queries]
    return {"metrics": quality(queries, results, k), "results": results, "k": k,
            "min_evidence": min_evidence, "max_weight": max_weight, "threshold": threshold,
            "warning": "Offline B1/B2 only. B0 requires real DSH snapshots; not proof of task success."}


def store(db, mode, source, output):
    p = Path(db); p.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(p) as con:
        con.execute("CREATE TABLE IF NOT EXISTS adaptive_eval_runs (run_id TEXT PRIMARY KEY, created_at TEXT, mode TEXT, source_sha256 TEXT, report_json TEXT)")
        con.execute("INSERT INTO adaptive_eval_runs VALUES (?,?,?,?,?)", (
            str(uuid.uuid4()), datetime.now(timezone.utc).isoformat(), mode,
            hashlib.sha256(Path(source).read_bytes()).hexdigest(), json.dumps(output, ensure_ascii=False)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("audit"); a.add_argument("--events", required=True)
    e = sub.add_parser("evaluate"); e.add_argument("--events", required=True)
    e.add_argument("--queries", required=True); e.add_argument("--k", type=int, default=3)
    e.add_argument("--min-evidence", type=int, default=5); e.add_argument("--max-weight", type=float, default=0.15)
    e.add_argument("--threshold", type=float, default=0.2)
    for s in (a, e): s.add_argument("--db"); s.add_argument("--out")
    args = p.parse_args()
    try:
        events = load(args.events)
        output = audit(events) if args.command == "audit" else evaluate(
            events, load(args.queries), k=args.k, min_evidence=args.min_evidence,
            max_weight=args.max_weight, threshold=args.threshold)
        if args.db: store(args.db, args.command, args.events, output)
        encoded = json.dumps(output, ensure_ascii=False, indent=2)
        if args.out:
            path = Path(args.out)
            if path.exists(): raise ValueError("refusing to overwrite report")
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text(encoded + "\n", encoding="utf-8")
        print(encoded)
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as ex:
        p.error(str(ex))


if __name__ == "__main__":
    main()
