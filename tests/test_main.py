"""Tests for main module."""

import logging
import sys
from unittest.mock import MagicMock, patch

import pytest

# Need to mock the environment variables before importing main.
with patch.dict(
    "os.environ",
    {"JIRA_API_TOKEN": "test-token", "JIRA_AUTH_TYPE": "basic"},
):
    from src.main import (
        add_comment_tool,
        assign_to_me_tool,
        create_ticket_tool,
        get_ticket_tool,
        list_tickets_tool,
        move_ticket_tool,
        open_ticket_in_browser_tool,
        setup_logging,
        update_ticket_description_tool,
    )


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_default_level(self) -> None:
        """Test setup_logging with default (INFO) level."""
        with patch("logging.basicConfig") as mock_basic_config:
            setup_logging(debug=False)
            mock_basic_config.assert_called_once()
            call_kwargs = mock_basic_config.call_args[1]
            assert call_kwargs["level"] == logging.INFO

    def test_setup_logging_debug_level(self) -> None:
        """Test setup_logging with DEBUG level."""
        with patch("logging.basicConfig") as mock_basic_config:
            setup_logging(debug=True)
            mock_basic_config.assert_called_once()
            call_kwargs = mock_basic_config.call_args[1]
            assert call_kwargs["level"] == logging.DEBUG

    def test_setup_logging_uses_stderr(self) -> None:
        """Test setup_logging uses stderr for output."""
        with patch("logging.basicConfig") as mock_basic_config:
            setup_logging()
            call_kwargs = mock_basic_config.call_args[1]
            assert call_kwargs["stream"] == sys.stderr


class TestListTicketsTool:
    """Tests for list_tickets_tool function."""

    @patch("src.main.list_tickets")
    def test_list_tickets_success(self, mock_list_tickets: MagicMock) -> None:
        """Test list_tickets_tool with results."""
        from src.models.jira_tickets import JiraTicket

        mock_list_tickets.return_value = [
            JiraTicket(
                key="TEST-1",
                summary="Test ticket",
                status="Open",
                priority="High",
                type="Bug",
                assignee="John Doe",
            ),
            JiraTicket(
                key="TEST-2",
                summary="Another ticket",
                status="Done",
                priority="Low",
                type="Task",
            ),
        ]

        result = list_tickets_tool()

        assert "TEST-1" in result
        assert "Test ticket" in result
        assert "TEST-2" in result
        assert "John Doe" in result

    @patch("src.main.list_tickets")
    def test_list_tickets_no_results(self, mock_list_tickets: MagicMock) -> None:
        """Test list_tickets_tool with no results."""
        mock_list_tickets.return_value = []

        result = list_tickets_tool()

        assert result == "No tickets found."

    @patch("src.main.list_tickets")
    def test_list_tickets_error(self, mock_list_tickets: MagicMock) -> None:
        """Test list_tickets_tool with error."""
        mock_list_tickets.side_effect = ValueError("Test error")

        result = list_tickets_tool()

        assert "Error listing tickets" in result
        assert "Test error" in result

    @patch("src.main.list_tickets")
    def test_list_tickets_with_filters(self, mock_list_tickets: MagicMock) -> None:
        """Test list_tickets_tool passes filters correctly."""
        mock_list_tickets.return_value = []

        list_tickets_tool(
            jql="project = TEST",
            limit=10,
            assigned_to_me=True,
            status="Open",
        )

        mock_list_tickets.assert_called_once_with(
            jql="project = TEST",
            limit=10,
            assigned_to_me=True,
            unassigned=None,
            status="Open",
            project=None,
            created_recently=None,
            updated_recently=None,
            order_by=None,
            order_direction=None,
        )


