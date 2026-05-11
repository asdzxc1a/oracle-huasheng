#!/usr/bin/env python3
"""
Adversarial Pass — Devil's Advocate Script

Usage:
    python devil_advocate.py --thesis "Actor is ready for drama lead" --evidence evidence.md --actor "Actor Name" --output adversarial.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from oracle.kernel.llm_client import LLMClient
from oracle.kernel.intelligence import (
    AdversarialFinding,
    run_adversarial_pass,
    _heuristic_adversarial,
)


def format_findings(findings: list[AdversarialFinding]) -> str:
    lines = ["# Adversarial Findings\n"]
    for f in findings:
        lines.append(f.to_markdown())
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run adversarial pass against a thesis")
    parser.add_argument("--thesis", required=True, help="Main thesis to challenge")
    parser.add_argument("--evidence", required=True, help="Path to evidence summary file")
    parser.add_argument("--actor", required=True, help="Actor name")
    parser.add_argument("--output", required=True, help="Output markdown file")
    args = parser.parse_args()

    evidence_path = Path(args.evidence)
    output_path = Path(args.output)

    if not evidence_path.exists():
        print(f"Evidence file not found: {evidence_path}", file=sys.stderr)
        return 1

    evidence = evidence_path.read_text(encoding="utf-8")
    llm = LLMClient()

    findings = run_adversarial_pass(llm, args.thesis, evidence, args.actor)

    output_path.write_text(format_findings(findings), encoding="utf-8")
    print(f"Wrote {len(findings)} adversarial finding(s) to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
