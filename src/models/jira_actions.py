"""Models for Jira objects."""

from pydantic import BaseModel


class CreateTicketResult(BaseModel):
    """Result of creating a ticket."""

    success: bool
    ticket_key: str | None = None
    ticket_url: str | None = None
    error: str | None = None


class MoveTicketResult(BaseModel):
    """Result of moving a ticket."""

    success: bool
    ticket_key: str
    previous_status: str
    new_status: str
    message: str


class AddCommentResult(BaseModel):
    """Result of adding a comment."""

    success: bool
    ticket_key: str
    message: str


class AssignToMeResult(BaseModel):
    """Result of assigning ticket to current user."""

    success: bool
    ticket_key: str
    assignee: str
    message: str


class UpdateDescriptionResult(BaseModel):
    """Result of updating ticket description."""

    success: bool
    ticket_key: str
    message: str


class Sprint(BaseModel):
    """Jira sprint information."""

    id: int
    name: str
    state: str
    start_date: str | None = None
    end_date: str | None = None
    goal: str | None = None


class ListSprintsResult(BaseModel):
    """Result of listing sprints."""

    sprints: list[Sprint]


class AddToSprintResult(BaseModel):
    """Result of adding ticket to sprint."""

    success: bool
    ticket_key: str
    sprint_id: int
    message: str


class RemoveFromSprintResult(BaseModel):
    """Result of removing ticket from sprint."""

    success: bool
    ticket_key: str
    message: str


class EditTicketResult(BaseModel):
    """Result of editing ticket fields."""

    success: bool
    ticket_key: str
    message: str
    updated_fields: list[str]
