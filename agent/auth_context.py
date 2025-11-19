import contextvars

# This variable is "async-safe". It tracks data separately for every concurrent request.
user_auth_token: contextvars.ContextVar[str | None] = contextvars.ContextVar("user_auth_token", default=None)
