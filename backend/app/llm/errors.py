from app.core.errors import AppException


class LLMError(AppException):
    """Base exception for all LLM Gateway errors."""

    def __init__(
        self,
        detail: str = "AI service encountered an unexpected error.",
        status_code: int = 500,
        internal_error: str | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.internal_error = internal_error

    def __str__(self) -> str:
        if self.internal_error:
            return f"{self.detail} (Internal: {self.internal_error})"
        return self.detail


class ConfigurationError(LLMError):
    """Raised when LLM provider configuration or credentials are missing or invalid."""

    def __init__(
        self,
        detail: str = "AI service configuration is invalid or missing credentials.",
        internal_error: str | None = None,
    ) -> None:
        super().__init__(detail=detail, status_code=500, internal_error=internal_error)


class ProviderUnavailableError(LLMError):
    """Raised when the AI provider network endpoint is unreachable or down."""

    def __init__(
        self,
        detail: str = "AI service is temporarily unavailable. Please try again later.",
        internal_error: str | None = None,
    ) -> None:
        super().__init__(detail=detail, status_code=503, internal_error=internal_error)


class RateLimitError(LLMError):
    """Raised when the AI provider rejects requests due to rate limits or quota exhaustion."""

    def __init__(
        self,
        detail: str = "AI service rate limit exceeded. Please retry shortly.",
        internal_error: str | None = None,
    ) -> None:
        super().__init__(detail=detail, status_code=429, internal_error=internal_error)


class ProviderRequestError(LLMError):
    """Raised when the AI provider rejects the request payload (e.g. invalid arguments, context length)."""

    def __init__(
        self,
        detail: str = "AI request could not be processed by the provider.",
        internal_error: str | None = None,
    ) -> None:
        super().__init__(detail=detail, status_code=400, internal_error=internal_error)


class ProviderTimeoutError(LLMError):
    """Raised when the connection or response from the AI provider times out."""

    def __init__(
        self,
        detail: str = "AI service request timed out. Please try again.",
        internal_error: str | None = None,
    ) -> None:
        super().__init__(detail=detail, status_code=504, internal_error=internal_error)
