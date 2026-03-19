"""
BART-large-CNN abstractive summarization.
Model is loaded once at EC2 startup and kept in memory — not reloaded per request.
"""
import re
from dataclasses import dataclass
from typing import Optional

from meeting_ai.transcription import TranscriptResult

# Lazy-loaded — only imported when first used
_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        from transformers import pipeline
        _pipeline = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=-1,  # CPU; change to 0 for GPU on EC2
        )
    return _pipeline


@dataclass
class SummaryResult:
    summary: str
    word_count: int
    compression_ratio: float  # original_words / summary_words


# ── Text cleaning ──────────────────────────────────────────────────────────────

def clean_transcript(transcript: TranscriptResult) -> str:
    """
    Stage 1: Clean raw transcript for NLP.
    - Normalize speaker labels
    - Remove filler words
    - Collapse whitespace
    """
    FILLERS = {"um", "uh", "like", "you know", "i mean", "sort of", "kind of", "basically"}
    filler_pattern = re.compile(
        r"\b(" + "|".join(re.escape(f) for f in FILLERS) + r")\b", re.IGNORECASE
    )

    lines = []
    for seg in transcript.segments:
        text = seg.text.strip()
        text = filler_pattern.sub("", text)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            lines.append(f"{seg.speaker}: {text}")

    return "\n".join(lines)


def _chunk_text(text: str, max_tokens: int = 1024) -> list[str]:
    """
    BART max input is 1024 tokens (~750 words).
    Split long transcripts into overlapping chunks.
    """
    words = text.split()
    chunk_size = 700
    overlap = 50
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


# ── Summarization ──────────────────────────────────────────────────────────────

def summarize(transcript: TranscriptResult) -> SummaryResult:
    """
    Stage 2: BART abstractive summarization.
    Handles long transcripts via chunking + merge.
    """
    cleaned = clean_transcript(transcript)
    original_word_count = len(cleaned.split())

    pipe = _get_pipeline()
    chunks = _chunk_text(cleaned)

    chunk_summaries = []
    for chunk in chunks:
        result = pipe(
            chunk,
            max_length=180,
            min_length=40,
            do_sample=False,
            truncation=True,
        )
        chunk_summaries.append(result[0]["summary_text"])

    # If multiple chunks, summarize the summaries
    if len(chunk_summaries) > 1:
        merged = " ".join(chunk_summaries)
        final = pipe(merged, max_length=250, min_length=80, do_sample=False, truncation=True)
        summary_text = final[0]["summary_text"]
    else:
        summary_text = chunk_summaries[0]

    summary_word_count = len(summary_text.split())
    compression = original_word_count / max(summary_word_count, 1)

    return SummaryResult(
        summary=summary_text,
        word_count=summary_word_count,
        compression_ratio=round(compression, 2),
    )
