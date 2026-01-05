"""Tests for tool_utils module."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.models.jira_tickets import JiraTicket, JiraTicketDetail
from src.tools.jira_executor import CommandResult
from src.tools.tool_utils import (
    _build_jql_from_params,
    _convert_adf_to_text,
    add_comment,
    add_to_sprint,
    assign_to_me,
    create_ticket,
    edit_ticket,
    get_ticket,
    list_sprints,
    list_tickets,
    move_ticket,
    open_ticket_in_browser,
    remove_from_sprint,
    update_ticket_description,
)


class TestBuildJqlFromParams:
    """Tests for _build_jql_from_params function."""

    def test_raw_jql_takes_precedence(self) -> None:
        """Test that raw JQL overrides other params."""
        jql = _build_jql_from_params(
            jql="project = TEST",
            assigned_to_me=True,
            status="Open",
        )
        assert jql == "project = TEST"

    def test_assigned_to_me_filter(self) -> None:
        """Test assigned_to_me filter."""
        jql = _build_jql_from_params(assigned_to_me=True)
        assert jql == "assignee = currentUser()"

    def test_unassigned_filter(self) -> None:
        """Test unassigned filter."""
        jql = _build_jql_from_params(unassigned=True)
        assert jql == "assignee is EMPTY"

    def test_status_filter(self) -> None:
        """Test status filter with normalization."""
        jql = _build_jql_from_params(status="in progress")
        assert jql == 'status = "In Progress"'

    def test_status_filter_custom(self) -> None:
        """Test status filter with custom status."""
        jql = _build_jql_from_params(status="Custom Status")
        assert jql == 'status = "Custom Status"'

    def test_project_filter(self) -> None:
        """Test project filter."""
        jql = _build_jql_from_params(project="TEST")
        assert jql == "project = TEST"

    def test_created_recently_filter(self) -> None:
        """Test created_recently filter."""
        jql = _build_jql_from_params(created_recently=True)
        assert jql == "created >= -7d"

    def test_updated_recently_filter(self) -> None:
        """Test updated_recently filter."""
        jql = _build_jql_from_params(updated_recently=True)
        assert jql == "updated >= -7d"

    def test_combined_filters(self) -> None:
        """Test multiple filters combined with AND."""
        jql = _build_jql_from_params(
            assigned_to_me=True,
            status="Open",
            project="TEST",
        )
        assert "assignee = currentUser()" in jql
        assert 'status = "Open"' in jql
        assert "project = TEST" in jql
        assert " AND " in jql

    def test_no_filters_returns_none(self) -> None:
        """Test that no filters returns None."""
        jql = _build_jql_from_params()
        assert jql is None

    def test_assigned_to_me_overrides_unassigned(self) -> None:
        """Test that assigned_to_me takes precedence over unassigned."""
        jql = _build_jql_from_params(assigned_to_me=True, unassigned=True)
        assert "currentUser()" in jql
        assert "EMPTY" not in jql


class TestConvertAdfToText:
    """Tests for _convert_adf_to_text function."""

    def test_simple_paragraph(self) -> None:
        """Test converting simple paragraph."""
        adf: dict[str, Any] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Hello world"}],
                }
            ],
        }
        result = _convert_adf_to_text(adf)
        assert result == "Hello world"

    def test_multiple_paragraphs(self) -> None:
        """Test converting multiple paragraphs."""
        adf: dict[str, Any] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "First paragraph"}],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Second paragraph"}],
                },
            ],
        }
        result = _convert_adf_to_text(adf)
        assert "First paragraph" in result
        assert "Second paragraph" in result

    def test_heading(self) -> None:
        """Test converting heading."""
        adf: dict[str, Any] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": "My Heading"}],
                }
            ],
        }
        result = _convert_adf_to_text(adf)
        assert result == "## My Heading"

    def test_bullet_list(self) -> None:
        """Test converting bullet list."""
        adf: dict[str, Any] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Item 1"}],
                                }
                            ],
                        },
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Item 2"}],
                                }
                            ],
                        },
                    ],
                }
            ],
        }
        result = _convert_adf_to_text(adf)
        assert "- Item 1" in result
        assert "- Item 2" in result

    def test_ordered_list(self) -> None:
        """Test converting ordered list."""
        adf: dict[str, Any] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "orderedList",
                    "attrs": {"start": 1},
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "First"}],
                                }
                            ],
                        },
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Second"}],
                                }
                            ],
                        },
                    ],
                }
            ],
        }
        result = _convert_adf_to_text(adf)
        assert "1. First" in result
        assert "2. Second" in result

    def test_code_block(self) -> None:
        """Test converting code block."""
        adf: dict[str, Any] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "codeBlock",
                    "attrs": {"language": "python"},
                    "content": [{"type": "text", "text": "print('hello')"}],
                }
            ],
        }
        result = _convert_adf_to_text(adf)
        assert "```python" in result
        assert "print('hello')" in result
        assert "```" in result

    def test_text_marks_bold(self) -> None:
        """Test converting bold text."""
        adf: dict[str, Any] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "bold text",
                            "marks": [{"type": "strong"}],
                        }
                    ],
                }
            ],
        }
        result = _convert_adf_to_text(adf)
        assert "**bold text**" in result

    def test_text_marks_italic(self) -> None:
        """Test converting italic text."""
        adf: dict[str, Any] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "italic text",
                            "marks": [{"type": "em"}],
                        }
                    ],
                }
            ],
        }
        result = _convert_adf_to_text(adf)
        assert "*italic text*" in result

    def test_text_marks_code(self) -> None:
        """Test converting inline code."""
        adf: dict[str, Any] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "code",
                            "marks": [{"type": "code"}],
                        }
                    ],
                }
            ],
        }
        result = _convert_adf_to_text(adf)
        assert "`code`" in result

    def test_text_marks_strikethrough(self) -> None:
        """Test converting strikethrough text."""
        adf: dict[str, Any] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "deleted",
                            "marks": [{"type": "strike"}],
                        }
                    ],
                }
            ],
        }
        result = _convert_adf_to_text(adf)
        assert "~~deleted~~" in result

    def test_horizontal_rule(self) -> None:
        """Test converting horizontal rule."""
        adf: dict[str, Any] = {
            "type": "doc",
            "version": 1,
            "content": [{"type": "rule"}],
        }
        result = _convert_adf_to_text(adf)
        assert "---" in result

    def test_blockquote(self) -> None:
        """Test converting blockquote."""
        adf: dict[str, Any] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "blockquote",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Quoted text"}],
                        }
                    ],
                }
            ],
        }
        result = _convert_adf_to_text(adf)
        assert "> Quoted text" in result

    def test_hard_break(self) -> None:
        """Test converting hard break."""
        adf: dict[str, Any] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Line 1"},
                        {"type": "hardBreak"},
                        {"type": "text", "text": "Line 2"},
                    ],
                }
            ],
        }
        result = _convert_adf_to_text(adf)
        assert "Line 1\nLine 2" in result

    def test_empty_document(self) -> None:
        """Test converting empty document."""
        adf: dict[str, Any] = {
            "type": "doc",
            "version": 1,
            "content": [],
        }
        result = _convert_adf_to_text(adf)
        assert result == ""


class TestListTickets:
    """Tests for list_tickets function."""

    def test_list_tickets_success(self, mock_execute_jira_command: MagicMock) -> None:
        """Test listing tickets successfully."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="TEST-1\tTest ticket 1\tOpen\tHigh\tBug\tJohn Doe\nTEST-2\tTest ticket 2\tDone\tMedium\tStory\t",
            stderr="",
            exit_code=0,
        )

        tickets = list_tickets()

        assert len(tickets) == 2
        assert tickets[0].key == "TEST-1"
        assert tickets[0].status == "Open"
        assert tickets[0].assignee == "John Doe"
        assert tickets[1].key == "TEST-2"
        assert tickets[1].assignee is None

    def test_list_tickets_with_filters(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test listing tickets with filters."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="TEST-1\tTest\tOpen\tHigh\tBug\t",
            stderr="",
            exit_code=0,
        )

        list_tickets(assigned_to_me=True, status="Open", project="TEST")

        # Verify the command args include JQL.
        call_args = mock_execute_jira_command.call_args[0][0]
        assert "--jql" in call_args

    def test_list_tickets_no_results(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test listing tickets with no results."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="No result found",
            exit_code=1,
        )

        tickets = list_tickets()

        assert tickets == []

    def test_list_tickets_with_limit(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test listing tickets with limit."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="TEST-1\tTest\tOpen\tHigh\tBug\t",
            stderr="",
            exit_code=0,
        )

        list_tickets(limit=10)

        call_args = mock_execute_jira_command.call_args[0][0]
        assert "--paginate" in call_args
        assert "0:10" in call_args

    def test_list_tickets_with_ordering(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test listing tickets with ordering."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="TEST-1\tTest\tOpen\tHigh\tBug\t",
            stderr="",
            exit_code=0,
        )

        list_tickets(order_by="created", order_direction="asc")

        call_args = mock_execute_jira_command.call_args[0][0]
        assert "--order-by" in call_args
        assert "created" in call_args
        assert "--reverse" in call_args

    def test_list_tickets_error(self, mock_execute_jira_command: MagicMock) -> None:
        """Test listing tickets with error."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="Permission denied",
            exit_code=1,
        )

        with pytest.raises(ValueError) as exc_info:
            list_tickets()

        assert "Failed to list tickets" in str(exc_info.value)


class TestGetTicket:
    """Tests for get_ticket function."""

    def test_get_ticket_success(
        self,
        mock_execute_jira_command: MagicMock,
        sample_raw_ticket_json: dict[str, Any],
    ) -> None:
        """Test getting ticket successfully."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout=json.dumps(sample_raw_ticket_json),
            stderr="",
            exit_code=0,
        )

        ticket = get_ticket("TEST-123")

        assert ticket.key == "TEST-123"
        assert ticket.summary == "Test ticket summary"
        assert ticket.status == "Open"
        assert ticket.assignee == "John Doe"
        assert len(ticket.comments) == 1

    def test_get_ticket_with_comments(
        self,
        mock_execute_jira_command: MagicMock,
        sample_raw_ticket_json: dict[str, Any],
    ) -> None:
        """Test getting ticket with comments count."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout=json.dumps(sample_raw_ticket_json),
            stderr="",
            exit_code=0,
        )

        get_ticket("TEST-123", comments=10)

        call_args = mock_execute_jira_command.call_args[0][0]
        assert "--comments" in call_args
        assert "10" in call_args

    def test_get_ticket_not_found(self, mock_execute_jira_command: MagicMock) -> None:
        """Test getting nonexistent ticket."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="Issue does not exist",
            exit_code=1,
        )

        with pytest.raises(ValueError) as exc_info:
            get_ticket("INVALID-999")

        assert "Failed to get ticket" in str(exc_info.value)

    def test_get_ticket_invalid_json(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test getting ticket with invalid JSON response."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="not json",
            stderr="",
            exit_code=0,
        )

        with pytest.raises(ValueError) as exc_info:
            get_ticket("TEST-123")

        assert "Failed to parse" in str(exc_info.value)


