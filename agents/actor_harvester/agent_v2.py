"""
Actor Harvester v2 — Finds real YouTube URLs, not search pages.

Uses yt-dlp to search YouTube and extract actual watch?v= URLs.
Rejects search result pages, playlists, and shorts.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def _run_yt_dlp_search(query: str, max_results: int = 10) -> list[dict[str, str]]:
    """
    Use yt-dlp to search YouTube and return real video URLs.
    Returns list of {url, title, duration} dicts.
    """
    cmd = [
        "yt-dlp",
        "--default-search", "ytsearch",
        "--print", "%(webpage_url)s||%(title)s||%(duration)s||%(id)s",
        "--playlist-end", str(max_results),
        "--no-download",
        "--no-playlist",
        "--no-warnings",
        f"ytsearch{max_results}:{query}",
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return []
        
        videos = []
        for line in result.stdout.strip().split("\n"):
            if "||" not in line:
                continue
            parts = line.split("||")
            if len(parts) >= 4:
                url = parts[0].strip()
                title = parts[1].strip()
                duration = parts[2].strip()
                video_id = parts[3].strip()
                
                # Validate: must be a real watch URL
                if "youtube.com/watch?" not in url and "youtu.be/" not in url:
                    continue
                if "/results?" in url or "search_query=" in url:
                    continue
                if "/shorts/" in url:
                    continue
                if "/playlist?" in url:
                    continue
                
                videos.append({
                    "url": url,
                    "title": title,
                    "duration": duration,
                    "video_id": video_id,
                })
        
        return videos
    except Exception:
        return []


def classify_source(title: str, query: str) -> dict[str, str]:
    """Classify a video by source type and access level based on title."""
    title_lower = title.lower()
    
    # Source type classification
    if any(k in title_lower for k in ["comic con", "comic-con", "sdcc", "panel", "q&a", "fan expo"]):
        source_type = "festival_qa"
    elif any(k in title_lower for k in ["tonight show", "fallon", "kimmel", "colbert", "graham norton", "ellen"]):
        source_type = "late_night"
    elif any(k in title_lower for k in ["behind the scenes", "bts", "inside the episode", "making of"]):
        source_type = "bts"
    elif any(k in title_lower for k in ["interview", "conversation", "talks", "podcast", "off menu", "variety"]):
        source_type = "interview"
    elif any(k in title_lower for k in ["red carpet", "premiere", "premiere", "arrival"]):
        source_type = "red_carpet"
    elif any(k in title_lower for k in ["audition", "screen test", "casting"]):
        source_type = "audition"
    elif any(k in title_lower for k in ["scene", "clip", "trailer", "official clip"]):
        source_type = "film_scene"
    else:
        source_type = "interview"
    
    # Access level classification
    if source_type in ["bts", "audition"]:
        access_level = "RAW"
    elif source_type in ["late_night"]:
        access_level = "SCRIPTED"
    else:
        access_level = "MANAGED"
    
    return {"source_type": source_type, "access_level": access_level}


def run(
    investigation_id: str,
    instructions: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Harvest real video URLs for an actor.
    Returns video catalog with actual watch?v= URLs.
    """
    actor = instructions.get("actor_name", context.get("actor", "Unknown"))
    inv_dir = Path(context["investigation_dir"])
    
    # Build search queries for different contexts
    queries = [
        f'{actor} interview',
        f'{actor} Comic Con panel Q&A',
        f'{actor} behind the scenes',
        f'{actor} late night show interview',
        f'{actor} red carpet',
    ]
    
    all_videos: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    
    for query in queries:
        results = _run_yt_dlp_search(query, max_results=5)
        for video in results:
            vid_id = video.get("video_id", "")
            if vid_id in seen_ids:
                continue
            seen_ids.add(vid_id)
            
            classification = classify_source(video["title"], query)
            
            all_videos.append({
                "url": video["url"],
                "title": video["title"],
                "source_type": classification["source_type"],
                "access_level": classification["access_level"],
                "duration": video.get("duration", "unknown"),
                "video_id": vid_id,
            })
        
        if len(all_videos) >= 10:
            break
    
    # Limit to top 5 by relevance (prioritize RAW and MANAGED over SCRIPTED)
    priority = {"RAW": 0, "MANAGED": 1, "SCRIPTED": 2}
    all_videos.sort(key=lambda v: priority.get(v["access_level"], 3))
    selected = all_videos[:5]
    
    # Write catalog
    catalog = {
        "actor": actor,
        "investigation_id": investigation_id,
        "videos_found": len(all_videos),
        "videos_selected": len(selected),
        "videos": selected,
    }
    
    catalog_path = inv_dir / "research" / "video-catalog.json"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    
    # Write human-readable catalog
    md_lines = [
        f"# Video Catalog — {actor}",
        f"**Investigation:** {investigation_id}",
        f"**Videos Found:** {len(all_videos)}",
        f"**Videos Selected:** {len(selected)}",
        "",
        "| # | Title | Type | Access | Duration | URL |",
        "|---|---|---|---|---|---|",
    ]
    for i, v in enumerate(selected, 1):
        md_lines.append(
            f"| {i} | {v['title']} | {v['source_type']} | {v['access_level']} | {v.get('duration', 'unknown')} | [Link]({v['url']}) |"
        )
    
    md_path = inv_dir / "research" / "video-catalog.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    
    return {
        "success": True,
        "videos_found": len(all_videos),
        "videos_selected": len(selected),
        "catalog_path": str(catalog_path),
    }
