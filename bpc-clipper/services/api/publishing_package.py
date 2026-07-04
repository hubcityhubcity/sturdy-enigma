from __future__ import annotations

import re

from models import CandidateClip, EditTimeline, ExportRecord


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def trim(value: str, limit: int) -> str:
    value = clean_text(value)
    if len(value) <= limit:
        return value
    return f"{value[: max(1, limit - 1)].rsplit(' ', 1)[0].rstrip(' ,.;:')}…"


def build_publishing_package(export: ExportRecord, edit: EditTimeline, candidate: CandidateClip | None) -> dict:
    hook = clean_text(edit.hook_text or (candidate.excerpt if candidate else ""))
    short_hook = trim(hook, 90)
    topic = short_hook.rstrip("?!.") or "This moment"
    category = (candidate.category if candidate else "high_retention").replace("_", " ")
    titles = list(dict.fromkeys([
        trim(topic, 90),
        trim(f"{topic}: The Part People Miss", 90),
        trim(f"Why This {category.title()} Moment Hits", 90),
    ]))
    captions = list(dict.fromkeys([
        f"{trim(hook, 180)}\n\nFull conversation clipped with Titan Clipper AI.".strip(),
        f"A {category} worth sitting with. {trim(hook, 180)}".strip(),
        f"Watch the full point before you judge it. {trim(hook, 180)}".strip(),
    ]))
    return {
        "export_id": export.id,
        "candidate_id": candidate.id if candidate else None,
        "title_options": titles,
        "caption_options": captions,
        "hashtags": ["#podcastclips", "#shorts", "#reels"],
        "clip_summary": trim(hook, 220),
        "duration_seconds": round(max(0, edit.end_seconds - edit.start_seconds), 1),
        "publishing_checklist": [
            "Watch the first three seconds with sound on and captions visible.",
            "Choose a title and caption option, then adjust it to match the creator’s voice.",
            "Confirm names, claims, music rights, and sensitive context before posting.",
            "Upload the vertical MP4 and review the native platform preview before publishing.",
        ],
        "recommended_title": titles[0] if titles else short_hook,
        "recommended_caption": captions[0] if captions else hook,
    }
