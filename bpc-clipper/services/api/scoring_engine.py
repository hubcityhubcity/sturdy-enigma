from dataclasses import dataclass
import re

from models import TranscriptSegment


@dataclass
class ScoreSignal:
    name: str
    score: int
    explanation: str


@dataclass
class ClipScoreBreakdown:
    hook: ScoreSignal
    curiosity: ScoreSignal
    emotion: ScoreSignal
    debate: ScoreSignal
    story: ScoreSignal
    retention: ScoreSignal
    context: ScoreSignal
    payoff: ScoreSignal
    overall: ScoreSignal

    def as_dict(self) -> dict:
        return {
            "hook": self.hook.__dict__,
            "curiosity": self.curiosity.__dict__,
            "emotion": self.emotion.__dict__,
            "debate": self.debate.__dict__,
            "story": self.story.__dict__,
            "retention": self.retention.__dict__,
            "context": self.context.__dict__,
            "payoff": self.payoff.__dict__,
            "overall": self.overall.__dict__,
            "engine": "titan_brain_v2",
        }


def clamp_score(value: int | float) -> int:
    return max(0, min(100, round(value)))


def text_words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9']+", text.lower())


def contains_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def starts_with_dependency(text: str) -> bool:
    opening = " ".join(text_words(text)[:4])
    return any(opening.startswith(term) for term in ["and", "but", "so", "because", "this", "that", "they", "he", "she", "it", "then"])


def score_hook(segment: TranscriptSegment) -> ScoreSignal:
    text = segment.text.strip()
    words = text_words(text)
    score = 42
    reasons = []
    if text.endswith("?") or contains_any(text, ["let me ask", "what if", "why", "how come", "answer this"]):
        score += 18
        reasons.append("opens with a question or challenge")
    if contains_any(text, ["nobody", "everybody", "never", "always", "truth", "mistake", "secret", "here is why"]):
        score += 14
        reasons.append("uses high-curiosity language")
    if contains_any(text, ["listen", "look", "here's", "here is", "the thing is", "watch this"]):
        score += 9
        reasons.append("has a direct attention cue")
    if 8 <= len(words) <= 32:
        score += 9
        reasons.append("opens at a short-form friendly length")
    if starts_with_dependency(text):
        score -= 12
        reasons.append("starts mid-thought and may need setup")
    if len(words) > 70:
        score -= 10
        reasons.append("opening may be too wordy")
    return ScoreSignal("hook", clamp_score(score), "; ".join(reasons) or "baseline hook strength")


def score_curiosity(segment: TranscriptSegment) -> ScoreSignal:
    text = segment.text
    score = 38
    reasons = []
    phrases = ["what happened", "nobody tells", "the reason", "the problem", "the truth", "secret", "mistake", "before you", "what people miss"]
    if contains_any(text, phrases):
        score += 25
        reasons.append("creates an information gap")
    if "?" in text:
        score += 12
        reasons.append("question creates an open loop")
    if contains_any(text, ["but", "however", "until", "unless", "turns out"]):
        score += 10
        reasons.append("contrast language promises a payoff")
    if contains_any(text, ["because", "that's why", "that is why", "the answer is"]):
        score += 7
        reasons.append("teases or begins resolving a question")
    return ScoreSignal("curiosity", clamp_score(score), "; ".join(reasons) or "limited curiosity trigger detected")


def score_emotion(segment: TranscriptSegment) -> ScoreSignal:
    text = segment.text
    score = 34
    reasons = []
    emotional_terms = [
        "love", "hate", "angry", "hurt", "pain", "fear", "proud", "cry", "laugh", "crazy", "wild",
        "powerful", "real", "honest", "respect", "disrespect", "broke", "rich", "survive", "win",
        "embarrassed", "grateful", "frustrated", "heartbroken", "scared",
    ]
    hits = sum(1 for term in emotional_terms if term in text.lower())
    score += min(38, hits * 8)
    if hits:
        reasons.append(f"contains {hits} emotional trigger(s)")
    if "!" in text:
        score += 7
        reasons.append("punctuation suggests intensity")
    if contains_any(text, ["i felt", "i was", "it hurt", "i cried", "i couldn't believe"]):
        score += 10
        reasons.append("uses first-person emotional framing")
    return ScoreSignal("emotion", clamp_score(score), "; ".join(reasons) or "mostly neutral emotional language")


def score_debate(segment: TranscriptSegment) -> ScoreSignal:
    text = segment.text
    score = 28
    reasons = []
    debate_terms = ["wrong", "disagree", "argue", "debate", "but", "not true", "challenge", "prove", "question", "lie", "cap"]
    hits = sum(1 for term in debate_terms if term in text.lower())
    score += min(42, hits * 9)
    if hits:
        reasons.append(f"contains {hits} conflict/debate signal(s)")
    if contains_any(text, ["let me ask", "answer this", "you cannot", "you can't tell me"]):
        score += 14
        reasons.append("uses a direct challenge format")
    if contains_any(text, ["i agree", "i disagree", "the problem with"]):
        score += 8
        reasons.append("states a clear position")
    return ScoreSignal("debate", clamp_score(score), "; ".join(reasons) or "low debate tension")


