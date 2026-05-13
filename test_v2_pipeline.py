#!/usr/bin/env python3
"""
End-to-end test for the Oracle V2 Pipeline.

Usage:
    python test_v2_pipeline.py [--actor "Actor Name"] [--question "Casting question"]
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from oracle.kernel import AgentRunner, create_manifest, load_manifest

BASE_PATH = Path(__file__).parent


def run_pipeline(actor: str, question: str, max_videos: int = 1) -> dict:
    """Run the full V2 pipeline and return results."""
    runner = AgentRunner(BASE_PATH)

    # 1. Create investigation
    print(f"\n🎭 Creating investigation for {actor}...")
    manifest = create_manifest(
        base_path=BASE_PATH,
        actor=actor,
        client_question=question,
    )
    inv_id = manifest["id"]
    print(f"   ID: {inv_id}")

    # 2. Actor Harvester
    print(f"\n📹 [1/5] Running Actor Harvester...")
    result = runner.run_agent(
        investigation_id=inv_id,
        agent_name="actor_harvester",
        instructions={"actor_name": actor, "max_videos": 10},
    )
    if not result["success"]:
        print(f"   ✗ Failed: {result.get('error')}")
        return result
    print(f"   ✓ Found {result['result']['videos_found']} videos")

    # 3. Video Analyzer v2
    print(f"\n🎬 [2/5] Running Video Analyzer v2 (max {max_videos} videos)...")
    result = runner.run_agent(
        investigation_id=inv_id,
        agent_name="video_analyzer_v2",
        instructions={"max_videos": max_videos},
    )
    if not result["success"]:
        print(f"   ✗ Failed: {result.get('error')}")
    else:
        print(f"   ✓ Analyzed {result['result'].get('videos_analyzed', 0)} videos, {result['result'].get('observations_count', 0)} observations")
        if result["result"].get("errors"):
            for err in result["result"]["errors"]:
                print(f"   ⚠ {err}")

    # 4. Knowledge Sync
    print(f"\n🧠 [3/5] Running Knowledge Sync...")
    result = runner.run_agent(
        investigation_id=inv_id,
        agent_name="knowledge_sync",
        instructions={},
    )
    if result["success"]:
        print(f"   ✓ Stored {result['result'].get('claims_stored', 0)} claims")

    # 5. Psychological Profiler
    print(f"\n🧬 [4/5] Running Psychological Profiler...")
    result = runner.run_agent(
        investigation_id=inv_id,
        agent_name="psychological_profiler",
        instructions={},
    )
    if result["success"]:
        dims = result["result"].get("dimensions", {})
        print(f"   ✓ Profile complete: {', '.join(f'{k}={v}' for k, v in dims.items())}")

    # 6. Wiki Sync
    print(f"\n📖 [5/5] Running Wiki Sync...")
    result = runner.run_agent(
        investigation_id=inv_id,
        agent_name="wiki_sync",
        instructions={},
    )
    if result["success"]:
        print(f"   ✓ Wiki updated: {result['result'].get('wiki_path')}")

    # 7. Red Team
    print(f"\n🛡️  [Bonus] Running Red Team Agent...")
    result = runner.run_agent(
        investigation_id=inv_id,
        agent_name="red_team_agent",
        instructions={},
    )
    if result["success"]:
        print(f"   ✓ Adversarial audit: {result['result'].get('challenges_count', 0)} challenges, score: {result['result'].get('adversarial_score', 0)}")

    # Final status
    manifest = load_manifest(BASE_PATH, inv_id)
    inv_dir = BASE_PATH / "investigations" / inv_id
    files = list(inv_dir.rglob("*"))
    print(f"\n📁 Investigation files ({len(files)}):")
    for f in sorted(files):
        if f.is_file():
            rel = f.relative_to(inv_dir)
            size = f.stat().st_size
            print(f"   {rel} ({size} bytes)")

    print(f"\n✅ Pipeline complete: {inv_id}")
    return {"success": True, "investigation_id": inv_id}


def main():
    parser = argparse.ArgumentParser(description="Test Oracle V2 Pipeline")
    parser.add_argument("--actor", default="Zendaya", help="Actor name")
    parser.add_argument("--question", default="Can they carry a $25M drama?", help="Casting question")
    parser.add_argument("--max-videos", type=int, default=1, help="Max videos to analyze")
    args = parser.parse_args()

    try:
        result = run_pipeline(args.actor, args.question, args.max_videos)
        sys.exit(0 if result["success"] else 1)
    except KeyboardInterrupt:
        print("\n\n⏹ Interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
