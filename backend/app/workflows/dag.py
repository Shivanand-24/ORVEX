import re
from typing import Any, Dict, List, Set
from uuid import UUID

from app.core.errors import BadRequestError

MAX_WORKFLOW_STEPS = 50
MAX_EXECUTION_STEPS = 100
STEP_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")


class GraphValidationError(BadRequestError):
    """Base error for workflow graph validation failures."""
    pass


DAGValidationError = GraphValidationError


class AmbiguousEntryStepError(GraphValidationError):
    """Raised when graph lacks a single deterministic Trigger root step."""
    pass


class CycleDetectedError(GraphValidationError):
    """Raised when graph contains cycles or back-edges violating DAG properties."""
    pass


class UnreachableStepError(GraphValidationError):
    """Raised when graph contains disconnected or unreachable orphan steps."""
    pass


class WorkflowGraphValidator:
    """Validates Directed Acyclic Graph (DAG) structures for ORVEX workflows."""

    @classmethod
    def validate_graph(cls, steps: List[Any]) -> None:
        """Thoroughly validates workflow steps as a valid, deterministic Directed Acyclic Graph.

        Steps can be Pydantic schemas, SQLAlchemy models, or dictionaries.
        """
        if not steps:
            raise GraphValidationError("Workflow must contain at least one step.")

        if len(steps) > MAX_WORKFLOW_STEPS:
            raise GraphValidationError(
                f"Workflow exceeds maximum allowed steps limit ({MAX_WORKFLOW_STEPS}). Found {len(steps)} steps."
            )

        # Normalize step identifiers and edge adjacency
        step_ids: Set[str] = set()
        step_types: Dict[str, str] = {}
        adjacency: Dict[str, List[str]] = {}
        in_degrees: Dict[str, int] = {}

        # 1. Collect nodes and check uniqueness & identifier validity
        for step in steps:
            raw_id = cls._get_field(step, "id") or cls._get_field(step, "step_id")
            if raw_id is None:
                raise GraphValidationError("Step is missing an identifier ('id' or 'step_id').")
            s_id = str(raw_id).strip()
            if not s_id or not STEP_ID_PATTERN.match(s_id):
                raise GraphValidationError(
                    f"Invalid step ID '{s_id}'. Step IDs must be non-empty and alphanumeric with hyphens/underscores."
                )

            raw_type = cls._get_field(step, "type") or cls._get_field(step, "step_type")
            if not raw_type:
                raise GraphValidationError(f"Step '{s_id}' is missing a step type.")
            s_type = str(raw_type).strip()

            if s_id in step_ids:
                raise GraphValidationError(f"Duplicate step ID '{s_id}' detected in workflow definition.")
            step_ids.add(s_id)
            step_types[s_id] = s_type
            adjacency[s_id] = []
            in_degrees[s_id] = 0

        # 2. Build edges and check self-references, missing references, and duplicate edges
        for step in steps:
            raw_id = cls._get_field(step, "id") or cls._get_field(step, "step_id")
            u = str(raw_id).strip()
            raw_next = cls._get_field(step, "next_step_ids") or []
            seen_edges_from_u: Set[str] = set()

            for target in raw_next:
                v = str(target).strip()
                # Check missing references
                if v not in step_ids:
                    raise GraphValidationError(
                        f"Step '{u}' references non-existent next_step_id '{v}'."
                    )
                # Check self-references
                if v == u:
                    raise GraphValidationError(
                        f"Self-referencing cycle detected on step '{u}'. A step cannot point to itself."
                    )
                # Check duplicate edges
                if v in seen_edges_from_u:
                    raise GraphValidationError(
                        f"Duplicate edge detected from step '{u}' to step '{v}'."
                    )
                seen_edges_from_u.add(v)
                adjacency[u].append(v)
                in_degrees[v] += 1

        # 3. Deterministic Entry / Start Step Check
        # Exactly one node must have in-degree == 0, and it must have type == 'Trigger' (case-insensitive)
        root_candidates = [s_id for s_id, deg in in_degrees.items() if deg == 0]

        if not root_candidates:
            raise AmbiguousEntryStepError(
                "Workflow graph has no entry step (all steps have incoming edges, creating an unavoidable cycle)."
            )

        if len(root_candidates) > 1:
            raise AmbiguousEntryStepError(
                f"Workflow graph must have exactly one root entry step with in-degree 0. "
                f"Found {len(root_candidates)} root candidates: {root_candidates}."
            )

        root_id = root_candidates[0]
        if step_types[root_id].lower() != "trigger":
            raise AmbiguousEntryStepError(
                f"Root entry step '{root_id}' must have type 'Trigger', but found '{step_types[root_id]}'."
            )

        # 4. Cycle Detection using DFS 3-Color Marking
        # 0 = WHITE (unvisited), 1 = GRAY (visiting), 2 = BLACK (visited)
        colors: Dict[str, int] = {s_id: 0 for s_id in step_ids}

        def dfs(node: str) -> None:
            colors[node] = 1  # GRAY
            for neighbor in adjacency[node]:
                if colors[neighbor] == 1:
                    raise CycleDetectedError(
                        f"Cycle detected in workflow graph involving step '{neighbor}'. "
                        f"Workflows must be strict Directed Acyclic Graphs (DAGs)."
                    )
                if colors[neighbor] == 0:
                    dfs(neighbor)
            colors[node] = 2  # BLACK

        # Run DFS across all components to ensure no cycles exist even in disconnected subgraphs
        for s_id in step_ids:
            if colors[s_id] == 0:
                dfs(s_id)

        # 5. Reachability & Orphan Step Detection
        # Traverse from root via BFS to ensure every single step is reachable
        visited: Set[str] = set()
        queue: List[str] = [root_id]
        visited.add(root_id)

        while queue:
            curr = queue.pop(0)
            for nxt in adjacency[curr]:
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)

        if len(visited) < len(step_ids):
            unreachable = sorted(list(step_ids - visited))
            raise UnreachableStepError(
                f"Unreachable or orphan steps detected in workflow: {unreachable}. "
                f"All steps must be reachable from the root Trigger step '{root_id}'."
            )

    @staticmethod
    def _get_field(step: Any, field_name: str) -> Any:
        if isinstance(step, dict):
            return step.get(field_name)
        return getattr(step, field_name, None)

    validate = validate_graph


graph_validator = WorkflowGraphValidator()
