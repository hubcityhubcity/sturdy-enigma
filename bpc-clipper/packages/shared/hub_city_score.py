from dataclasses import dataclass, asdict


@dataclass
class ScoreInput:
    hook_strength: int
    context_clarity: int
    payoff_strength: int
    emotion: int
    debate_tension: int
    educational_value: int
    quotability: int
    audio_quality: int
    visual_suitability: int
    caption_readability: int
    risk_penalty: int = 0


WEIGHTS = {
    "hook_strength": 1.35,
    "context_clarity": 1.20,
    "payoff_strength": 1.25,
    "emotion": 0.85,
    "debate_tension": 0.90,
    "educational_value": 0.75,
    "quotability": 1.10,
    "audio_quality": 0.70,
    "visual_suitability": 0.65,
    "caption_readability": 0.70,
}


def clamp(value: int, minimum: int = 0, maximum: int = 10) -> int:
    return max(minimum, min(maximum, value))


def calculate_hub_city_score(score_input: ScoreInput) -> dict:
    values = asdict(score_input)
    weighted_total = 0.0
    max_total = 0.0

    for key, weight in WEIGHTS.items():
        weighted_total += clamp(values[key]) * weight
        max_total += 10 * weight

    raw_score = (weighted_total / max_total) * 100
    final_score = round(max(0, raw_score - clamp(score_input.risk_penalty) * 3))

    return {
        "score": final_score,
        "breakdown": values,
        "explanation": explain_score(score_input, final_score),
    }


def explain_score(score_input: ScoreInput, final_score: int) -> str:
    strengths = []
    if score_input.hook_strength >= 8:
        strengths.append("strong opening hook")
    if score_input.context_clarity >= 8:
        strengths.append("clear standalone context")
    if score_input.payoff_strength >= 8:
        strengths.append("strong payoff")
    if score_input.quotability >= 8:
        strengths.append("high quotability")
    if score_input.debate_tension >= 8:
        strengths.append("debate tension")

    if not strengths:
        strengths.append("balanced clip fundamentals")

    risk_note = " Risk penalty applied." if score_input.risk_penalty > 0 else ""
    return f"Hub City Score {final_score}: " + ", ".join(strengths) + "." + risk_note


if __name__ == "__main__":
    demo = ScoreInput(
        hook_strength=9,
        context_clarity=8,
        payoff_strength=9,
        emotion=7,
        debate_tension=8,
        educational_value=6,
        quotability=9,
        audio_quality=8,
        visual_suitability=7,
        caption_readability=8,
    )
    print(calculate_hub_city_score(demo))