class TestCreateTicket:
    """Tests for create_ticket function."""

    def test_create_ticket_success(self, mock_execute_jira_command: MagicMock) -> None:
        """Test creating ticket successfully."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout='{"key": "TEST-456", "self": "https://jira.example.com/rest/api/2/issue/12345"}',
            stderr="",
            exit_code=0,
        )

        result = create_ticket(
            project="TEST",
            issue_type="Bug",
            summary="New bug",
        )

        assert result.success is True
        assert result.ticket_key == "TEST-456"

    def test_create_ticket_with_all_options(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test creating ticket with all options."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout='{"key": "TEST-456", "self": "https://example.com"}',
            stderr="",
            exit_code=0,
        )

        create_ticket(
            project="TEST",
            issue_type="Story",
            summary="New story",
            description="Description text",
            priority="High",
            assignee="john.doe",
            labels=["label1", "label2"],
            components=["comp1"],
        )

        call_args = mock_execute_jira_command.call_args[0][0]
        assert "--priority" in call_args
        assert "High" in call_args
        assert "--assignee" in call_args
        assert "--label" in call_args
        assert "--component" in call_args

    def test_create_ticket_failure(self, mock_execute_jira_command: MagicMock) -> None:
        """Test creating ticket with failure."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="Project not found",
            exit_code=1,
        )

        result = create_ticket(
            project="INVALID",
            issue_type="Bug",
            summary="Test",
        )

        assert result.success is False
        assert "Project not found" in result.error


