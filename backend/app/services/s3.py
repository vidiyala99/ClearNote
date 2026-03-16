import boto3
from botocore.exceptions import BotoCoreError, ClientError
from app.config import settings

_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
    return _s3_client


AUDIO_MAGIC_BYTES = {
    b"\x1a\x45\xdf\xa3": "webm",   # WebM/MKV
    b"\xff\xfb": "mp3",            # MP3
    b"\xff\xf3": "mp3",
    b"\xff\xf2": "mp3",
    b"ID3": "mp3",                 # MP3 ID3 tag
    b"RIFF": "wav",                # WAV (check offset 8 for "WAVE")
    b"\x00\x00\x00\x18ftyp": "m4a",  # M4A (check offset 4)
    b"\x00\x00\x00\x20ftyp": "mp4",
}


def generate_presigned_post(s3_key: str, expiry: int = 900) -> dict:
    client = get_s3_client()
    return client.generate_presigned_post(
        Bucket=settings.s3_bucket_name,
        Key=s3_key,
        Conditions=[
            ["starts-with", "$Content-Type", "audio/"],
            ["content-length-range", 1, 524_288_000],
        ],
        ExpiresIn=expiry,
    )


def get_magic_bytes(s3_key: str, timeout: float = 5.0) -> bytes:
    """Fetch first 12 bytes from S3 to check file type. Raises on timeout/error."""
    import botocore.config
    client = boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        config=botocore.config.Config(connect_timeout=timeout, read_timeout=timeout),
    )
    resp = client.get_object(
        Bucket=settings.s3_bucket_name,
        Key=s3_key,
        Range="bytes=0-11",
    )
    return resp["Body"].read()


def is_valid_audio(magic: bytes) -> bool:
    for prefix, _ in AUDIO_MAGIC_BYTES.items():
        if magic.startswith(prefix):
            return True
    # M4A: "ftyp" starts at offset 4
    if len(magic) >= 8 and magic[4:8] == b"ftyp":
        return True
    return False


def delete_object(s3_key: str) -> None:
    get_s3_client().delete_object(Bucket=settings.s3_bucket_name, Key=s3_key)
