#!/usr/bin/env python3
"""
Tier Marking Script

Usage:
    python tagger.py --claims claims.json --output claims-tagged.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from oracle.kernel.intelligence import Claim, apply_tier_marking, tag_text_with_tiers


def load_claims(path: Path) -> list[Claim]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Claim(**c) for c in data.get("claims", [])]


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply tier marking to claims")
    parser.add_argument("--claims", required=True, help="Path to claims JSON file")
    parser.add_argument("--text", help="Optional markdown text to tag with tiers")
    parser.add_argument("--output", required=True, help="Output JSON file")
    args = parser.parse_args()

    claims_path = Path(args.claims)
    output_path = Path(args.output)

    if not claims_path.exists():
        print(f"Claims file not found: {claims_path}", file=sys.stderr)
        return 1

    claims = load_claims(claims_path)
    claims = apply_tier_marking(claims)

    result = {
        "claims": [
            {
                "text": c.text,
                "source_type": c.source_type,
                "access_level": c.access_level,
                "source_url": c.source_url,
                "timestamp": c.timestamp,
                "tier": c.tier,
                "confidence": c.confidence,
            }
            for c in claims
        ]
    }

    if args.text:
        result["tagged_text"] = tag_text_with_tiers(args.text, claims)

    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {len(claims)} tagged claim(s) to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