class TestMoveTicket:
    """Tests for move_ticket function."""

    def test_move_ticket_success(self, mock_execute_jira_command: MagicMock) -> None:
        """Test moving ticket successfully."""
        # First call: get current status.
        # Second call: move ticket.
        mock_execute_jira_command.side_effect = [
            CommandResult(
                stdout="TEST-123\tOpen",
                stderr="",
                exit_code=0,
            ),
            CommandResult(
                stdout="",
                stderr="",
                exit_code=0,
            ),
        ]

        result = move_ticket("TEST-123", "In Progress")

        assert result.success is True
        assert result.previous_status == "Open"
        assert result.new_status == "In Progress"

    def test_move_ticket_normalizes_status(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test moving ticket normalizes status."""
        mock_execute_jira_command.side_effect = [
            CommandResult(stdout="TEST-123\tOpen", stderr="", exit_code=0),
            CommandResult(stdout="", stderr="", exit_code=0),
        ]

        result = move_ticket("TEST-123", "in progress")

        assert result.new_status == "In Progress"

    def test_move_ticket_get_status_fails(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test moving ticket when getting status fails."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="Ticket not found",
            exit_code=1,
        )

        with pytest.raises(ValueError) as exc_info:
            move_ticket("INVALID-123", "Done")

        assert "Failed to get current status" in str(exc_info.value)


class TestAddComment:
    """Tests for add_comment function."""

    def test_add_comment_success(self, mock_execute_jira_command: MagicMock) -> None:
        """Test adding comment successfully."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = add_comment("TEST-123", "This is a comment")

        assert result.success is True
        assert result.ticket_key == "TEST-123"

        # Verify stdin_input was passed.
        call_kwargs = mock_execute_jira_command.call_args[1]
        assert call_kwargs["stdin_input"] == "This is a comment"

    def test_add_comment_failure(self, mock_execute_jira_command: MagicMock) -> None:
        """Test adding comment with failure."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="Permission denied",
            exit_code=1,
        )

        with pytest.raises(ValueError) as exc_info:
            add_comment("TEST-123", "Comment")

        assert "Failed to add comment" in str(exc_info.value)


class TestAssignToMe:
    """Tests for assign_to_me function."""

    def test_assign_to_me_success(self, mock_execute_jira_command: MagicMock) -> None:
        """Test assigning ticket to current user successfully."""
        mock_execute_jira_command.side_effect = [
            CommandResult(stdout="john.doe@example.com", stderr="", exit_code=0),
            CommandResult(stdout="", stderr="", exit_code=0),
        ]

        result = assign_to_me("TEST-123")

        assert result.success is True
        assert result.assignee == "john.doe@example.com"
        assert result.ticket_key == "TEST-123"

    def test_assign_to_me_get_user_fails(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test assigning when getting current user fails."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="Auth error",
            exit_code=1,
        )

        with pytest.raises(ValueError) as exc_info:
            assign_to_me("TEST-123")

        assert "Failed to get current user" in str(exc_info.value)

    def test_assign_to_me_empty_user(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test assigning when current user is empty."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        with pytest.raises(ValueError) as exc_info:
            assign_to_me("TEST-123")

        assert "Unable to determine current user" in str(exc_info.value)


class TestOpenTicketInBrowser:
    """Tests for open_ticket_in_browser function."""

    def test_open_ticket_success(self, mock_execute_jira_command: MagicMock) -> None:
        """Test opening ticket in browser successfully."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = open_ticket_in_browser("TEST-123")

        assert "Successfully opened" in result
        assert "TEST-123" in result

    def test_open_ticket_failure(self, mock_execute_jira_command: MagicMock) -> None:
        """Test opening ticket with failure."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="Error opening browser",
            exit_code=1,
        )

        with pytest.raises(ValueError) as exc_info:
            open_ticket_in_browser("TEST-123")

        assert "Failed to open ticket" in str(exc_info.value)


class TestUpdateTicketDescription:
    """Tests for update_ticket_description function."""

    def test_update_description_success(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test updating ticket description successfully."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = update_ticket_description("TEST-123", "New description")

        assert result.success is True
        assert result.ticket_key == "TEST-123"

        # Verify stdin_input was passed.
        call_kwargs = mock_execute_jira_command.call_args[1]
        assert call_kwargs["stdin_input"] == "New description"

    def test_update_description_failure(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test updating description with failure."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="Permission denied",
            exit_code=1,
        )

        with pytest.raises(ValueError) as exc_info:
            update_ticket_description("TEST-123", "Description")

        assert "Failed to update ticket" in str(exc_info.value)


class TestListSprints:
    """Tests for list_sprints function."""

    def test_list_sprints_success(self, mock_execute_jira_command: MagicMock) -> None:
        """Test listing sprints successfully."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="123\tSprint 1\tactive\t2024-01-01\t2024-01-14\n456\tSprint 2\tfuture\t2024-01-15\t2024-01-28",
            stderr="",
            exit_code=0,
        )

        result = list_sprints(board_id=1)

        assert len(result.sprints) == 2
        assert result.sprints[0].id == 123
        assert result.sprints[0].name == "Sprint 1"
        assert result.sprints[0].state == "active"
        assert result.sprints[0].start_date == "2024-01-01"
        assert result.sprints[0].end_date == "2024-01-14"
        assert result.sprints[1].id == 456
        assert result.sprints[1].name == "Sprint 2"
        assert result.sprints[1].state == "future"

    def test_list_sprints_with_state_filter(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test listing sprints with state filter."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="123\tSprint 1\tactive\t2024-01-01\t2024-01-14",
            stderr="",
            exit_code=0,
        )

        list_sprints(board_id=1, state="active")

        call_args = mock_execute_jira_command.call_args[0][0]
        assert "--state" in call_args
        assert "active" in call_args

    def test_list_sprints_with_limit(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test listing sprints with limit."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="123\tSprint 1\tactive\t2024-01-01\t2024-01-14",
            stderr="",
            exit_code=0,
        )

        list_sprints(board_id=1, limit=10)

        call_args = mock_execute_jira_command.call_args[0][0]
        assert "--paginate" in call_args
        assert "0:10" in call_args

    def test_list_sprints_no_results(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test listing sprints with no results."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="No result found",
            exit_code=1,
        )

        result = list_sprints(board_id=1)

        assert result.sprints == []

    def test_list_sprints_no_sprints_found(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test listing sprints with 'no sprints' message."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="no sprints found for board",
            exit_code=1,
        )

        result = list_sprints(board_id=1)

        assert result.sprints == []

    def test_list_sprints_error(self, mock_execute_jira_command: MagicMock) -> None:
        """Test listing sprints with error."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="Permission denied",
            exit_code=1,
        )

        with pytest.raises(ValueError) as exc_info:
            list_sprints(board_id=1)

        assert "Failed to list sprints" in str(exc_info.value)

    def test_list_sprints_partial_columns(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test listing sprints with only required columns."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="123\tSprint 1\tactive",
            stderr="",
            exit_code=0,
        )

        result = list_sprints(board_id=1)

        assert len(result.sprints) == 1
        assert result.sprints[0].id == 123
        assert result.sprints[0].name == "Sprint 1"
        assert result.sprints[0].state == "active"
        assert result.sprints[0].start_date is None
        assert result.sprints[0].end_date is None


class TestAddToSprint:
    """Tests for add_to_sprint function."""

    def test_add_to_sprint_success(self, mock_execute_jira_command: MagicMock) -> None:
        """Test adding ticket to sprint successfully."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = add_to_sprint("TEST-123", sprint_id=456)

        assert result.success is True
        assert result.ticket_key == "TEST-123"
        assert result.sprint_id == 456
        assert "Successfully added TEST-123 to sprint 456" in result.message

    def test_add_to_sprint_command_args(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test add_to_sprint command arguments."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        add_to_sprint("TEST-123", sprint_id=789)

        call_args = mock_execute_jira_command.call_args[0][0]
        assert "sprint" in call_args
        assert "add" in call_args
        assert "789" in call_args
        assert "TEST-123" in call_args

    def test_add_to_sprint_failure(self, mock_execute_jira_command: MagicMock) -> None:
        """Test adding ticket to sprint with failure."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="Sprint not found",
            exit_code=1,
        )

        with pytest.raises(ValueError) as exc_info:
            add_to_sprint("TEST-123", sprint_id=999)

        assert "Failed to add TEST-123 to sprint 999" in str(exc_info.value)


class TestRemoveFromSprint:
    """Tests for remove_from_sprint function."""

    def test_remove_from_sprint_success(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test removing ticket from sprint successfully."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = remove_from_sprint("TEST-123")

        assert result.success is True
        assert result.ticket_key == "TEST-123"
        assert "Successfully removed TEST-123 from its sprint" in result.message

    def test_remove_from_sprint_command_args(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test remove_from_sprint command arguments."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        remove_from_sprint("TEST-456")

        call_args = mock_execute_jira_command.call_args[0][0]
        assert "issue" in call_args
        assert "edit" in call_args
        assert "TEST-456" in call_args
        assert "--custom" in call_args
        assert "sprint=" in call_args
        assert "--no-input" in call_args

    def test_remove_from_sprint_failure(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test removing ticket from sprint with failure."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="Ticket not found",
            exit_code=1,
        )

        with pytest.raises(ValueError) as exc_info:
            remove_from_sprint("INVALID-999")

        assert "Failed to remove INVALID-999 from sprint" in str(exc_info.value)


class TestEditTicket:
    """Tests for edit_ticket function."""

    def test_edit_ticket_summary(self, mock_execute_jira_command: MagicMock) -> None:
        """Test editing ticket summary."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = edit_ticket("TEST-123", summary="New summary")

        assert result.success is True
        assert result.ticket_key == "TEST-123"
        assert "summary" in result.updated_fields

        call_args = mock_execute_jira_command.call_args[0][0]
        assert "--summary" in call_args
        assert "New summary" in call_args

    def test_edit_ticket_priority(self, mock_execute_jira_command: MagicMock) -> None:
        """Test editing ticket priority."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = edit_ticket("TEST-123", priority="High")

        assert result.success is True
        assert "priority" in result.updated_fields

        call_args = mock_execute_jira_command.call_args[0][0]
        assert "--priority" in call_args
        assert "High" in call_args

    def test_edit_ticket_assignee(self, mock_execute_jira_command: MagicMock) -> None:
        """Test editing ticket assignee."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = edit_ticket("TEST-123", assignee="john.doe")

        assert result.success is True
        assert "assignee" in result.updated_fields

        call_args = mock_execute_jira_command.call_args[0][0]
        assert "--assignee" in call_args
        assert "john.doe" in call_args

    def test_edit_ticket_unassign(self, mock_execute_jira_command: MagicMock) -> None:
        """Test unassigning ticket."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = edit_ticket("TEST-123", assignee="")

        assert result.success is True
        assert "assignee" in result.updated_fields

        call_args = mock_execute_jira_command.call_args[0][0]
        assert "--assignee" in call_args
        assert "x" in call_args

    def test_edit_ticket_labels(self, mock_execute_jira_command: MagicMock) -> None:
        """Test editing ticket labels."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = edit_ticket("TEST-123", labels=["bug", "urgent"])

        assert result.success is True
        assert "labels" in result.updated_fields

        call_args = mock_execute_jira_command.call_args[0][0]
        label_count = call_args.count("--label")
        assert label_count == 2

    def test_edit_ticket_add_labels(self, mock_execute_jira_command: MagicMock) -> None:
        """Test adding labels to ticket."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = edit_ticket("TEST-123", add_labels=["new-label"])

        assert result.success is True
        assert "labels (added)" in result.updated_fields

        call_args = mock_execute_jira_command.call_args[0][0]
        assert "--label" in call_args
        assert "+new-label" in call_args

    def test_edit_ticket_remove_labels(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test removing labels from ticket."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = edit_ticket("TEST-123", remove_labels=["old-label"])

        assert result.success is True
        assert "labels (removed)" in result.updated_fields

        call_args = mock_execute_jira_command.call_args[0][0]
        assert "--label" in call_args
        assert "-old-label" in call_args

    def test_edit_ticket_components(self, mock_execute_jira_command: MagicMock) -> None:
        """Test editing ticket components."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = edit_ticket("TEST-123", components=["backend", "api"])

        assert result.success is True
        assert "components" in result.updated_fields

        call_args = mock_execute_jira_command.call_args[0][0]
        component_count = call_args.count("--component")
        assert component_count == 2

    def test_edit_ticket_fix_versions(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test editing ticket fix versions."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = edit_ticket("TEST-123", fix_versions=["1.0.0", "1.1.0"])

        assert result.success is True
        assert "fix_versions" in result.updated_fields

        call_args = mock_execute_jira_command.call_args[0][0]
        version_count = call_args.count("--fix-version")
        assert version_count == 2

    def test_edit_ticket_parent(self, mock_execute_jira_command: MagicMock) -> None:
        """Test editing ticket parent."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = edit_ticket("TEST-123", parent="TEST-100")

        assert result.success is True
        assert "parent" in result.updated_fields

        call_args = mock_execute_jira_command.call_args[0][0]
        assert "--parent" in call_args
        assert "TEST-100" in call_args

    def test_edit_ticket_custom_fields(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test editing ticket custom fields."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = edit_ticket(
            "TEST-123",
            custom_fields={"customfield_10001": "value1", "story_points": "5"},
        )

        assert result.success is True
        assert "custom:customfield_10001" in result.updated_fields
        assert "custom:story_points" in result.updated_fields

        call_args = mock_execute_jira_command.call_args[0][0]
        custom_count = call_args.count("--custom")
        assert custom_count == 2

    def test_edit_ticket_multiple_fields(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test editing multiple ticket fields at once."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )

        result = edit_ticket(
            "TEST-123",
            summary="Updated summary",
            priority="Critical",
            assignee="jane.doe",
            labels=["critical-bug"],
        )

        assert result.success is True
        assert "summary" in result.updated_fields
        assert "priority" in result.updated_fields
        assert "assignee" in result.updated_fields
        assert "labels" in result.updated_fields

    def test_edit_ticket_no_fields_specified(
        self, mock_execute_jira_command: MagicMock
    ) -> None:
        """Test editing ticket with no fields specified."""
        result = edit_ticket("TEST-123")

        assert result.success is False
        assert "No fields specified to update" in result.message
        assert result.updated_fields == []

        # Verify command was not called.
        mock_execute_jira_command.assert_not_called()

    def test_edit_ticket_failure(self, mock_execute_jira_command: MagicMock) -> None:
        """Test editing ticket with failure."""
        mock_execute_jira_command.return_value = CommandResult(
            stdout="",
            stderr="Permission denied",
            exit_code=1,
        )

        with pytest.raises(ValueError) as exc_info:
            edit_ticket("TEST-123", summary="New summary")

        assert "Failed to edit ticket TEST-123" in str(exc_info.value)
