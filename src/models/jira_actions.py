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
