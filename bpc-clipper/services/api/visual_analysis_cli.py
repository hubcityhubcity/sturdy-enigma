import argparse
import json
from pathlib import Path

from visual_runtime import get_visual_analyzer


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Titan visual-analysis plan for a local video file.")
    parser.add_argument("media_path")
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--end", type=float, default=None)
    parser.add_argument("--sample-hz", type=float, default=2.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    analyzer = get_visual_analyzer()
    plan = analyzer.analyze_video(
        Path(args.media_path),
        start_seconds=args.start,
        end_seconds=args.end,
        sample_hz=args.sample_hz,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan.as_dict(), indent=2), encoding="utf-8")
    print(json.dumps({
        "provider": analyzer.provider_name,
        "output": str(output),
        "shots": len(plan.shots),
        "keyframes": len(plan.keyframes),
        "warnings": plan.warnings,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
