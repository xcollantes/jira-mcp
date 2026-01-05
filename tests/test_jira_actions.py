"""Tests for jira_actions module."""

import pytest
from src.models.jira_actions import (
    AddCommentResult,
    AssignToMeResult,
    CreateTicketResult,
    MoveTicketResult,
    UpdateDescriptionResult,
)


class TestCreateTicketResult:
    """Tests for CreateTicketResult model."""

    def test_successful_creation(self) -> None:
        """Test successful ticket creation result."""
        result = CreateTicketResult(
            success=True,
            ticket_key="TEST-123",
            ticket_url="https://jira.example.com/browse/TEST-123",
        )
        assert result.success is True
        assert result.ticket_key == "TEST-123"
        assert result.ticket_url == "https://jira.example.com/browse/TEST-123"
        assert result.error is None

    def test_failed_creation(self) -> None:
        """Test failed ticket creation result."""
        result = CreateTicketResult(
            success=False,
            error="Permission denied",
        )
        assert result.success is False
        assert result.ticket_key is None
        assert result.ticket_url is None
        assert result.error == "Permission denied"

    def test_default_values(self) -> None:
        """Test default values for optional fields."""
        result = CreateTicketResult(success=True)
        assert result.ticket_key is None
        assert result.ticket_url is None
        assert result.error is None


class TestMoveTicketResult:
    """Tests for MoveTicketResult model."""

    def test_successful_move(self) -> None:
        """Test successful ticket move result."""
        result = MoveTicketResult(
            success=True,
            ticket_key="TEST-123",
            previous_status="Open",
            new_status="In Progress",
            message="Successfully moved TEST-123 from Open to In Progress",
        )
        assert result.success is True
        assert result.ticket_key == "TEST-123"
        assert result.previous_status == "Open"
        assert result.new_status == "In Progress"
        assert "Successfully moved" in result.message

    def test_move_to_same_status(self) -> None:
        """Test moving ticket to same status."""
        result = MoveTicketResult(
            success=True,
            ticket_key="TEST-123",
            previous_status="Open",
            new_status="Open",
            message="Ticket already in status Open",
        )
        assert result.previous_status == result.new_status


class TestAddCommentResult:
    """Tests for AddCommentResult model."""

    def test_successful_comment(self) -> None:
        """Test successful comment addition result."""
        result = AddCommentResult(
            success=True,
            ticket_key="TEST-123",
            message="Successfully added comment to TEST-123",
        )
        assert result.success is True
        assert result.ticket_key == "TEST-123"
        assert "Successfully added" in result.message

    def test_comment_with_different_tickets(self) -> None:
        """Test comment result with different ticket keys."""
        result1 = AddCommentResult(
            success=True,
            ticket_key="PROJ-1",
            message="Added",
        )
        result2 = AddCommentResult(
            success=True,
            ticket_key="ANOTHER-999",
            message="Added",
        )
        assert result1.ticket_key != result2.ticket_key


class TestAssignToMeResult:
    """Tests for AssignToMeResult model."""

    def test_successful_assignment(self) -> None:
        """Test successful ticket assignment result."""
        result = AssignToMeResult(
            success=True,
            ticket_key="TEST-123",
            assignee="john.doe@example.com",
            message="Successfully assigned TEST-123 to john.doe@example.com",
        )
        assert result.success is True
        assert result.ticket_key == "TEST-123"
        assert result.assignee == "john.doe@example.com"
        assert result.assignee in result.message

    def test_assignment_with_display_name(self) -> None:
        """Test assignment with display name as assignee."""
        result = AssignToMeResult(
            success=True,
            ticket_key="TEST-123",
            assignee="John Doe",
            message="Successfully assigned TEST-123 to John Doe",
        )
        assert result.assignee == "John Doe"


class TestUpdateDescriptionResult:
    """Tests for UpdateDescriptionResult model."""

    def test_successful_update(self) -> None:
        """Test successful description update result."""
        result = UpdateDescriptionResult(
            success=True,
            ticket_key="TEST-123",
            message="Successfully updated description for TEST-123",
        )
        assert result.success is True
        assert result.ticket_key == "TEST-123"
        assert "Successfully updated" in result.message

    def test_update_message_format(self) -> None:
        """Test that update message contains ticket key."""
        result = UpdateDescriptionResult(
            success=True,
            ticket_key="MYPROJECT-456",
            message="Successfully updated description for MYPROJECT-456",
        )
        assert result.ticket_key in result.message
