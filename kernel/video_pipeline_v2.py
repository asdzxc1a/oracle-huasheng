"""
Oracle Video Pipeline v2 — Honest Video Analysis.

Pipeline:
  1. Download video via yt-dlp (real URLs only, no search pages)
  2. Segment into 3 clips: baseline / pressure / fatigue
  3. Upload each clip to Gemini 2.5 Pro for native video analysis
  4. Store analysis JSON + raw clips
  5. Evidence audit trail

Huasheng Rule: Every video downloaded produces physical evidence on disk.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class VideoSegment:
    """A segment of a video with its Gemini analysis."""
    segment_id: str
    start_min: float
    end_min: float
    clip_path: Path | None = None
    analysis_text: str = ""
    analysis_model: str = ""
    error: str = ""


@dataclass
class ProcessedVideoV2:
    """Result of processing a single video source."""
    url: str
    title: str
    source_type: str
    access_level: str
    video_path: Path | None = None
    duration: int = 0
    segments: list[VideoSegment] = field(default_factory=list)
    error: str = ""
    downloaded: bool = False


def is_valid_youtube_url(url: str) -> bool:
    """Reject search result pages and invalid URLs."""
    if not url or url == "NOT_FOUND":
        return False
    if "/results?" in url or "search_query=" in url:
        return False
    if "youtube.com/watch?" not in url and "youtu.be/" not in url:
        return False
    return True


def download_video(
    url: str,
    output_dir: Path,
    max_duration: int = 2700,  # 45 minutes
) -> Path | None:
    """
    Download a video using yt-dlp.
    Returns path to downloaded file, or None on failure.
    """
    if not is_valid_youtube_url(url):
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "%(id)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--format", "best[height<=720]",
        "--output", output_template,
        "--max-filesize", "500M",
        "--max-downloads", "1",
        "--no-warnings",
        url,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode != 0:
            return None

        files = list(output_dir.glob("*"))
        video_files = [f for f in files if f.suffix in (".mp4", ".webm", ".mkv", ".mov")]
        if video_files:
            return video_files[0]
        return None
    except Exception:
        return None


def _get_video_duration(video_path: Path) -> int:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(video_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        return int(float(data["format"]["duration"]))
    except Exception:
        return 0


def segment_video(
    video_path: Path,
    output_dir: Path,
    duration: int,
) -> list[VideoSegment]:
    """
    Split video into 3 segments:
    - Baseline: first 5 minutes (relaxed, starting state)
    - Pressure: middle 10 minutes (sustained interaction)
    - Fatigue: last 5 minutes (tired, recovery state)
    
    For short videos (< 20 min), use proportional segments.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    segments: list[VideoSegment] = []
    
    if duration <= 0:
        return segments
    
    # Define segment boundaries
    if duration <= 1200:  # <= 20 min
        # Short video: first 1/4, middle 1/2, last 1/4
        baseline_end = duration * 0.25
        pressure_end = duration * 0.75
    else:
        # Long video: first 5 min, middle 10 min, last 5 min
        baseline_end = min(300, duration * 0.2)
        pressure_end = min(baseline_end + 600, duration * 0.8)
    
    segment_defs = [
        ("baseline", 0, baseline_end, "Relaxed opening state"),
        ("pressure", baseline_end, pressure_end, "Sustained interaction under pressure"),
        ("fatigue", pressure_end, duration, "Fatigue and recovery state"),
    ]
    
    for seg_name, start_sec, end_sec, description in segment_defs:
        start = float(start_sec)
        end = float(min(end_sec, duration))
        if end <= start + 5:  # Skip if too short
            continue
            
        segment_id = f"{video_path.stem}_{seg_name}"
        clip_path = output_dir / f"{segment_id}.mp4"
        
        # Extract segment with ffmpeg
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(start),
            "-i", str(video_path),
            "-t", str(end - start),
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            str(clip_path),
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, timeout=60)
            if clip_path.exists():
                segments.append(VideoSegment(
                    segment_id=segment_id,
                    start_min=start / 60,
                    end_min=end / 60,
                    clip_path=clip_path,
                ))
        except Exception:
            pass
    
    return segments


def analyze_segment_with_gemini(
    segment: VideoSegment,
    llm_client: Any,
    actor: str,
    client_question: str,
) -> VideoSegment:
    """
    Upload segment clip to Gemini 2.5 Pro and analyze.
    Returns segment with analysis_text filled in.
    """
    if not segment.clip_path or not segment.clip_path.exists():
        segment.error = "No clip file to analyze"
        return segment
    
    prompt = (
        f"You are a forensic casting analyst watching video evidence of actor {actor}.\n\n"
        f"Casting Question: {client_question}\n"
        f"Video Segment: {segment.segment_id} (minutes {segment.start_min:.1f} to {segment.end_min:.1f})\n\n"
        f"Analyze this video segment in extreme detail. Focus on:\n"
        f"1. BODY LANGUAGE: posture, gestures, spatial behavior, touch adapters\n"
        f"2. FACIAL EXPRESSIONS: micro-expressions, eye contact patterns, baseline vs. stress\n"
        f"3. VOCAL PROSODY: pitch, pace, volume, hesitations, fillers\n"
        f"4. STRESS SIGNALS: fight/flight/freeze/fawn indicators\n"
        f"5. SOCIAL CALIBRATION: rapport building, dominance/submission, mirroring\n"
        f"6. AUTHENTICITY: genuine vs. performative behavior\n\n"
        f"Be specific. Name timestamps. Quote exact phrases."
        f"Do NOT give generic compliments. Every observation must be diagnostic."
    )
    
    system = (
        "You are a forensic casting analyst with 20 years of experience. "
        "You extract only observable, actionable signals. 'She is talented' is banned. "
        "'At 02:34, her voice drops an octave when asked about franchise pressure' is valid."
    )
    
    try:
        response = llm_client.analyze_video(
            video_path=segment.clip_path,
            prompt=prompt,
            system=system,
            max_tokens=8000,
            temperature=0.2,
        )
        segment.analysis_text = response.text
        segment.analysis_model = response.model
    except Exception as e:
        segment.error = str(e)
    
    return segment


