from typing import Any, Optional


class BaseAppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"error_code={self.error_code!r})"
        )


# =============================================================================
# FILE / UPLOAD EXCEPTIONS
# =============================================================================


class FileTooLargeError(BaseAppException):
    def __init__(self, filename: str, size_bytes: int, max_bytes: int):
        super().__init__(
            message=f"File '{filename}' is too large ({size_bytes} bytes). Maximum allowed: {max_bytes} bytes.",
            status_code=413,
            error_code="FILE_TOO_LARGE",
            details={"filename": filename, "size_bytes": size_bytes, "max_bytes": max_bytes},
        )


class UnsupportedFileTypeError(BaseAppException):
    def __init__(self, filename: str, extension: str):
        super().__init__(
            message=f"File type '{extension}' is not supported for file '{filename}'.",
            status_code=415,
            error_code="UNSUPPORTED_FILE_TYPE",
            details={"filename": filename, "extension": extension},
        )


class FileValidationError(BaseAppException):
    def __init__(self, filename: str, reason: str):
        super().__init__(
            message=f"File validation failed for '{filename}': {reason}",
            status_code=400,
            error_code="FILE_VALIDATION_ERROR",
            details={"filename": filename, "reason": reason},
        )


class FileNotFoundError(BaseAppException):
    def __init__(self, file_id: str):
        super().__init__(
            message=f"File with id '{file_id}' was not found.",
            status_code=404,
            error_code="FILE_NOT_FOUND",
            details={"file_id": file_id},
        )


# =============================================================================
# DOCUMENT PROCESSING EXCEPTIONS
# =============================================================================


class DocumentParsingError(BaseAppException):
    def __init__(self, filename: str, reason: str):
        super().__init__(
            message=f"Failed to parse document '{filename}': {reason}",
            status_code=422,
            error_code="DOCUMENT_PARSING_ERROR",
            details={"filename": filename, "reason": reason},
        )


class DocumentNotFoundError(BaseAppException):
    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document with id '{document_id}' was not found.",
            status_code=404,
            error_code="DOCUMENT_NOT_FOUND",
            details={"document_id": document_id},
        )


class DocumentProcessingError(BaseAppException):
    def __init__(self, document_id: str, stage: str, reason: str):
        super().__init__(
            message=f"Processing failed for document '{document_id}' at stage '{stage}': {reason}",
            status_code=500,
            error_code="DOCUMENT_PROCESSING_ERROR",
            details={"document_id": document_id, "stage": stage, "reason": reason},
        )


# =============================================================================
# EMBEDDING EXCEPTIONS
# =============================================================================


class EmbeddingError(BaseAppException):
    def __init__(self, reason: str):
        super().__init__(
            message=f"Embedding generation failed: {reason}",
            status_code=500,
            error_code="EMBEDDING_ERROR",
            details={"reason": reason},
        )


# =============================================================================
# RETRIEVAL EXCEPTIONS
# =============================================================================


class RetrievalError(BaseAppException):
    def __init__(self, reason: str):
        super().__init__(
            message=f"Retrieval failed: {reason}",
            status_code=500,
            error_code="RETRIEVAL_ERROR",
            details={"reason": reason},
        )


class VectorStoreError(BaseAppException):
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Vector store operation '{operation}' failed: {reason}",
            status_code=500,
            error_code="VECTOR_STORE_ERROR",
            details={"operation": operation, "reason": reason},
        )


# =============================================================================
# QUERY / GENERATION EXCEPTIONS
# =============================================================================


class QueryValidationError(BaseAppException):
    def __init__(self, reason: str):
        super().__init__(
            message=f"Invalid query: {reason}",
            status_code=400,
            error_code="QUERY_VALIDATION_ERROR",
            details={"reason": reason},
        )


class LLMError(BaseAppException):
    def __init__(self, provider: str, reason: str):
        super().__init__(
            message=f"LLM call failed for provider '{provider}': {reason}",
            status_code=502,
            error_code="LLM_ERROR",
            details={"provider": provider, "reason": reason},
        )


class LLMRateLimitError(BaseAppException):
    def __init__(self, provider: str):
        super().__init__(
            message=f"Rate limit exceeded for LLM provider '{provider}'. Please retry after some time.",
            status_code=429,
            error_code="LLM_RATE_LIMIT",
            details={"provider": provider},
        )


# =============================================================================
# JOB / WORKER EXCEPTIONS
# =============================================================================


class JobNotFoundError(BaseAppException):
    def __init__(self, job_id: str):
        super().__init__(
            message=f"Job with id '{job_id}' was not found.",
            status_code=404,
            error_code="JOB_NOT_FOUND",
            details={"job_id": job_id},
        )


class JobFailedError(BaseAppException):
    def __init__(self, job_id: str, reason: str):
        super().__init__(
            message=f"Job '{job_id}' failed: {reason}",
            status_code=500,
            error_code="JOB_FAILED",
            details={"job_id": job_id, "reason": reason},
        )


# =============================================================================
# CONFIGURATION EXCEPTIONS
# =============================================================================


class ConfigurationError(BaseAppException):
    def __init__(self, reason: str):
        super().__init__(
            message=f"Configuration error: {reason}",
            status_code=500,
            error_code="CONFIGURATION_ERROR",
            details={"reason": reason},
        )
