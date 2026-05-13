#!/usr/bin/env python3
"""
Oracle — Main CLI entry point.

Usage:
    python oracle.py investigate --actor "Zendaya" --question "Can she carry a $25M drama?"
    python oracle.py status --id <investigation-id>
    python oracle.py run --id <investigation-id> --agent video_analysis
    python oracle.py list
"""

import argparse
import sys
from pathlib import Path

# Add oracle package to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from oracle.kernel import (
    AgentRunner,
    ContextStore,
    create_manifest,
    load_manifest,
    list_investigations,
    pause_for_human,
    investigation_dir,
)

BASE_PATH = SCRIPT_DIR


def cmd_investigate(args: argparse.Namespace) -> None:
    """Create a new investigation and optionally run the first agent."""
    manifest = create_manifest(
        base_path=BASE_PATH,
        actor=args.actor,
        client_question=args.question,
        human_initial_read=args.read or "",
    )
    print(f"\n🎭 Investigation created: {manifest['id']}")
    print(f"   Actor:    {manifest['actor']}")
    print(f"   Question: {manifest['client_question']}")
    print(f"   Path:     {investigation_dir(BASE_PATH, manifest['id'])}")

    if args.run_harvester:
        print("\n▶ Running Actor Harvester...")
        runner = AgentRunner(BASE_PATH)
        result = runner.run_agent(
            investigation_id=manifest["id"],
            agent_name="actor_harvester",
            instructions={"actor_name": args.actor},
        )
        if result["success"]:
            print(f"   ✓ Actor Harvester complete — {result['result']['videos_found']} videos found")
        else:
            print(f"   ✗ Actor Harvester failed: {result.get('error', 'unknown')}")

    if args.run_video:
        print("\n▶ Running Video Analysis Agent...")
        runner = AgentRunner(BASE_PATH)
        result = runner.run_agent(
            investigation_id=manifest["id"],
            agent_name="video_analysis",
            instructions={"focus": args.focus or ""},
        )
        if result["success"]:
            print(f"   ✓ Video Analysis complete — brief written to {result['result']['brief_path']}")
        else:
            print(f"   ✗ Video Analysis failed: {result.get('error', 'unknown')}")

    if args.run_v2_pipeline:
        print("\n▶ Running FULL V2 Pipeline (honest video + profiler)...")
        runner = AgentRunner(BASE_PATH)
        
        # Step 1: Video Analyzer v2 (honest pipeline)
        print("\n  [1/5] Video Analyzer v2 — real video download + Gemini analysis...")
        result = runner.run_agent(
            investigation_id=manifest["id"],
            agent_name="video_analyzer_v2",
            instructions={"max_videos": args.max_videos or 3},
        )
        if result["success"]:
            print(f"   ✓ Video Analyzer v2 complete — {result['result'].get('videos_analyzed', 0)} videos, {result['result'].get('observations_count', 0)} observations")
        else:
            print(f"   ✗ Video Analyzer v2 failed: {result.get('error', 'unknown')}")
        
        # Step 2: Knowledge Sync
        print("\n  [2/5] Knowledge Sync — building knowledge graph...")
        result = runner.run_agent(
            investigation_id=manifest["id"],
            agent_name="knowledge_sync",
            instructions={},
        )
        if result["success"]:
            print(f"   ✓ Knowledge Sync complete — {result['result'].get('claims_stored', 0)} claims stored")
        else:
            print(f"   ✗ Knowledge Sync failed: {result.get('error', 'unknown')}")
        
        # Step 3: Wiki Sync
        print("\n  [3/5] Wiki Sync — generating actor wiki...")
        result = runner.run_agent(
            investigation_id=manifest["id"],
            agent_name="wiki_sync",
            instructions={},
        )
        if result["success"]:
            print(f"   ✓ Wiki Sync complete — {result['result'].get('wiki_path', 'N/A')}")
        else:
            print(f"   ✗ Wiki Sync failed: {result.get('error', 'unknown')}")
        
        # Step 4: Psychological Profiler
        print("\n  [4/5] Psychological Profiler — deep behavioral analysis...")
        result = runner.run_agent(
            investigation_id=manifest["id"],
            agent_name="psychological_profiler",
            instructions={},
        )
        if result["success"]:
            dims = result['result'].get('dimensions', {})
            print(f"   ✓ Profiler complete — dimensions: {', '.join(f'{k}={v}' for k,v in dims.items())}")
        else:
            print(f"   ✗ Profiler failed: {result.get('error', 'unknown')}")
        
        # Step 5: Red Team Agent
        print("\n  [5/5] Red Team — adversarial audit...")
        result = runner.run_agent(
            investigation_id=manifest["id"],
            agent_name="red_team_agent",
            instructions={},
        )
        if result["success"]:
            print(f"   ✓ Red Team complete — {result['result'].get('challenges_count', 0)} challenges, score: {result['result'].get('adversarial_score', 0)}")
        else:
            print(f"   ✗ Red Team failed: {result.get('error', 'unknown')}")

    if args.pause:
        pause_for_human(
            base_path=BASE_PATH,
            investigation_id=manifest["id"],
            reason="Initial investigation complete. Review and give next instructions.",
        )