class TestGetTicketTool:
    """Tests for get_ticket_tool function."""

    @patch("src.main.get_ticket")
    def test_get_ticket_success(self, mock_get_ticket: MagicMock) -> None:
        """Test get_ticket_tool with valid ticket."""
        from src.models.jira_tickets import JiraComment, JiraTicketDetail

        mock_get_ticket.return_value = JiraTicketDetail(
            key="TEST-123",
            summary="Test summary",
            status="Open",
            priority="High",
            type="Bug",
            assignee="John Doe",
            reporter="Jane Smith",
            created="2024-01-10T09:00:00.000+0000",
            updated="2024-01-15T10:30:00.000+0000",
            description="Test description",
            comments=[
                JiraComment(
                    author="John Doe",
                    created="2024-01-15T10:30:00.000+0000",
                    body="Test comment",
                )
            ],
        )

        result = get_ticket_tool("TEST-123")

        assert "TEST-123" in result
        assert "Test summary" in result
        assert "Open" in result
        assert "John Doe" in result
        assert "Test description" in result
        assert "Test comment" in result

    @patch("src.main.get_ticket")
    def test_get_ticket_no_description(self, mock_get_ticket: MagicMock) -> None:
        """Test get_ticket_tool with no description."""
        from src.models.jira_tickets import JiraTicketDetail

        mock_get_ticket.return_value = JiraTicketDetail(
            key="TEST-123",
            summary="Test",
            status="Open",
            priority="High",
            type="Bug",
            description=None,
        )

        result = get_ticket_tool("TEST-123")

        assert "No description provided" in result

    @patch("src.main.get_ticket")
    def test_get_ticket_no_comments(self, mock_get_ticket: MagicMock) -> None:
        """Test get_ticket_tool with no comments."""
        from src.models.jira_tickets import JiraTicketDetail

        mock_get_ticket.return_value = JiraTicketDetail(
            key="TEST-123",
            summary="Test",
            status="Open",
            priority="High",
            type="Bug",
            comments=[],
        )

        result = get_ticket_tool("TEST-123")

        assert "No comments" in result

    @patch("src.main.get_ticket")
    def test_get_ticket_error(self, mock_get_ticket: MagicMock) -> None:
        """Test get_ticket_tool with error."""
        mock_get_ticket.side_effect = ValueError("Ticket not found")

        result = get_ticket_tool("INVALID-123")

        assert "Error getting ticket" in result
        assert "INVALID-123" in result


class TestCreateTicketTool:
    """Tests for create_ticket_tool function."""

    @patch("src.main.create_ticket")
    def test_create_ticket_success(self, mock_create_ticket: MagicMock) -> None:
        """Test create_ticket_tool success."""
        from src.models.jira_actions import CreateTicketResult

        mock_create_ticket.return_value = CreateTicketResult(
            success=True,
            ticket_key="TEST-456",
            ticket_url="https://jira.example.com/browse/TEST-456",
        )

        result = create_ticket_tool(
            project="TEST",
            issue_type="Bug",
            summary="New bug",
        )

        assert "Successfully created" in result
        assert "TEST-456" in result

    @patch("src.main.create_ticket")
    def test_create_ticket_failure(self, mock_create_ticket: MagicMock) -> None:
        """Test create_ticket_tool failure."""
        from src.models.jira_actions import CreateTicketResult

        mock_create_ticket.return_value = CreateTicketResult(
            success=False,
            error="Project not found",
        )

        result = create_ticket_tool(
            project="INVALID",
            issue_type="Bug",
            summary="Test",
        )

        assert "Failed to create ticket" in result
        assert "Project not found" in result

    @patch("src.main.create_ticket")
    def test_create_ticket_exception(self, mock_create_ticket: MagicMock) -> None:
        """Test create_ticket_tool with exception."""
        mock_create_ticket.side_effect = Exception("Network error")

        result = create_ticket_tool(
            project="TEST",
            issue_type="Bug",
            summary="Test",
        )

        assert "Error creating ticket" in result


