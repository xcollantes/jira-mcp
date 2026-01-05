"""Shared pytest fixtures for jira-mcp tests."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from src.models.jira_actions import (
    AddCommentResult,
    AssignToMeResult,
    CreateTicketResult,
    MoveTicketResult,
    UpdateDescriptionResult,
)
from src.models.jira_tickets import JiraComment, JiraTicket, JiraTicketDetail
from src.tools.jira_executor import CommandResult


@pytest.fixture
def mock_command_result_success() -> CommandResult:
    """Create a successful command result."""
    return CommandResult(
        stdout="success output",
        stderr="",
        exit_code=0,
    )


@pytest.fixture
def mock_command_result_failure() -> CommandResult:
    """Create a failed command result."""
    return CommandResult(
        stdout="",
        stderr="error: command failed",
        exit_code=1,
    )


@pytest.fixture
def sample_jira_ticket() -> JiraTicket:
    """Create a sample JiraTicket for testing."""
    return JiraTicket(
        key="TEST-123",
        summary="Test ticket summary",
        status="Open",
        priority="High",
        type="Bug",
        assignee="John Doe",
        reporter="Jane Smith",
    )


@pytest.fixture
def sample_jira_comment() -> JiraComment:
    """Create a sample JiraComment for testing."""
    return JiraComment(
        author="John Doe",
        created="2024-01-15T10:30:00.000+0000",
        body="This is a test comment.",
    )


@pytest.fixture
def sample_jira_ticket_detail(
    sample_jira_ticket: JiraTicket,
    sample_jira_comment: JiraComment,
) -> JiraTicketDetail:
    """Create a sample JiraTicketDetail for testing."""
    return JiraTicketDetail(
        key=sample_jira_ticket.key,
        summary=sample_jira_ticket.summary,
        status=sample_jira_ticket.status,
        priority=sample_jira_ticket.priority,
        type=sample_jira_ticket.type,
        assignee=sample_jira_ticket.assignee,
        reporter=sample_jira_ticket.reporter,
        created="2024-01-10T09:00:00.000+0000",
        updated="2024-01-15T10:30:00.000+0000",
        description="This is a test ticket description.",
        comments=[sample_jira_comment],
    )


@pytest.fixture
def sample_raw_ticket_json() -> dict[str, Any]:
    """Create sample raw JSON response from jira-cli for a ticket."""
    return {
        "key": "TEST-123",
        "fields": {
            "summary": "Test ticket summary",
            "status": {"name": "Open"},
            "priority": {"name": "High"},
            "issuetype": {"name": "Bug"},
            "assignee": {"displayName": "John Doe"},
            "reporter": {"displayName": "Jane Smith"},
            "created": "2024-01-10T09:00:00.000+0000",
            "updated": "2024-01-15T10:30:00.000+0000",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Test description"}],
                    }
                ],
            },
            "comment": {
                "comments": [
                    {
                        "author": {"displayName": "John Doe"},
                        "created": "2024-01-15T10:30:00.000+0000",
                        "body": {
                            "type": "doc",
                            "version": 1,
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {"type": "text", "text": "Test comment"}
                                    ],
                                }
                            ],
                        },
                    }
                ]
            },
        },
    }


@pytest.fixture
def sample_create_ticket_result() -> CreateTicketResult:
    """Create a sample CreateTicketResult for testing."""
    return CreateTicketResult(
        success=True,
        ticket_key="TEST-456",
        ticket_url="https://jira.example.com/browse/TEST-456",
    )


@pytest.fixture
def sample_move_ticket_result() -> MoveTicketResult:
    """Create a sample MoveTicketResult for testing."""
    return MoveTicketResult(
        success=True,
        ticket_key="TEST-123",
        previous_status="Open",
        new_status="In Progress",
        message="Successfully moved TEST-123 from Open to In Progress",
    )


@pytest.fixture
def sample_add_comment_result() -> AddCommentResult:
    """Create a sample AddCommentResult for testing."""
    return AddCommentResult(
        success=True,
        ticket_key="TEST-123",
        message="Successfully added comment to TEST-123",
    )


@pytest.fixture
def sample_assign_to_me_result() -> AssignToMeResult:
    """Create a sample AssignToMeResult for testing."""
    return AssignToMeResult(
        success=True,
        ticket_key="TEST-123",
        assignee="john.doe@example.com",
        message="Successfully assigned TEST-123 to john.doe@example.com",
    )


@pytest.fixture
def sample_update_description_result() -> UpdateDescriptionResult:
    """Create a sample UpdateDescriptionResult for testing."""
    return UpdateDescriptionResult(
        success=True,
        ticket_key="TEST-123",
        message="Successfully updated description for TEST-123",
    )


@pytest.fixture
def mock_execute_jira_command():
    """Mock the execute_jira_command function."""
    with patch("src.tools.tool_utils.execute_jira_command") as mock:
        yield mock


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for testing jira_executor."""
    with patch("subprocess.run") as mock:
        yield mock


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(
        "os.environ",
        {
            "JIRA_API_TOKEN": "test-token",
            "JIRA_AUTH_TYPE": "basic",
        },
    ):
        yield