def cmd_status(args: argparse.Namespace) -> None:
    """Show the status of an investigation."""
    try:
        m = load_manifest(BASE_PATH, args.id)
    except FileNotFoundError:
        print(f"Investigation '{args.id}' not found.")
        sys.exit(1)

    print(f"\n🎭 Investigation: {m['id']}")
    print(f"   Actor:     {m['actor']}")
    print(f"   Question:  {m['client_question']}")
    print(f"   Status:    {m['status']}")
    print(f"   Created:   {m['created_at']}")
    print(f"   Updated:   {m['updated_at']}")

    print("\n   Pipeline:")
    for stage, agents in m["pipeline"].items():
        print(f"      {stage.upper()}:")
        for agent, status in agents.items():
            icon = "●" if status == "completed" else "○" if status == "not_started" else "◐"
            print(f"         {icon} {agent}: {status}")

    if m["agents_completed"]:
        print(f"\n   Completed: {', '.join(m['agents_completed'])}")
    if m["human_actions_required"]:
        print(f"   Human actions required: {', '.join(m['human_actions_required'])}")


def cmd_run(args: argparse.Namespace) -> None:
    """Run a specific agent for an investigation."""
    runner = AgentRunner(BASE_PATH)
    available = runner.list_agents()
    agent_names = [a["name"] for a in available]

    if args.agent not in agent_names:
        print(f"Agent '{args.agent}' not found. Available: {', '.join(agent_names)}")
        sys.exit(1)

    print(f"\n▶ Running {args.agent} for investigation {args.id}...")
    result = runner.run_agent(
        investigation_id=args.id,
        agent_name=args.agent,
        instructions={"focus": args.focus or ""},
    )

    if result["success"]:
        print(f"   ✓ {args.agent} complete")
        if "brief_path" in result.get("result", {}):
            print(f"   📄 Output: {result['result']['brief_path']}")
    else:
        print(f"   ✗ Failed: {result.get('error', 'unknown')}")


def cmd_list(args: argparse.Namespace) -> None:
    """List all investigations."""
    investigations = list_investigations(BASE_PATH)
    if not investigations:
        print("No investigations found.")
        return

    print(f"\n🎭 {len(investigations)} investigation(s):")
    for inv in investigations:
        status_icon = "✓" if inv["status"] == "completed" else "⏸" if "paused" in inv["status"] else "⋯"
        print(f"   [{status_icon}] {inv['id']} — {inv['actor']} ({inv['status']})")


def cmd_human(args: argparse.Namespace) -> None:
    """Pause for human input on an investigation."""
    result = pause_for_human(
        base_path=BASE_PATH,
        investigation_id=args.id,
        reason=args.reason or "Human review requested via CLI.",
    )
    print(f"\n   Received: {result['human_instructions']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="oracle",
        description="Oracle — Actor Assessment Intelligence System",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # investigate
    p_inv = subparsers.add_parser("investigate", help="Create a new investigation")
    p_inv.add_argument("--actor", required=True, help="Actor name")
    p_inv.add_argument("--question", required=True, help="Client casting question")
    p_inv.add_argument("--read", default="", help="Human initial read/instinct")
    p_inv.add_argument("--run-harvester", action="store_true", help="Auto-run Actor Harvester")
    p_inv.add_argument("--run-video", action="store_true", help="Auto-run Video Analysis (legacy)")
    p_inv.add_argument("--run-v2-pipeline", action="store_true", help="Run full honest V2 pipeline")
    p_inv.add_argument("--max-videos", type=int, default=3, help="Max videos to analyze in V2 pipeline")
    p_inv.add_argument("--focus", default="", help="Focus area for video analysis")
    p_inv.add_argument("--pause", action="store_true", help="Pause for human input after")
    p_inv.set_defaults(func=cmd_investigate)

    # status
    p_status = subparsers.add_parser("status", help="Show investigation status")
    p_status.add_argument("--id", required=True, help="Investigation ID")
    p_status.set_defaults(func=cmd_status)

    # run
    p_run = subparsers.add_parser("run", help="Run an agent")
    p_run.add_argument("--id", required=True, help="Investigation ID")
    p_run.add_argument("--agent", required=True, help="Agent name")
    p_run.add_argument("--focus", default="", help="Focus instructions")
    p_run.set_defaults(func=cmd_run)

    # list
    p_list = subparsers.add_parser("list", help="List all investigations")
    p_list.set_defaults(func=cmd_list)

    # human
    p_human = subparsers.add_parser("human", help="Pause for human input")
    p_human.add_argument("--id", required=True, help="Investigation ID")
    p_human.add_argument("--reason", default="", help="Reason for pause")
    p_human.set_defaults(func=cmd_human)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
