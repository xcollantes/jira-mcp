from typing import Literal

from pydantic import BaseModel, Field

# Status constants.
JIRA_STATUS_VALUES: tuple[str, ...] = (
    "open",
    "in progress",
    "in review",
    "done",
    "closed",
    "canceled",
    "todo",
    "to do",
)

JiraStatusValue = Literal[
    "open",
    "in progress",
    "in review",
    "done",
    "closed",
    "canceled",
    "todo",
    "to do",
]

# Map from lowercase enum values to Jira status names.
JIRA_STATUS_MAP: dict[str, str] = {
    "open": "Open",
    "in progress": "In Progress",
    "in review": "In Review",
    "done": "Done",
    "closed": "Closed",
    "canceled": "Canceled",
    "todo": "To Do",
    "to do": "To Do",
}


class JiraComment(BaseModel):
    """Jira comment."""

    author: str
    created: str
    body: str


class JiraTicket(BaseModel):
    """Jira ticket summary information."""

    key: str
    summary: str
    status: str
    priority: str
    type: str
    assignee: str | None = None
    reporter: str | None = None
    created: str | None = None
    updated: str | None = None
    description: str | None = None


class JiraTicketDetail(JiraTicket):
    """Detailed Jira ticket with comments."""

    comments: list[JiraComment] = Field(default_factory=list)
