"""
Transcription module — AWS Transcribe (primary) + Whisper (local fallback).
Parses Transcribe JSON output and maps speaker labels to structured segments.
"""
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from backend.core.config import get_settings

settings = get_settings()


@dataclass
class TranscriptSegment:
    speaker: str          # "Speaker_0", "Speaker_1", etc.
    start_time: float     # seconds
    end_time: float
    text: str
    confidence: float


@dataclass
class TranscriptResult:
    meeting_id: str
    full_text: str
    segments: list[TranscriptSegment] = field(default_factory=list)
    speakers: list[str] = field(default_factory=list)
    language: str = "en-US"
    duration_seconds: float = 0.0


# ── AWS Transcribe ─────────────────────────────────────────────────────────────

class AWSTranscribeService:
    def __init__(self):
        self.client = boto3.client("transcribe", region_name=settings.AWS_REGION)
        self.s3 = boto3.client("s3", region_name=settings.AWS_REGION)

    def submit_job(self, meeting_id: str, audio_s3_key: str) -> str:
        """Submit async transcription job. Returns job_name."""
        job_name = f"meeting-{meeting_id}-{int(time.time())}"
        media_uri = f"s3://{settings.S3_BUCKET}/{audio_s3_key}"

        self.client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": media_uri},
            MediaFormat=self._infer_format(audio_s3_key),
            LanguageCode="en-US",
            Settings={
                "ShowSpeakerLabels": True,
                "MaxSpeakerLabels": 10,
            },
            OutputBucketName=settings.S3_BUCKET,
            OutputKey=f"transcripts/{meeting_id}/transcript.json",
        )
        return job_name

    def poll_job(self, job_name: str, timeout_seconds: int = 600) -> dict:
        """Poll until job completes. Returns raw Transcribe JSON."""
        start = time.time()
        while time.time() - start < timeout_seconds:
            resp = self.client.get_transcription_job(TranscriptionJobName=job_name)
            status = resp["TranscriptionJob"]["TranscriptionJobStatus"]
            if status == "COMPLETED":
                return resp["TranscriptionJob"]
            elif status == "FAILED":
                reason = resp["TranscriptionJob"].get("FailureReason", "Unknown")
                raise RuntimeError(f"Transcription job failed: {reason}")
            time.sleep(10)
        raise TimeoutError(f"Transcription job {job_name} timed out after {timeout_seconds}s")

    def fetch_transcript_json(self, meeting_id: str) -> dict:
        """Fetch completed transcript JSON from S3."""
        key = f"transcripts/{meeting_id}/transcript.json"
        resp = self.s3.get_object(Bucket=settings.S3_BUCKET, Key=key)
        return json.loads(resp["Body"].read())

    @staticmethod
    def _infer_format(s3_key: str) -> str:
        ext = s3_key.rsplit(".", 1)[-1].lower()
        mapping = {"mp3": "mp3", "mp4": "mp4", "wav": "wav", "flac": "flac", "ogg": "ogg", "webm": "webm"}
        return mapping.get(ext, "mp3")


def parse_transcribe_output(raw: dict, meeting_id: str) -> TranscriptResult:
    """
    Parse AWS Transcribe JSON into structured TranscriptResult.
    Handles speaker diarization segments.
    """
    transcript_obj = raw.get("results", {})
    full_text = transcript_obj.get("transcripts", [{}])[0].get("transcript", "")

    segments: list[TranscriptSegment] = []
    speakers: set[str] = set()

    speaker_segments = transcript_obj.get("speaker_labels", {}).get("segments", [])
    items = transcript_obj.get("items", [])

    # Build word → speaker map from diarization
    word_speaker_map: dict[tuple, str] = {}
    for seg in speaker_segments:
        label = seg.get("speaker_label", "Speaker_0")
        for item in seg.get("items", []):
            start = item.get("start_time")
            end = item.get("end_time")
            if start and end:
                word_speaker_map[(float(start), float(end))] = label

    # Group consecutive items by speaker into segments
    current_speaker = None
    current_words: list[str] = []
    current_start = 0.0
    current_end = 0.0
    current_confidences: list[float] = []

    for item in items:
        if item.get("type") == "punctuation":
            if current_words:
                current_words[-1] += item["alternatives"][0]["content"]
            continue

        start = float(item.get("start_time", 0))
        end = float(item.get("end_time", 0))
        word = item["alternatives"][0]["content"]
        conf = float(item["alternatives"][0].get("confidence", 1.0))

        speaker = word_speaker_map.get((start, end), current_speaker or "Speaker_0")
        speakers.add(speaker)

        if speaker != current_speaker:
            if current_words and current_speaker:
                segments.append(TranscriptSegment(
                    speaker=current_speaker,
                    start_time=current_start,
                    end_time=current_end,
                    text=" ".join(current_words),
                    confidence=sum(current_confidences) / len(current_confidences) if current_confidences else 1.0,
                ))
            current_speaker = speaker
            current_words = [word]
            current_start = start
            current_end = end
            current_confidences = [conf]
        else:
            current_words.append(word)
            current_end = end
            current_confidences.append(conf)

    # Flush last segment
    if current_words and current_speaker:
        segments.append(TranscriptSegment(
            speaker=current_speaker,
            start_time=current_start,
            end_time=current_end,
            text=" ".join(current_words),
            confidence=sum(current_confidences) / len(current_confidences),
        ))

    duration = segments[-1].end_time if segments else 0.0

    return TranscriptResult(
        meeting_id=meeting_id,
        full_text=full_text,
        segments=segments,
        speakers=sorted(speakers),
        duration_seconds=duration,
    )


# ── Whisper local fallback (dev/offline) ───────────────────────────────────────

class WhisperService:
    """Local Whisper fallback for development without AWS."""

    def __init__(self, model_size: str = "base"):
        self._model = None
        self.model_size = model_size

    def _load(self):
        if self._model is None:
            import whisper  # lazy import — not installed in prod Lambda
            self._model = whisper.load_model(self.model_size)

    def transcribe_file(self, audio_path: str, meeting_id: str) -> TranscriptResult:
        self._load()
        result = self._model.transcribe(audio_path, word_timestamps=True)
        full_text = result["text"].strip()

        segments = []
        for seg in result.get("segments", []):
            segments.append(TranscriptSegment(
                speaker="Speaker_0",  # Whisper base has no diarization
                start_time=seg["start"],
                end_time=seg["end"],
                text=seg["text"].strip(),
                confidence=1.0 - seg.get("no_speech_prob", 0.0),
            ))

        return TranscriptResult(
            meeting_id=meeting_id,
            full_text=full_text,
            segments=segments,
            speakers=["Speaker_0"],
            duration_seconds=result["segments"][-1]["end"] if result["segments"] else 0.0,
        )
