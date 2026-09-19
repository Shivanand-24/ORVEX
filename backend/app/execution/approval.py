from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, NotFoundError
from app.models.agent import Agent
from app.repositories.membership_repository import membership_repository


class ApprovalManager:
    """Manages human-in-the-loop approval evaluation and permission boundaries."""

    def should_require_approval(self, agent: Agent) -> bool:
        """Determines if the agent execution must be paused for approval.

        Uses the existing Agent.require_approval model field directly.
        """
        return bool(agent.require_approval)

    async def validate_approver(
        self,
        db: AsyncSession,
        organization_id: UUID,
        approver_user_id: UUID,
    ) -> None:
        """Verifies that the user granting approval belongs to the organization."""
        membership = await membership_repository.find_by_organization_and_user(
            db, organization_id=organization_id, user_id=approver_user_id
        )
        if not membership:
            raise BadRequestError(
                f"User '{approver_user_id}' is not a member of organization '{organization_id}' "
                "and cannot approve this execution."
            )


approval_manager = ApprovalManager()
