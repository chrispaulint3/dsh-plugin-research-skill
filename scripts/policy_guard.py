#!/usr/bin/env python3
"""Static guard for proposed adaptive-execution config JSON; not runtime IAM."""
import argparse
import json
from pathlib import Path


def validate(config):
    mode = config.get("mode", "observe")
    if mode not in {"off", "observe", "recommend", "enforce"}:
        raise ValueError("mode must be off/observe/recommend/enforce")
    skill = config.get("skill", {})
    tool = config.get("tool", {})
    learning = config.get("learning", {})
    if mode != "enforce" and (skill.get("catalogShadow", False) or tool.get("routingEnabled", False)):
        raise ValueError(f"{mode} cannot shadow Catalog or restrict tools; only enforce may mutate visibility")
    if mode == "off" and (learning.get("enabled", False) or config.get("collectEvents", False)):
        raise ValueError("off must not collect or learn")
    weight = learning.get("maxHistoryWeight", 0.15)
    if not isinstance(weight, (float, int)) or not 0 <= weight <= 0.15:
        raise ValueError("maxHistoryWeight must be between 0 and 0.15")
    evidence = learning.get("minEvidence", 5)
    if not isinstance(evidence, int) or isinstance(evidence, bool) or evidence < 1:
        raise ValueError("minEvidence must be positive integer")
    return {"mode": mode, "visibility_mutation_allowed": mode == "enforce", "max_history_weight": weight}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", required=True)
    args = p.parse_args()
    result = validate(json.loads(Path(args.config).read_text(encoding="utf-8")))
    print(json.dumps({"valid": True, **result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
