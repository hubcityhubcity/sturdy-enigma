CAPTION_PRESETS = {
    "bpc_clean_editorial": {
        "font_name": "Arial",
        "font_size": 16,
        "primary_colour": "&H00FFFFFF",
        "outline_colour": "&H00000000",
        "back_colour": "&H80000000",
        "bold": 1,
        "outline": 2,
        "shadow": 1,
        "alignment": 2,
        "margin_v": 180,
    },
    "bpc_debate_heat": {
        "font_name": "Arial",
        "font_size": 18,
        "primary_colour": "&H00FFFFFF",
        "outline_colour": "&H00000000",
        "back_colour": "&H80000000",
        "bold": 1,
        "outline": 3,
        "shadow": 2,
        "alignment": 2,
        "margin_v": 160,
    },
    "bpc_story_mode": {
        "font_name": "Arial",
        "font_size": 15,
        "primary_colour": "&H00FFFFFF",
        "outline_colour": "&H00000000",
        "back_colour": "&H80000000",
        "bold": 1,
        "outline": 2,
        "shadow": 1,
        "alignment": 2,
        "margin_v": 190,
    },
}


def get_caption_preset(name: str | None) -> dict:
    return CAPTION_PRESETS.get(name or "", CAPTION_PRESETS["bpc_clean_editorial"])


def ffmpeg_force_style(name: str | None) -> str:
    preset = get_caption_preset(name)
    style_parts = [
        f"FontName={preset['font_name']}",
        f"FontSize={preset['font_size']}",
        f"PrimaryColour={preset['primary_colour']}",
        f"OutlineColour={preset['outline_colour']}",
        f"BackColour={preset['back_colour']}",
        f"Bold={preset['bold']}",
        f"Outline={preset['outline']}",
        f"Shadow={preset['shadow']}",
        f"Alignment={preset['alignment']}",
        f"MarginV={preset['margin_v']}",
    ]
    return ",".join(style_parts)


def list_caption_presets() -> list[dict]:
    return [
        {"name": name, "settings": settings}
        for name, settings in CAPTION_PRESETS.items()
    ]