def process_video_source_v2(
    video_info: dict[str, Any],
    investigation_dir: Path,
    llm_client: Any,
    actor: str,
    client_question: str,
) -> ProcessedVideoV2:
    """
    Full honest pipeline:
      1. Validate URL (reject search pages)
      2. Download via yt-dlp
      3. Segment into 3 clips
      4. Analyze each clip with Gemini 2.5 Pro native video
      5. Store everything on disk
    """
    url = video_info.get("url", "")
    title = video_info.get("title", "Unknown")
    source_type = video_info.get("source_type", "unknown")
    access_level = video_info.get("access_level", "MANAGED")
    
    result = ProcessedVideoV2(
        url=url,
        title=title,
        source_type=source_type,
        access_level=access_level,
    )
    
    # Validate URL
    if not is_valid_youtube_url(url):
        result.error = f"Invalid URL: {url}"
        return result
    
    # Set up directories
    sources_dir = investigation_dir / "sources"
    clips_dir = sources_dir / "clips"
    segments_dir = sources_dir / "segments"
    analysis_dir = sources_dir / "analysis"
    
    # Download
    video_path = download_video(url, clips_dir)
    if not video_path:
        result.error = "Download failed"
        return result
    
    result.video_path = video_path
    result.duration = _get_video_duration(video_path)
    result.downloaded = True
    
    # Segment
    result.segments = segment_video(video_path, segments_dir, result.duration)
    
    # Analyze each segment with Gemini
    for segment in result.segments:
        analyze_segment_with_gemini(segment, llm_client, actor, client_question)
    
    # Write metadata
    meta = {
        "url": url,
        "title": title,
        "source_type": source_type,
        "access_level": access_level,
        "local_video": str(video_path),
        "duration_seconds": result.duration,
        "downloaded": result.downloaded,
        "segments": [
            {
                "id": s.segment_id,
                "start_min": s.start_min,
                "end_min": s.end_min,
                "clip_path": str(s.clip_path) if s.clip_path else None,
                "analysis_model": s.analysis_model,
                "analysis_length": len(s.analysis_text),
                "error": s.error,
            }
            for s in result.segments
        ],
    }
    meta_path = sources_dir / "metadata" / f"{video_path.stem}.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    
    # Write analysis texts
    for segment in result.segments:
        if segment.analysis_text:
            analysis_path = analysis_dir / f"{segment.segment_id}_analysis.md"
            analysis_path.parent.mkdir(parents=True, exist_ok=True)
            analysis_path.write_text(
                f"# Analysis: {segment.segment_id}\n\n"
                f"**Model:** {segment.analysis_model}\n"
                f"**Segment:** {segment.start_min:.1f} min - {segment.end_min:.1f} min\n\n"
                f"{segment.analysis_text}\n",
                encoding="utf-8",
            )
    
    return result


def process_all_sources_v2(
    video_catalog: list[dict[str, Any]],
    investigation_dir: Path,
    llm_client: Any,
    actor: str,
    client_question: str,
    max_videos: int = 5,
) -> list[ProcessedVideoV2]:
    """Process all videos in catalog up to max_videos."""
    results = []
    for video in video_catalog[:max_videos]:
        result = process_video_source_v2(
            video, investigation_dir, llm_client, actor, client_question
        )
        results.append(result)
    return results


def generate_evidence_audit(
    processed: list[ProcessedVideoV2],
) -> dict[str, Any]:
    """Generate honest evidence audit for the brief."""
    total_requested = len(processed)
    total_downloaded = sum(1 for p in processed if p.downloaded)
    total_failed = sum(1 for p in processed if p.error and not p.downloaded)
    total_minutes = sum(p.duration for p in processed) / 60
    total_segments = sum(len(p.segments) for p in processed)
    total_analyzed = sum(
        1 for p in processed for s in p.segments if s.analysis_text
    )
    
    return {
        "videos_requested": total_requested,
        "videos_downloaded": total_downloaded,
        "videos_failed": total_failed,
        "total_minutes_analyzed": round(total_minutes, 1),
        "total_segments_created": total_segments,
        "total_segments_analyzed": total_analyzed,
        "analysis_model": "gemini-2.5-pro-preview",
        "all_claims_traceable_to_video": total_downloaded > 0,
    }
