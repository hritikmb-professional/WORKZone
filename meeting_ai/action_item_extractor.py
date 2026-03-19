"""
Hybrid action item extractor.
Method 1: spaCy rule-based (dependency parsing + imperative verb detection)
Method 2: Groq LLaMA-3.1-8b-instant few-shot prompt (free tier, ~500ms)
Both methods vote — high agreement = high confidence score.
Items below 0.7 confidence are flagged for human review.
"""
import json
import re
from dataclasses import dataclass, field
from typing import Optional

from backend.core.config import get_settings
from meeting_ai.transcription import TranscriptResult

settings = get_settings()

_nlp = None
CONFIDENCE_THRESHOLD = 0.7


def _get_nlp():
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("en_core_web_lg")
    return _nlp


@dataclass
class ActionItem:
    task_text: str
    assignee_raw: Optional[str]
    due_date_raw: Optional[str]
    confidence: float
    source: str                 # "spacy", "groq", or "both"
    needs_review: bool = False

    def __post_init__(self):
        self.needs_review = self.confidence < CONFIDENCE_THRESHOLD


# ── spaCy rule-based extractor ─────────────────────────────────────────────────

IMPERATIVE_PATTERNS = [
    r"\b(please\s+)?(?:send|update|schedule|review|create|prepare|follow up|reach out|check|confirm|complete|finish|write|draft|share|present|discuss|set up|book|arrange|coordinate|ensure|make sure)\b",
]
ASSIGNEE_PATTERNS = [
    r"\b([A-Z][a-z]+)\s+(?:will|should|needs to|has to|must)\b",
    r"\b(?:action for|assigned to|owner:?)\s+([A-Z][a-z]+)\b",
]
DUE_DATE_PATTERNS = [
    r"by\s+((?:next\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|week|month|eod|end of day|end of week))",
    r"(?:due|deadline)\s+(?:is\s+)?([^,.]+)",
    r"(tomorrow|today|this week|next week)",
]

imperative_re = re.compile("|".join(IMPERATIVE_PATTERNS), re.IGNORECASE)
assignee_re = [re.compile(p, re.IGNORECASE) for p in ASSIGNEE_PATTERNS]
due_date_re = [re.compile(p, re.IGNORECASE) for p in DUE_DATE_PATTERNS]


def _extract_assignee(text: str) -> Optional[str]:
    for pattern in assignee_re:
        m = pattern.search(text)
        if m:
            return m.group(1)
    return None


def _extract_due_date(text: str) -> Optional[str]:
    for pattern in due_date_re:
        m = pattern.search(text)
        if m:
            return m.group(1)
    return None


def extract_with_spacy(transcript: TranscriptResult) -> list[ActionItem]:
    nlp = _get_nlp()
    items: list[ActionItem] = []

    for seg in transcript.segments:
        doc = nlp(seg.text)
        for sent in doc.sents:
            text = sent.text.strip()
            if len(text) < 10:
                continue
            if not imperative_re.search(text):
                continue
            has_action_root = any(
                token.dep_ == "ROOT" and token.pos_ == "VERB"
                for token in sent
            )
            if not has_action_root:
                continue

            assignee = _extract_assignee(text) or seg.speaker
            due_date = _extract_due_date(text)

            confidence = 0.65
            if assignee and assignee != seg.speaker:
                confidence += 0.1
            if due_date:
                confidence += 0.1
            confidence = min(confidence, 0.88)

            items.append(ActionItem(
                task_text=text,
                assignee_raw=assignee,
                due_date_raw=due_date,
                confidence=round(confidence, 2),
                source="spacy",
            ))

    return items


# ── Groq LLaMA extractor ───────────────────────────────────────────────────────

GROQ_SYSTEM = """You are an expert meeting analyst. Extract action items from meeting transcripts.
Return ONLY valid JSON array — no preamble, no markdown, no explanation.
Format: [{"task": "...", "assignee": "...", "due_date": "..."}]
assignee and due_date must be null if not explicitly mentioned.
Only include genuine action items — not discussion points or questions."""

GROQ_FEW_SHOT = """Example input: "John will send the proposal by Friday. We should review the budget next week."
Example output: [{"task": "Send the proposal", "assignee": "John", "due_date": "Friday"}, {"task": "Review the budget", "assignee": null, "due_date": "next week"}]"""


def extract_with_groq(transcript: TranscriptResult) -> list[ActionItem]:
    if not settings.GROQ_API_KEY:
        return []

    from groq import Groq
    client = Groq(api_key=settings.GROQ_API_KEY)

    text = transcript.full_text[:6000]

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": GROQ_SYSTEM},
                {"role": "user", "content": GROQ_FEW_SHOT},
                {"role": "user", "content": f"Transcript:\n{text}"},
            ],
            temperature=0,
            max_tokens=1000,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if model adds them
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

        parsed = json.loads(raw)
    except Exception as e:
        print(f"Groq extraction failed: {e}")
        return []

    items = []
    for item in parsed:
        if not item.get("task"):
            continue
        items.append(ActionItem(
            task_text=item["task"],
            assignee_raw=item.get("assignee"),
            due_date_raw=item.get("due_date"),
            confidence=0.82,
            source="groq",
        ))
    return items


# ── Voting / merge ─────────────────────────────────────────────────────────────

def _texts_similar(a: str, b: str, threshold: float = 0.6) -> bool:
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    if not wa or not wb:
        return False
    return len(wa & wb) / len(wa | wb) >= threshold


def merge_and_vote(spacy_items: list[ActionItem], groq_items: list[ActionItem]) -> list[ActionItem]:
    merged: list[ActionItem] = []
    used_groq: set[int] = set()

    for sp_item in spacy_items:
        matched = False
        for i, groq_item in enumerate(groq_items):
            if i in used_groq:
                continue
            if _texts_similar(sp_item.task_text, groq_item.task_text):
                boosted = min((sp_item.confidence + groq_item.confidence) / 2 + 0.1, 0.99)
                merged.append(ActionItem(
                    task_text=groq_item.task_text,
                    assignee_raw=groq_item.assignee_raw or sp_item.assignee_raw,
                    due_date_raw=groq_item.due_date_raw or sp_item.due_date_raw,
                    confidence=round(boosted, 2),
                    source="both",
                ))
                used_groq.add(i)
                matched = True
                break
        if not matched:
            merged.append(sp_item)

    for i, groq_item in enumerate(groq_items):
        if i not in used_groq:
            merged.append(groq_item)

    return sorted(merged, key=lambda x: x.confidence, reverse=True)


# ── Public API ─────────────────────────────────────────────────────────────────

def extract_action_items(transcript: TranscriptResult) -> list[ActionItem]:
    spacy_items = extract_with_spacy(transcript)
    groq_items = extract_with_groq(transcript)
    return merge_and_vote(spacy_items, groq_items)


def extract_decisions(transcript: TranscriptResult) -> list[str]:
    nlp = _get_nlp()
    decisions = []
    decision_patterns = re.compile(
        r"\b(we decided|we agreed|it was decided|we will|going forward|the decision is|we\'re going with|we chose)\b",
        re.IGNORECASE
    )
    for seg in transcript.segments:
        doc = nlp(seg.text)
        for sent in doc.sents:
            if decision_patterns.search(sent.text):
                decisions.append(sent.text.strip())
    return decisions