class TestMoveTicketTool:
    """Tests for move_ticket_tool function."""

    @patch("src.main.move_ticket")
    def test_move_ticket_success(self, mock_move_ticket: MagicMock) -> None:
        """Test move_ticket_tool success."""
        from src.models.jira_actions import MoveTicketResult

        mock_move_ticket.return_value = MoveTicketResult(
            success=True,
            ticket_key="TEST-123",
            previous_status="Open",
            new_status="In Progress",
            message="Successfully moved TEST-123 from Open to In Progress",
        )

        result = move_ticket_tool("TEST-123", "In Progress")

        assert "Successfully moved" in result

    @patch("src.main.move_ticket")
    def test_move_ticket_error(self, mock_move_ticket: MagicMock) -> None:
        """Test move_ticket_tool with error."""
        mock_move_ticket.side_effect = ValueError("Invalid transition")

        result = move_ticket_tool("TEST-123", "Invalid Status")

        assert "Error moving ticket" in result


class TestAddCommentTool:
    """Tests for add_comment_tool function."""

    @patch("src.main.add_comment")
    def test_add_comment_success(self, mock_add_comment: MagicMock) -> None:
        """Test add_comment_tool success."""
        from src.models.jira_actions import AddCommentResult

        mock_add_comment.return_value = AddCommentResult(
            success=True,
            ticket_key="TEST-123",
            message="Successfully added comment to TEST-123",
        )

        result = add_comment_tool("TEST-123", "Test comment")

        assert "Successfully added" in result

    @patch("src.main.add_comment")
    def test_add_comment_error(self, mock_add_comment: MagicMock) -> None:
        """Test add_comment_tool with error."""
        mock_add_comment.side_effect = ValueError("Permission denied")

        result = add_comment_tool("TEST-123", "Comment")

        assert "Error adding comment" in result


class TestAssignToMeTool:
    """Tests for assign_to_me_tool function."""

    @patch("src.main.assign_to_me")
    def test_assign_to_me_success(self, mock_assign_to_me: MagicMock) -> None:
        """Test assign_to_me_tool success."""
        from src.models.jira_actions import AssignToMeResult

        mock_assign_to_me.return_value = AssignToMeResult(
            success=True,
            ticket_key="TEST-123",
            assignee="john.doe@example.com",
            message="Successfully assigned TEST-123 to john.doe@example.com",
        )

        result = assign_to_me_tool("TEST-123")

        assert "Successfully assigned" in result

    @patch("src.main.assign_to_me")
    def test_assign_to_me_error(self, mock_assign_to_me: MagicMock) -> None:
        """Test assign_to_me_tool with error."""
        mock_assign_to_me.side_effect = ValueError("Auth error")

        result = assign_to_me_tool("TEST-123")

        assert "Error assigning ticket" in result


class TestOpenTicketInBrowserTool:
    """Tests for open_ticket_in_browser_tool function."""

    @patch("src.main.open_ticket_in_browser")
    def test_open_ticket_success(self, mock_open_ticket: MagicMock) -> None:
        """Test open_ticket_in_browser_tool success."""
        mock_open_ticket.return_value = "Successfully opened ticket TEST-123 in browser"

        result = open_ticket_in_browser_tool("TEST-123")

        assert "Successfully opened" in result

    @patch("src.main.open_ticket_in_browser")
    def test_open_ticket_error(self, mock_open_ticket: MagicMock) -> None:
        """Test open_ticket_in_browser_tool with error."""
        mock_open_ticket.side_effect = ValueError("Browser error")

        result = open_ticket_in_browser_tool("TEST-123")

        assert "Error opening ticket" in result


class TestUpdateTicketDescriptionTool:
    """Tests for update_ticket_description_tool function."""

    @patch("src.main.update_ticket_description")
    def test_update_description_success(
        self, mock_update_description: MagicMock
    ) -> None:
        """Test update_ticket_description_tool success."""
        from src.models.jira_actions import UpdateDescriptionResult

        mock_update_description.return_value = UpdateDescriptionResult(
            success=True,
            ticket_key="TEST-123",
            message="Successfully updated description for TEST-123",
        )

        result = update_ticket_description_tool("TEST-123", "New description")

        assert "Successfully updated" in result

    @patch("src.main.update_ticket_description")
    def test_update_description_error(self, mock_update_description: MagicMock) -> None:
        """Test update_ticket_description_tool with error."""
        mock_update_description.side_effect = ValueError("Permission denied")

        result = update_ticket_description_tool("TEST-123", "Description")

        assert "Error updating description" in result
