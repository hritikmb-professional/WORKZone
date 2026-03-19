"""
S3 service — upload, presigned URLs, lifecycle management.
Audio deleted after transcript generated (GDPR data minimisation).
"""
import io
import uuid
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from backend.core.config import get_settings

settings = get_settings()

ALLOWED_FORMATS = {"mp3", "mp4", "wav", "flac", "ogg", "webm", "m4a"}
MAX_FILE_SIZE_MB = 500
CHUNK_SIZE_MB = 25  # pydub chunks files > 25MB


class S3Service:
    def __init__(self):
        self.s3 = boto3.client("s3", region_name=settings.AWS_REGION)
        self.bucket = settings.S3_BUCKET

    def validate_audio(self, filename: str, size_bytes: int) -> None:
        ext = Path(filename).suffix.lstrip(".").lower()
        if ext not in ALLOWED_FORMATS:
            raise ValueError(f"Unsupported format: {ext}. Allowed: {ALLOWED_FORMATS}")
        if size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"File too large: {size_bytes / 1024 / 1024:.1f}MB. Max: {MAX_FILE_SIZE_MB}MB")

    async def upload_audio(self, file: UploadFile, meeting_id: str) -> str:
        """Upload audio file to S3. Returns S3 key."""
        ext = Path(file.filename).suffix.lstrip(".").lower()
        s3_key = f"meetings/{meeting_id}/audio.{ext}"

        content = await file.read()
        self.validate_audio(file.filename, len(content))

        self.s3.put_object(
            Bucket=self.bucket,
            Key=s3_key,
            Body=content,
            ContentType=f"audio/{ext}",
            ServerSideEncryption="aws:kms",  # SSE-KMS mandatory
        )
        return s3_key

    def get_transcript_json(self, meeting_id: str) -> dict:
        """Fetch transcript JSON from S3."""
        import json
        key = f"transcripts/{meeting_id}/transcript.json"
        resp = self.s3.get_object(Bucket=self.bucket, Key=key)
        return json.loads(resp["Body"].read())

    def presigned_url(self, s3_key: str, expires: int = 3600) -> str:
        return self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": s3_key},
            ExpiresIn=expires,
        )

    def delete_audio(self, meeting_id: str, ext: str = "mp3") -> None:
        """Delete audio after transcription — GDPR minimisation."""
        key = f"meetings/{meeting_id}/audio.{ext}"
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=key)
        except ClientError:
            pass  # already deleted or never existed


s3_service = S3Service()
