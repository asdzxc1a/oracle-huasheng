"""
Oracle Video Pipeline — Extract, Process, Transcribe

Huasheng Rule: "Research without files is research that never happened."
This pipeline ensures every video source produces physical evidence on disk:
- Downloaded video file
- Extracted frames (PNG)
- Audio transcript ( Whisper )
- Metadata JSON
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProcessedVideo:
    """Result of processing a single video source."""

    url: str
    title: str
    source_type: str
    access_level: str
    video_path: Path | None = None
    frames_dir: Path | None = None
    transcript_path: Path | None = None
    metadata_path: Path | None = None
    duration: int = 0
    frame_count: int = 0
    transcript_text: str = ""
    error: str = ""


def download_video(
    url: str,
    output_dir: Path,
    max_duration: int = 600,
) -> Path | None:
    """
    Download a video using yt-dlp.
    Returns path to downloaded file, or None on failure.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "%(id)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--format", "best[height<=720]",  # 720p to save bandwidth/time
        "--output", output_template,
        "--max-filesize", "500M",
        "--no-warnings",
        url,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            # Log error but don't crash
            return None

        # Find the downloaded file
        files = list(output_dir.glob("*"))
        video_files = [f for f in files if f.suffix in (".mp4", ".webm", ".mkv", ".mov")]
        if video_files:
            return video_files[0]
        return None
    except Exception:
        return None


def extract_frames(
    video_path: Path,
    output_dir: Path,
    num_frames: int = 12,
) -> list[Path]:
    """
    Extract evenly-spaced frames from a video using ffmpeg.
    Returns list of frame paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get video duration
    duration = _get_video_duration(video_path)
    if duration <= 0:
        return []

    # Calculate frame timestamps
    if duration <= 30:
        # Short video: extract frames every 2 seconds
        timestamps = list(range(2, int(duration), 2))
    else:
        # Longer video: extract evenly spaced frames
        step = duration / (num_frames + 1)
        timestamps = [step * (i + 1) for i in range(min(num_frames, 20))]

    frames = []
    for i, ts in enumerate(timestamps):
        frame_path = output_dir / f"frame_{i:03d}_{ts:.1f}s.png"
        cmd = [
            "ffmpeg",
            "-ss", str(ts),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            "-y",
            str(frame_path),
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=30)
            if frame_path.exists():
                frames.append(frame_path)
        except Exception:
            continue

    return frames


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


def extract_audio(video_path: Path, output_dir: Path) -> Path | None:
    """Extract audio track from video as MP3."""
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_path = output_dir / f"{video_path.stem}.mp3"

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",
        "-acodec", "libmp3lame",
        "-q:a", "4",
        "-y",
        str(audio_path),
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=60)
        return audio_path if audio_path.exists() else None
    except Exception:
        return None


def transcribe_audio(
    audio_path: Path,
    openai_key: str | None = None,
) -> str:
    """
    Transcribe audio using OpenAI Whisper.
    Returns transcript text, or empty string on failure.
    """
    api_key = openai_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return ""

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        with open(audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
            )
        return transcript.text
    except Exception:
        return ""


def process_video_source(
    video_info: dict[str, Any],
    investigation_dir: Path,
    extract_frames_flag: bool = True,
    transcribe_flag: bool = True,
) -> ProcessedVideo:
    """
    Full pipeline: download → extract frames → transcribe → metadata.
    Writes all outputs to investigation_dir/sources/.
    """
    url = video_info.get("url", "")
    title = video_info.get("title", "Unknown")
    source_type = video_info.get("source_type", "unknown")
    access_level = video_info.get("access_level", "MANAGED")

    result = ProcessedVideo(
        url=url,
        title=title,
        source_type=source_type,
        access_level=access_level,
    )

    if not url or url == "NOT_FOUND":
        result.error = "No valid URL"
        return result

    # Set up source directories
    sources_dir = investigation_dir / "sources"
    clips_dir = sources_dir / "clips"
    frames_dir = sources_dir / "screenshots"
    transcripts_dir = sources_dir / "transcripts"

    # Download
    video_path = download_video(url, clips_dir)
    if not video_path:
        result.error = "Download failed"
        return result

    result.video_path = video_path
    result.duration = _get_video_duration(video_path)

    # Extract frames
    if extract_frames_flag:
        frame_dir = frames_dir / video_path.stem
        frames = extract_frames(video_path, frame_dir)
        result.frames_dir = frame_dir
        result.frame_count = len(frames)

    # Transcribe
    if transcribe_flag:
        audio_path = extract_audio(video_path, clips_dir)
        if audio_path:
            transcript = transcribe_audio(audio_path)
            if transcript:
                transcript_path = transcripts_dir / f"{video_path.stem}.txt"
                transcript_path.parent.mkdir(parents=True, exist_ok=True)
                transcript_path.write_text(transcript, encoding="utf-8")
                result.transcript_path = transcript_path
                result.transcript_text = transcript

    # Write metadata
    meta = {
        "url": url,
        "title": title,
        "source_type": source_type,
        "access_level": access_level,
        "local_video": str(video_path) if video_path else None,
        "duration_seconds": result.duration,
        "frames_extracted": result.frame_count,
        "frames_dir": str(result.frames_dir) if result.frames_dir else None,
        "transcript_path": str(result.transcript_path) if result.transcript_path else None,
        "transcript_preview": result.transcript_text[:500] if result.transcript_text else "",
    }
    meta_path = sources_dir / "metadata" / f"{video_path.stem}.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    result.metadata_path = meta_path

    return result


def process_all_sources(
    video_catalog: list[dict[str, Any]],
    investigation_dir: Path,
    max_videos: int = 3,
) -> list[ProcessedVideo]:
    """
    Process all videos in a catalog up to max_videos.
    Returns list of ProcessedVideo results.
    """
    results = []
    for video in video_catalog[:max_videos]:
        result = process_video_source(video, investigation_dir)
        results.append(result)
    return results


def get_source_evidence(
    investigation_dir: Path,
) -> dict[str, Any]:
    """
    Compile all source evidence from an investigation directory.
    Returns dict with frames, transcripts, and metadata.
    """
    sources_dir = investigation_dir / "sources"
    evidence = {
        "frames": [],
        "transcripts": {},
        "metadata": [],
    }

    # Collect frames
    screenshots_dir = sources_dir / "screenshots"
    if screenshots_dir.exists():
        for frame_dir in screenshots_dir.iterdir():
            if frame_dir.is_dir():
                frames = sorted(frame_dir.glob("*.png"))
                evidence["frames"].extend([str(f) for f in frames])

    # Collect transcripts
    transcripts_dir = sources_dir / "transcripts"
    if transcripts_dir.exists():
        for transcript_file in transcripts_dir.glob("*.txt"):
            evidence["transcripts"][transcript_file.stem] = transcript_file.read_text(
                encoding="utf-8"
            )

    # Collect metadata
    metadata_dir = sources_dir / "metadata"
    if metadata_dir.exists():
        for meta_file in metadata_dir.glob("*.json"):
            evidence["metadata"].append(json.loads(meta_file.read_text(encoding="utf-8")))

    return evidence
