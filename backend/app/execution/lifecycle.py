from enum import Enum

from app.core.errors import BadRequestError


class ExecutionStatus(str, Enum):
    """Lifecycle states for an Agent Execution."""

    PENDING = "pending"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InvalidStateTransitionError(BadRequestError):
    """Raised when an illegal lifecycle state transition is attempted."""

    def __init__(self, from_state: str, to_state: str):
        super().__init__(
            f"Invalid execution lifecycle transition: cannot transition from '{from_state}' to '{to_state}'."
        )
        self.from_state = from_state
        self.to_state = to_state


# Directed acyclic graph of valid state transitions
VALID_TRANSITIONS: dict[ExecutionStatus, set[ExecutionStatus]] = {
    ExecutionStatus.PENDING: {
        ExecutionStatus.RUNNING,
        ExecutionStatus.WAITING_FOR_APPROVAL,
        ExecutionStatus.CANCELLED,
        ExecutionStatus.FAILED,
    },
    ExecutionStatus.WAITING_FOR_APPROVAL: {
        ExecutionStatus.RUNNING,
        ExecutionStatus.CANCELLED,
        ExecutionStatus.FAILED,
    },
    ExecutionStatus.RUNNING: {
        ExecutionStatus.WAITING_FOR_APPROVAL,
        ExecutionStatus.COMPLETED,
        ExecutionStatus.FAILED,
        ExecutionStatus.CANCELLED,
    },
    # Terminal states cannot transition to anything
    ExecutionStatus.COMPLETED: set(),
    ExecutionStatus.FAILED: set(),
    ExecutionStatus.CANCELLED: set(),
}


def normalize_status(status: ExecutionStatus | str) -> ExecutionStatus:
    """Normalizes string or enum status to ExecutionStatus enum."""
    if isinstance(status, ExecutionStatus):
        return status
    try:
        return ExecutionStatus(status.strip().lower())
    except (ValueError, AttributeError):
        valid = [s.value for s in ExecutionStatus]
        raise BadRequestError(
            f"Invalid execution status: '{status}'. Valid options are: {valid}"
        )


def validate_transition(
    current_status: ExecutionStatus | str,
    target_status: ExecutionStatus | str,
) -> ExecutionStatus:
    """Validates that transition from current_status to target_status is permitted."""
    current = normalize_status(current_status)
    target = normalize_status(target_status)

    allowed = VALID_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidStateTransitionError(current.value, target.value)

    return target
