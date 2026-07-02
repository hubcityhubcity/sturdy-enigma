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
    overall: ScoreSignal

    def as_dict(self) -> dict:
        return {
            "hook": self.hook.__dict__,
            "curiosity": self.curiosity.__dict__,
            "emotion": self.emotion.__dict__,
            "debate": self.debate.__dict__,
            "story": self.story.__dict__,
            "retention": self.retention.__dict__,
            "overall": self.overall.__dict__,
        }


def clamp_score(value: int) -> int:
    return max(0, min(100, value))


def text_words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9']+", text.lower())


def contains_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def score_hook(segment: TranscriptSegment) -> ScoreSignal:
    text = segment.text.strip()
    words = text_words(text)
    score = 45
    reasons = []

    if text.endswith("?") or contains_any(text, ["let me ask", "what if", "why", "how come"]):
        score += 18
        reasons.append("opens with a question or challenge")
    if contains_any(text, ["nobody", "everybody", "never", "always", "truth", "mistake", "secret"]):
        score += 14
        reasons.append("uses high-curiosity language")
    if contains_any(text, ["listen", "look", "here's", "here is", "the thing is"]):
        score += 8
        reasons.append("has a direct attention cue")
    if 8 <= len(words) <= 35:
        score += 8
        reasons.append("short enough for a strong opening")
    if len(words) > 70:
        score -= 10
        reasons.append("opening may be too wordy")

    return ScoreSignal("hook", clamp_score(score), "; ".join(reasons) or "baseline hook strength")


def score_curiosity(segment: TranscriptSegment) -> ScoreSignal:
    text = segment.text
    score = 40
    reasons = []
    phrases = ["what happened", "nobody tells", "the reason", "the problem", "the truth", "secret", "mistake", "before you"]
    if contains_any(text, phrases):
        score += 25
        reasons.append("creates an information gap")
    if "?" in text:
        score += 12
        reasons.append("question creates open loop")
    if contains_any(text, ["but", "however", "until", "unless"]):
        score += 8
        reasons.append("contrast language suggests payoff")
    return ScoreSignal("curiosity", clamp_score(score), "; ".join(reasons) or "limited curiosity trigger detected")


def score_emotion(segment: TranscriptSegment) -> ScoreSignal:
    text = segment.text
    score = 35
    reasons = []
    emotional_terms = [
        "love", "hate", "angry", "hurt", "pain", "fear", "proud", "cry", "laugh", "crazy", "wild",
        "powerful", "real", "honest", "respect", "disrespect", "broke", "rich", "survive", "win",
    ]
    hits = sum(1 for term in emotional_terms if term in text.lower())
    score += min(35, hits * 8)
    if hits:
        reasons.append(f"contains {hits} emotional trigger(s)")
    if "!" in text:
        score += 8
        reasons.append("punctuation suggests intensity")
    return ScoreSignal("emotion", clamp_score(score), "; ".join(reasons) or "mostly neutral emotional language")


def score_debate(segment: TranscriptSegment) -> ScoreSignal:
    text = segment.text
    score = 30
    reasons = []
    debate_terms = ["wrong", "disagree", "argue", "debate", "but", "no", "not true", "challenge", "prove", "question"]
    hits = sum(1 for term in debate_terms if term in text.lower())
    score += min(40, hits * 9)
    if hits:
        reasons.append(f"contains {hits} conflict/debate signal(s)")
    if contains_any(text, ["let me ask", "answer this"]):
        score += 14
        reasons.append("direct challenge format")
    return ScoreSignal("debate", clamp_score(score), "; ".join(reasons) or "low debate tension")


def score_story(segment: TranscriptSegment) -> ScoreSignal:
    text = segment.text
    score = 35
    reasons = []
    story_terms = ["when i", "one day", "then", "after", "before", "because", "remember", "started", "ended"]
    hits = sum(1 for term in story_terms if term in text.lower())
    score += min(35, hits * 8)
    if hits:
        reasons.append(f"contains {hits} story structure signal(s)")
    duration = segment.end_seconds - segment.start_seconds
    if 20 <= duration <= 60:
        score += 10
        reasons.append("duration fits short story arc")
    return ScoreSignal("story", clamp_score(score), "; ".join(reasons) or "limited story structure")


def score_retention(segment: TranscriptSegment) -> ScoreSignal:
    text = segment.text
    words = text_words(text)
    duration = max(1.0, segment.end_seconds - segment.start_seconds)
    words_per_second = len(words) / duration
    score = 50
    reasons = []

    if 1.8 <= words_per_second <= 3.4:
        score += 18
        reasons.append("speaking pace is short-form friendly")
    elif words_per_second < 1.2:
        score -= 12
        reasons.append("pace may feel slow")
    elif words_per_second > 4.0:
        score -= 8
        reasons.append("pace may feel rushed")

    if 18 <= duration <= 55:
        score += 14
        reasons.append("duration fits Shorts/TikTok retention window")
    elif duration > 75:
        score -= 12
        reasons.append("clip may run long")

    filler_count = sum(words.count(word) for word in ["um", "uh", "like", "you", "know"])
    if filler_count > 6:
        score -= 8
        reasons.append("filler words may reduce retention")

    return ScoreSignal("retention", clamp_score(score), "; ".join(reasons) or "baseline retention profile")


def score_segment(segment: TranscriptSegment) -> ClipScoreBreakdown:
    hook = score_hook(segment)
    curiosity = score_curiosity(segment)
    emotion = score_emotion(segment)
    debate = score_debate(segment)
    story = score_story(segment)
    retention = score_retention(segment)

    weighted = round(
        hook.score * 0.25
        + curiosity.score * 0.18
        + emotion.score * 0.15
        + debate.score * 0.14
        + story.score * 0.10
        + retention.score * 0.18
    )
    overall = ScoreSignal(
        "overall",
        clamp_score(weighted),
        "weighted blend of hook, curiosity, emotion, debate, story, and retention signals",
    )
    return ClipScoreBreakdown(hook, curiosity, emotion, debate, story, retention, overall)
