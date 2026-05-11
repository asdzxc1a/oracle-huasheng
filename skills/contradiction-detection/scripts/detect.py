#!/usr/bin/env python3
"""
Contradiction Detection Script

Usage:
    python detect.py --claims claims.json --actor "Actor Name" --output contradictions.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running standalone when oracle is on PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from oracle.kernel.llm_client import LLMClient
from oracle.kernel.intelligence import (
    Claim,
    Contradiction,
    detect_contradictions,
    _heuristic_contradictions,
)


def load_claims(path: Path) -> list[Claim]:
    """Load claims from JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Claim(**c) for c in data.get("claims", [])]


def format_contradictions(contradictions: list[Contradiction]) -> str:
    """Format contradictions as markdown."""
    lines = ["# Contradiction Map\n"]
    for c in contradictions:
        lines.append(c.to_markdown())
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect contradictions in actor claims")
    parser.add_argument("--claims", required=True, help="Path to claims JSON file")
    parser.add_argument("--actor", required=True, help="Actor name")
    parser.add_argument("--min-pairs", type=int, default=2, help="Minimum contradiction pairs")
    parser.add_argument("--output", required=True, help="Output markdown file")
    args = parser.parse_args()

    claims_path = Path(args.claims)
    output_path = Path(args.output)

    if not claims_path.exists():
        print(f"Claims file not found: {claims_path}", file=sys.stderr)
        return 1

    claims = load_claims(claims_path)
    llm = LLMClient()

    contradictions = detect_contradictions(llm, claims, args.actor, min_pairs=args.min_pairs)

    output_path.write_text(format_contradictions(contradictions), encoding="utf-8")
    print(f"Wrote {len(contradictions)} contradiction(s) to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
