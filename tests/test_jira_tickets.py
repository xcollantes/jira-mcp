"""Tests for jira_tickets module."""

import pytest

from src.models.jira_tickets import (
    COMMON_STATUS_MAP,
    JiraComment,
    JiraTicket,
    JiraTicketDetail,
    normalize_status,
)


class TestNormalizeStatus:
    """Tests for normalize_status function."""

    @pytest.mark.parametrize(
        "input_status,expected",
        [
            ("open", "Open"),
            ("OPEN", "Open"),
            ("Open", "Open"),
            ("in progress", "In Progress"),
            ("IN PROGRESS", "In Progress"),
            ("done", "Done"),
            ("closed", "Closed"),
            ("todo", "To Do"),
            ("to do", "To Do"),
            ("backlog", "Backlog"),
            ("blocked", "Blocked"),
            ("in review", "In Review"),
            ("ready for review", "Ready for Review"),
            ("ready for qa", "Ready for QA"),
            ("in qa", "In QA"),
            ("deployed", "Deployed"),
            ("canceled", "Canceled"),
        ],
    )
    def test_common_statuses(self, input_status: str, expected: str) -> None:
        """Test normalization of common statuses."""
        assert normalize_status(input_status) == expected

    def test_unknown_status_returns_as_is(self) -> None:
        """Test that unknown statuses are returned unchanged."""
        assert normalize_status("Custom Status") == "Custom Status"
        assert normalize_status("My Special Status") == "My Special Status"

    def test_empty_string(self) -> None:
        """Test handling of empty string."""
        assert normalize_status("") == ""

    def test_status_map_is_complete(self) -> None:
        """Test that status map contains expected entries."""
        expected_statuses = [
            "open",
            "in progress",
            "done",
            "closed",
            "todo",
            "backlog",
        ]
        for status in expected_statuses:
            assert status in COMMON_STATUS_MAP


class TestJiraComment:
    """Tests for JiraComment model."""

    def test_comment_creation(self) -> None:
        """Test creating a JiraComment instance."""
        comment = JiraComment(
            author="John Doe",
            created="2024-01-15T10:30:00.000+0000",
            body="This is a test comment.",
        )
        assert comment.author == "John Doe"
        assert comment.created == "2024-01-15T10:30:00.000+0000"
        assert comment.body == "This is a test comment."

    def test_comment_with_multiline_body(self) -> None:
        """Test comment with multiline body."""
        body = "Line 1\nLine 2\nLine 3"
        comment = JiraComment(
            author="Jane Smith",
            created="2024-01-15T11:00:00.000+0000",
            body=body,
        )
        assert comment.body == body
        assert "\n" in comment.body

    def test_comment_with_empty_body(self) -> None:
        """Test comment with empty body."""
        comment = JiraComment(
            author="John Doe",
            created="2024-01-15T10:30:00.000+0000",
            body="",
        )
        assert comment.body == ""


class TestJiraTicket:
    """Tests for JiraTicket model."""

    def test_ticket_creation_with_all_fields(self) -> None:
        """Test creating a JiraTicket with all fields."""
        ticket = JiraTicket(
            key="TEST-123",
            summary="Test ticket summary",
            status="Open",
            priority="High",
            type="Bug",
            assignee="John Doe",
            reporter="Jane Smith",
            created="2024-01-10T09:00:00.000+0000",
            updated="2024-01-15T10:30:00.000+0000",
            description="Test description",
        )
        assert ticket.key == "TEST-123"
        assert ticket.summary == "Test ticket summary"
        assert ticket.status == "Open"
        assert ticket.priority == "High"
        assert ticket.type == "Bug"
        assert ticket.assignee == "John Doe"
        assert ticket.reporter == "Jane Smith"
        assert ticket.created == "2024-01-10T09:00:00.000+0000"
        assert ticket.updated == "2024-01-15T10:30:00.000+0000"
        assert ticket.description == "Test description"

    def test_ticket_creation_minimal(self) -> None:
        """Test creating a JiraTicket with minimal required fields."""
        ticket = JiraTicket(
            key="TEST-456",
            summary="Minimal ticket",
            status="Open",
            priority="Medium",
            type="Task",
        )
        assert ticket.key == "TEST-456"
        assert ticket.assignee is None
        assert ticket.reporter is None
        assert ticket.created is None
        assert ticket.updated is None
        assert ticket.description is None

    def test_ticket_with_none_optional_fields(self) -> None:
        """Test ticket with explicit None for optional fields."""
        ticket = JiraTicket(
            key="TEST-789",
            summary="Test",
            status="Open",
            priority="Low",
            type="Story",
            assignee=None,
            reporter=None,
        )
        assert ticket.assignee is None
        assert ticket.reporter is None

    def test_ticket_key_format(self) -> None:
        """Test various ticket key formats."""
        # Standard format.
        ticket1 = JiraTicket(
            key="PROJ-123",
            summary="Test",
            status="Open",
            priority="High",
            type="Bug",
        )
        assert ticket1.key == "PROJ-123"

        # Long project key.
        ticket2 = JiraTicket(
            key="VERYLONGPROJECT-1",
            summary="Test",
            status="Open",
            priority="High",
            type="Bug",
        )
        assert ticket2.key == "VERYLONGPROJECT-1"


class TestJiraTicketDetail:
    """Tests for JiraTicketDetail model."""

    def test_ticket_detail_creation(
        self, sample_jira_comment: JiraComment
    ) -> None:
        """Test creating a JiraTicketDetail instance."""
        detail = JiraTicketDetail(
            key="TEST-123",
            summary="Test ticket summary",
            status="Open",
            priority="High",
            type="Bug",
            assignee="John Doe",
            reporter="Jane Smith",
            created="2024-01-10T09:00:00.000+0000",
            updated="2024-01-15T10:30:00.000+0000",
            description="Test description",
            comments=[sample_jira_comment],
        )
        assert detail.key == "TEST-123"
        assert len(detail.comments) == 1
        assert detail.comments[0].author == "John Doe"

    def test_ticket_detail_inherits_from_ticket(self) -> None:
        """Test that JiraTicketDetail inherits from JiraTicket."""
        detail = JiraTicketDetail(
            key="TEST-123",
            summary="Test",
            status="Open",
            priority="High",
            type="Bug",
        )
        assert isinstance(detail, JiraTicket)

    def test_ticket_detail_empty_comments(self) -> None:
        """Test ticket detail with empty comments list."""
        detail = JiraTicketDetail(
            key="TEST-123",
            summary="Test",
            status="Open",
            priority="High",
            type="Bug",
            comments=[],
        )
        assert detail.comments == []

    def test_ticket_detail_default_comments(self) -> None:
        """Test ticket detail with default empty comments."""
        detail = JiraTicketDetail(
            key="TEST-123",
            summary="Test",
            status="Open",
            priority="High",
            type="Bug",
        )
        assert detail.comments == []

    def test_ticket_detail_multiple_comments(self) -> None:
        """Test ticket detail with multiple comments."""
        comments = [
            JiraComment(
                author=f"User {i}",
                created=f"2024-01-{10 + i}T10:00:00.000+0000",
                body=f"Comment {i}",
            )
            for i in range(5)
        ]
        detail = JiraTicketDetail(
            key="TEST-123",
            summary="Test",
            status="Open",
            priority="High",
            type="Bug",
            comments=comments,
        )
        assert len(detail.comments) == 5
        assert detail.comments[0].author == "User 0"
        assert detail.comments[4].author == "User 4"
