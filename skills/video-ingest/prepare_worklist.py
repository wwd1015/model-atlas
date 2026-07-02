"""video-ingest prepare-phase helper.

Deterministic. Parses transcripts (.vtt/.srt/.txt, or subtitles embedded in
the media container when ffmpeg is available), normalizes them to [mm:ss]
blocks, and writes the worklist + runbook for Claude Code's execute phase.
No LLM work happens here.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}
TRANSCRIPT_EXTS = [".vtt", ".srt", ".txt"]

_TS_VTT = re.compile(r"(\d+):(\d{2}):(\d{2})[.,](\d{3})")
_BLOCK_SECONDS = 60  # merge caption cues into ~1-minute blocks


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower())
    return text.strip("-")


def _to_seconds(m: re.Match) -> int:
    h, mi, s, _ms = (int(g) for g in m.groups())
    return h * 3600 + mi * 60 + s


def parse_captions(raw: str) -> list[tuple[int, str]]:
    """Parse VTT/SRT into (start_seconds, text) cues."""
    cues: list[tuple[int, str]] = []
    current_start: int | None = None
    buff: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if "-->" in line:
            if current_start is not None and buff:
                cues.append((current_start, " ".join(buff)))
            m = _TS_VTT.search(line)
            current_start = _to_seconds(m) if m else 0
            buff = []
        elif not line or line == "WEBVTT" or line.isdigit() or line.startswith("NOTE"):
            continue
        elif current_start is not None:
            buff.append(re.sub(r"<[^>]+>", "", line))  # strip cue markup
    if current_start is not None and buff:
        cues.append((current_start, " ".join(buff)))
    return cues


def normalize_transcript(path: Path) -> str:
    """Any supported transcript file → markdown with [mm:ss] blocks."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix in (".vtt", ".srt"):
        cues = parse_captions(raw)
        blocks: dict[int, list[str]] = {}
        for start, text in cues:
            blocks.setdefault(start // _BLOCK_SECONDS, []).append(text)
        lines = []
        for block in sorted(blocks):
            mm, ss = divmod(block * _BLOCK_SECONDS, 60)
            lines.append(f"**[{mm:02d}:{ss:02d}]** " + " ".join(blocks[block]))
        return "\n\n".join(lines)
    return raw  # .txt — keep as-is (may already carry timestamps)


def extract_embedded_subtitles(video: Path, out: Path) -> bool:
    """Try ffmpeg subtitle extraction; quietly report False if unavailable/absent."""
    if shutil.which("ffmpeg") is None:
        return False
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(video), "-map", "0:s:0", str(out)],
            capture_output=True, timeout=120,
        )
        return result.returncode == 0 and out.exists() and out.stat().st_size > 0
    except (subprocess.SubprocessError, OSError):
        return False


def find_transcript(media: Path, videos_dir: Path, artifacts_videos: Path) -> Path | None:
    for ext in TRANSCRIPT_EXTS:
        cand = media.with_suffix(ext)
        if cand.exists():
            return cand
    embedded = artifacts_videos / f"{media.stem}.embedded.vtt"
    if extract_embedded_subtitles(media, embedded):
        return embedded
    return None


def prepare(videos_dir: Path, artifacts_dir: Path, content_dir: Path,
            template_path: Path, channel: str) -> None:
    artifacts_videos = artifacts_dir / "videos"
    artifacts_videos.mkdir(parents=True, exist_ok=True)

    media_files = sorted(p for p in videos_dir.glob("*") if p.suffix.lower() in VIDEO_EXTS)
    # Standalone transcripts (no video next to them) are ingestable too.
    standalone = sorted(
        p for p in videos_dir.glob("*")
        if p.suffix.lower() in TRANSCRIPT_EXTS
        and not any(p.stem == m.stem for m in media_files)
    )

    worklist, skipped = [], []
    for media in media_files:
        transcript = find_transcript(media, videos_dir, artifacts_videos)
        if transcript is None:
            skipped.append(str(media))
            continue
        worklist.append((media, transcript))
    worklist += [(None, t) for t in standalone]

    entries = []
    for media, transcript in worklist:
        stem = (media or transcript).stem
        slug = slugify(stem)
        norm_path = artifacts_videos / f"{slug}_transcript.md"
        norm_path.write_text(normalize_transcript(transcript), encoding="utf-8")
        entries.append(
            {
                "slug": slug,
                "title": stem.replace("_", " ").replace("-", " ").strip(),
                "transcript_path": str(norm_path),
                "media_path": str(media) if media else str(transcript),
                "channel": channel,
                "output_path": str(content_dir / channel / f"{slug}.md"),
            }
        )

    worklist_path = artifacts_dir / "video_worklist.json"
    worklist_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    runbook = template_path.read_text(encoding="utf-8")
    runbook = (
        runbook.replace("{{worklist_path}}", str(worklist_path))
        .replace("{{total_count}}", str(len(entries)))
        .replace("{{channel}}", channel)
    )
    runbook_path = artifacts_dir / "video_runbook.md"
    runbook_path.write_text(runbook, encoding="utf-8")

    print(f"Worklist: {len(entries)} video(s) → {worklist_path}")
    if skipped:
        print("Skipped (no transcript found, none embedded):")
        for s in skipped:
            print(f"  - {s}")
    print(f"Runbook: {runbook_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare the video ingest runbook")
    parser.add_argument("--videos-dir", type=Path, default=Path("raw/videos"))
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--content-dir", type=Path, default=Path("content"))
    parser.add_argument("--channel", default="onboarding")
    parser.add_argument(
        "--template", type=Path,
        default=Path("skills/video-ingest/runbook_template.md"),
    )
    args = parser.parse_args()
    if not args.videos_dir.is_dir():
        raise SystemExit(f"No {args.videos_dir}/ directory — drop videos/transcripts there first.")
    prepare(args.videos_dir, args.artifacts_dir, args.content_dir, args.template, args.channel)


if __name__ == "__main__":
    main()
