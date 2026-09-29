"""Safe, user-actionable errors for CloudTalk tool calls."""

from mcp.server.mcpserver.exceptions import ToolError


class CloudTalkToolError(ToolError):
    """A failure with deliberately safe client-visible text."""


class MissingCredentialsError(CloudTalkToolError):
    def __init__(self) -> None:
        super().__init__(
            "CloudTalk credentials are missing. Set CLOUDTALK_KEY_ID and "
            "CLOUDTALK_KEY_SECRET, or run cloudtalk-mcp-setup."
        )


class AuthorizationError(CloudTalkToolError):
    def __init__(self) -> None:
        super().__init__(
            "CloudTalk authorization was rejected or expired. Reauthorize "
            "the account with cloudtalk-mcp-setup."
        )


class NotFoundError(CloudTalkToolError):
    def __init__(self) -> None:
        super().__init__("The requested CloudTalk record was not found.")


class RateLimitError(CloudTalkToolError):
    def __init__(self, retry_hint: str) -> None:
        super().__init__(f"CloudTalk rate limit reached. {retry_hint}")


class UpstreamHTTPError(CloudTalkToolError):
    def __init__(self, status_code: int, reason: str) -> None:
        super().__init__(f"CloudTalk API returned HTTP {status_code}: {reason}.")


class UpstreamResponseError(CloudTalkToolError):
    def __init__(self) -> None:
        super().__init__(
            "CloudTalk API returned an unreadable response. Check the result in CloudTalk before retrying."
        )


class TransportError(CloudTalkToolError):
    def __init__(self, *, write: bool) -> None:
        if write:
            message = (
                "CloudTalk request could not be confirmed. The operation outcome "
                "may be unknown; check its status before retrying."
            )
        else:
            message = "CloudTalk connection failed. Check connectivity and try again."
        super().__init__(message)
