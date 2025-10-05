from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeInvocationContext:
    actor_id: str
    session_id: str


_DEFAULT_CONTEXT = RuntimeInvocationContext(
    actor_id="default_user", session_id="sake_session_default_user"
)

_current_context: ContextVar[RuntimeInvocationContext | None] = ContextVar(
    "bedrock_agentcore_runtime_context",
    default=None,
)


def set_runtime_context(actor_id: str, session_id: str) -> None:
    """Store the invocation-scoped identifiers for downstream tool access."""
    _current_context.set(RuntimeInvocationContext(actor_id=actor_id, session_id=session_id))


def get_runtime_context() -> RuntimeInvocationContext:
    """Return the currently active invocation context."""
    return _current_context.get() or _DEFAULT_CONTEXT


def clear_runtime_context() -> None:
    """Reset the context after a request completes."""
    _current_context.set(None)
