"""Jira ticket models.

Note: Fields like status, priority, and type are flexible strings. Jira
implementations can have custom values for these fields depending on project
configuration and workflow settings.
"""

from typing import Any

from pydantic import BaseModel, Field

# Type alias for ADF (Atlassian Document Format) documents.
AdfDocument = dict[str, Any]

# Common status mappings for convenience. These are typical Jira statuses,
# but your Jira instance may have different or additional statuses.
COMMON_STATUS_MAP: dict[str, str] = {
    "open": "Open",
    "in progress": "In Progress",
    "in review": "In Review",
    "done": "Done",
    "closed": "Closed",
    "canceled": "Canceled",
    "todo": "To Do",
    "to do": "To Do",
    "backlog": "Backlog",
    "blocked": "Blocked",
    "ready for review": "Ready for Review",
    "ready for qa": "Ready for QA",
    "in qa": "In QA",
    "deployed": "Deployed",
}


def normalize_status(status: str) -> str:
    """Normalize a status string to its Jira display name.

    If the status matches a common status (case-insensitive), returns the
    properly capitalized version. Otherwise, returns the status as-is.

    Args:
        status: The status string to normalize.

    Returns:
        Normalized status string.
    """
    return COMMON_STATUS_MAP.get(status.lower(), status)


class JiraComment(BaseModel):
    """Jira comment."""

    author: str = Field(description="Display name of the comment author.")
    created: str = Field(
        description="ISO timestamp when the comment was created."
    )
    body: str = Field(description="Comment body text.")


class JiraTicket(BaseModel):
    """Jira ticket summary information.

    Note: status, priority, and type are flexible string fields. The available
    values depend on your Jira project configuration.
    """

    key: str = Field(description="Jira ticket key (e.g., PROJ-123).")
    summary: str = Field(description="Ticket summary/title.")
    status: str = Field(
        description="Current status (e.g., Open, In Progress, Done)."
    )
    priority: str = Field(
        description="Priority level (e.g., High, Medium, Low)."
    )
    type: str = Field(description="Issue type (e.g., Bug, Story, Task, Epic).")
    assignee: str | None = Field(
        default=None, description="Assignee display name."
    )
    reporter: str | None = Field(
        default=None, description="Reporter display name."
    )
    created: str | None = Field(
        default=None, description="ISO timestamp when created."
    )
    updated: str | None = Field(
        default=None, description="ISO timestamp when last updated."
    )
    description: str | None = Field(
        default=None, description="Ticket description."
    )


class JiraTicketDetail(JiraTicket):
    """Detailed Jira ticket with comments."""

    comments: list[JiraComment] = Field(
        default_factory=list, description="List of comments."
    )
