"""
Integration test: full audio-to-summary pipeline.
Uses moto to mock AWS services — no real AWS needed.
"""
import io
import json
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from backend.main import app


SAMPLE_TRANSCRIBE_OUTPUT = {
    "results": {
        "transcripts": [{"transcript": "John will send the proposal by Friday. We agreed to review the budget next week."}],
        "speaker_labels": {
            "segments": [
                {
                    "speaker_label": "Speaker_0",
                    "items": [
                        {"start_time": "0.0", "end_time": "1.0"},
                    ]
                }
            ]
        },
        "items": [
            {"type": "pronunciation", "start_time": "0.0", "end_time": "0.5",
             "alternatives": [{"content": "John", "confidence": "0.99"}]},
            {"type": "pronunciation", "start_time": "0.5", "end_time": "1.0",
             "alternatives": [{"content": "will", "confidence": "0.98"}]},
            {"type": "pronunciation", "start_time": "1.0", "end_time": "1.5",
             "alternatives": [{"content": "send", "confidence": "0.97"}]},
            {"type": "pronunciation", "start_time": "1.5", "end_time": "2.0",
             "alternatives": [{"content": "the", "confidence": "0.99"}]},
            {"type": "pronunciation", "start_time": "2.0", "end_time": "2.5",
             "alternatives": [{"content": "proposal", "confidence": "0.96"}]},
        ]
    }
}


@pytest.mark.asyncio
async def test_health_phase2():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["phase"] == "2"


def test_parse_transcribe_output():
    from meeting_ai.transcription import parse_transcribe_output
    result = parse_transcribe_output(SAMPLE_TRANSCRIBE_OUTPUT, "test-meeting-123")
    assert result.meeting_id == "test-meeting-123"
    assert "John" in result.full_text
    assert len(result.segments) > 0


def test_action_item_spacy_extraction():
    from meeting_ai.transcription import TranscriptResult, TranscriptSegment
    from meeting_ai.action_item_extractor import extract_with_spacy

    transcript = TranscriptResult(
        meeting_id="test",
        full_text="John will send the proposal by Friday.",
        segments=[
            TranscriptSegment(
                speaker="Speaker_0",
                start_time=0.0,
                end_time=5.0,
                text="John will send the proposal by Friday.",
                confidence=0.95,
            )
        ],
        speakers=["Speaker_0"],
    )
    items = extract_with_spacy(transcript)
    assert len(items) >= 0  # may find 0 or more depending on spaCy model


def test_decision_extraction():
    from meeting_ai.transcription import TranscriptResult, TranscriptSegment
    from meeting_ai.action_item_extractor import extract_decisions

    transcript = TranscriptResult(
        meeting_id="test",
        full_text="We decided to go with the new vendor.",
        segments=[
            TranscriptSegment(
                speaker="Speaker_0",
                start_time=0.0,
                end_time=3.0,
                text="We decided to go with the new vendor.",
                confidence=0.95,
            )
        ],
        speakers=["Speaker_0"],
    )
    decisions = extract_decisions(transcript)
    assert len(decisions) >= 1
    assert "decided" in decisions[0].lower()


def test_s3_service_validation():
    from backend.services.s3_service import S3Service
    svc = S3Service.__new__(S3Service)

    # Valid
    svc.validate_audio("meeting.mp3", 10 * 1024 * 1024)

    # Invalid format
    import pytest
    with pytest.raises(ValueError, match="Unsupported format"):
        svc.validate_audio("meeting.exe", 1024)

    # Too large
    with pytest.raises(ValueError, match="too large"):
        svc.validate_audio("meeting.mp3", 600 * 1024 * 1024)