def score_story(segment: TranscriptSegment) -> ScoreSignal:
    text = segment.text
    score = 34
    reasons = []
    story_terms = ["when i", "one day", "then", "after", "before", "because", "remember", "started", "ended", "at the time"]
    hits = sum(1 for term in story_terms if term in text.lower())
    score += min(36, hits * 8)
    if hits:
        reasons.append(f"contains {hits} story structure signal(s)")
    duration = segment.end_seconds - segment.start_seconds
    if 20 <= duration <= 60:
        score += 10
        reasons.append("duration fits a short story arc")
    if contains_any(text, ["then i realized", "what happened next", "from that day"]):
        score += 9
        reasons.append("contains a narrative turn")
    return ScoreSignal("story", clamp_score(score), "; ".join(reasons) or "limited story structure")


def score_retention(segment: TranscriptSegment) -> ScoreSignal:
    text = segment.text
    words = text_words(text)
    duration = max(1.0, segment.end_seconds - segment.start_seconds)
    words_per_second = len(words) / duration
    score = 48
    reasons = []
    if 1.8 <= words_per_second <= 3.4:
        score += 18
        reasons.append("speaking pace is short-form friendly")
    elif words_per_second < 1.2:
        score -= 12
        reasons.append("pace may feel slow")
    elif words_per_second > 4.0:
        score -= 9
        reasons.append("pace may feel rushed")
    if 18 <= duration <= 55:
        score += 14
        reasons.append("duration fits Shorts/TikTok retention")
    elif duration < 10:
        score -= 10
        reasons.append("may be too short to land a full point")
    elif duration > 75:
        score -= 13
        reasons.append("clip may run long")
    filler_count = sum(words.count(word) for word in ["um", "uh", "like"])
    if filler_count > 4:
        score -= min(14, filler_count * 2)
        reasons.append("filler words may reduce retention")
    return ScoreSignal("retention", clamp_score(score), "; ".join(reasons) or "baseline retention profile")


def score_context(segment: TranscriptSegment) -> ScoreSignal:
    text = segment.text.strip()
    words = text_words(text)
    score = 58
    reasons = []
    if starts_with_dependency(text):
        score -= 26
        reasons.append("starts with a reference that may require prior context")
    else:
        score += 10
        reasons.append("opens as a standalone thought")
    if contains_any(text, ["as i said", "like i said", "that guy", "this person", "they did", "he did", "she did"]):
        score -= 13
        reasons.append("contains an unclear reference")
    if contains_any(text, ["the reason", "the point", "what i mean", "here is", "this is why"]):
        score += 10
        reasons.append("states its own framing")
    if len(words) < 7:
        score -= 10
        reasons.append("may be too brief to establish context")
    return ScoreSignal("context", clamp_score(score), "; ".join(reasons) or "moderately self-contained")


def score_payoff(segment: TranscriptSegment) -> ScoreSignal:
    text = segment.text.strip()
    score = 42
    reasons = []
    if contains_any(text, ["because", "that's why", "that is why", "the truth is", "the answer is", "what changed", "the lesson"]):
        score += 22
        reasons.append("contains a clear answer or takeaway")
    if contains_any(text, ["but then", "until", "turns out", "instead", "so i", "and that"]):
        score += 13
        reasons.append("includes a narrative or logical turn")
    if text.endswith((".", "!")):
        score += 8
        reasons.append("ends with a complete statement")
    if text.endswith("?") and not contains_any(text, ["the answer", "because", "why"]):
        score -= 10
        reasons.append("may end on an unresolved question")
    if len(text_words(text)) < 8:
        score -= 8
        reasons.append("may not have room for a full payoff")
    return ScoreSignal("payoff", clamp_score(score), "; ".join(reasons) or "limited payoff signal")


def risk_flags_for_breakdown(breakdown: dict) -> list[str]:
    flags: list[str] = []
    if breakdown.get("context", {}).get("score", 100) < 45:
        flags.append("context_required")
    if breakdown.get("payoff", {}).get("score", 100) < 45:
        flags.append("weak_payoff")
    if breakdown.get("retention", {}).get("score", 100) < 45:
        flags.append("retention_risk")
    if breakdown.get("hook", {}).get("score", 0) >= 75 and breakdown.get("context", {}).get("score", 100) < 50:
        flags.append("strong_hook_needs_setup")
    return flags


def score_segment(segment: TranscriptSegment) -> ClipScoreBreakdown:
    hook = score_hook(segment)
    curiosity = score_curiosity(segment)
    emotion = score_emotion(segment)
    debate = score_debate(segment)
    story = score_story(segment)
    retention = score_retention(segment)
    context = score_context(segment)
    payoff = score_payoff(segment)
    weighted = round(
        hook.score * 0.18
        + curiosity.score * 0.11
        + emotion.score * 0.14
        + debate.score * 0.12
        + story.score * 0.10
        + retention.score * 0.15
        + context.score * 0.10
        + payoff.score * 0.10
    )
    overall = ScoreSignal(
        "overall",
        clamp_score(weighted),
        "Titan Brain v2 weighted hook, curiosity, emotion, debate, story, retention, context, and payoff quality.",
    )
    return ClipScoreBreakdown(hook, curiosity, emotion, debate, story, retention, context, payoff, overall)
