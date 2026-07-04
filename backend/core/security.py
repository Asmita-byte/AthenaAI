import mimetypes
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import bcrypt
import jwt
import magic

from backend.config import get_settings
from backend.core.exceptions import (
    FileTooLargeError,
    FileValidationError,
    UnsupportedFileTypeError,
)
from backend.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

ALLOWED_MIME_TYPES: dict[str, list[str]] = {
    ".pdf": ["application/pdf"],
    ".docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    ".pptx": ["application/vnd.openxmlformats-officedocument.presentationml.presentation"],
    ".xlsx": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
    ".csv": ["text/csv", "text/plain", "application/csv"],
    ".txt": ["text/plain"],
    ".png": ["image/png"],
    ".jpg": ["image/jpeg"],
    ".jpeg": ["image/jpeg"],
    ".webp": ["image/webp"],
}

DANGEROUS_PATTERNS: list[str] = [
    r"\.\.",
    r"[<>:\"|?*]",
    r"^\.",
    r"\x00",
]


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    name = name.strip()

    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, name):
            raise FileValidationError(
                filename=filename,
                reason=f"Filename contains invalid characters: pattern '{pattern}' matched.",
            )

    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^\w\-.]", "", name)

    if len(name) > 255:
        stem = Path(name).stem[:200]
        suffix = Path(name).suffix
        name = stem + suffix

    if not name or name in (".", ".."):
        raise FileValidationError(
            filename=filename,
            reason="Filename is empty or invalid after sanitization.",
        )

    return name


def validate_file_size(filename: str, size_bytes: int) -> None:
    if size_bytes > settings.max_upload_size_bytes:
        raise FileTooLargeError(
            filename=filename,
            size_bytes=size_bytes,
            max_bytes=settings.max_upload_size_bytes,
        )

    if size_bytes == 0:
        raise FileValidationError(
            filename=filename,
            reason="File is empty (0 bytes).",
        )


def validate_file_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower()

    if not extension:
        raise FileValidationError(
            filename=filename,
            reason="File has no extension.",
        )

    if extension not in settings.allowed_extensions:
        raise UnsupportedFileTypeError(filename=filename, extension=extension)

    return extension


def validate_mime_type(filename: str, file_bytes: bytes, extension: str) -> str:
    detected_mime = magic.from_buffer(file_bytes[:2048], mime=True)
    allowed_mimes = ALLOWED_MIME_TYPES.get(extension, [])

    if detected_mime not in allowed_mimes:
        raise FileValidationError(
            filename=filename,
            reason=(
                f"MIME type mismatch. Extension '{extension}' expects one of "
                f"{allowed_mimes}, but file content detected as '{detected_mime}'."
            ),
        )

    logger.debug(
        "MIME type validated",
        filename=filename,
        detected_mime=detected_mime,
        extension=extension,
    )

    return detected_mime


def validate_upload(filename: str, file_bytes: bytes) -> dict:
    logger.info("Validating upload", filename=filename, size_bytes=len(file_bytes))

    sanitized_name = sanitize_filename(filename)
    validate_file_size(sanitized_name, len(file_bytes))
    extension = validate_file_extension(sanitized_name)
    mime_type = validate_mime_type(sanitized_name, file_bytes, extension)

    logger.info(
        "Upload validation passed",
        original_filename=filename,
        sanitized_filename=sanitized_name,
        extension=extension,
        mime_type=mime_type,
        size_bytes=len(file_bytes),
    )

    return {
        "original_filename": filename,
        "sanitized_filename": sanitized_name,
        "extension": extension,
        "mime_type": mime_type,
        "size_bytes": len(file_bytes),
    }


# ---------- Password hashing ----------


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# ---------- JWT tokens ----------


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
