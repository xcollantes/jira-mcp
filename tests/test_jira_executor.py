"""Tests for jira_executor module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.tools.jira_executor import (
    CommandResult,
    execute_jira_command,
    execute_jira_command_json,
    get_jira_cli_path,
)


class TestCommandResult:
    """Tests for CommandResult model."""

    def test_command_result_creation(self) -> None:
        """Test creating a CommandResult instance."""
        result = CommandResult(
            stdout="output",
            stderr="error",
            exit_code=0,
        )
        assert result.stdout == "output"
        assert result.stderr == "error"
        assert result.exit_code == 0

    def test_command_result_defaults(self) -> None:
        """Test CommandResult with empty strings."""
        result = CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )
        assert result.stdout == ""
        assert result.stderr == ""

    def test_command_result_with_multiline_output(self) -> None:
        """Test CommandResult with multiline output."""
        multiline = "line1\nline2\nline3"
        result = CommandResult(
            stdout=multiline,
            stderr="",
            exit_code=0,
        )
        assert result.stdout == multiline
        assert "line2" in result.stdout


class TestGetJiraCliPath:
    """Tests for get_jira_cli_path function."""

    def test_default_path(self) -> None:
        """Test default jira-cli path."""
        with patch.dict("os.environ", {}, clear=True):
            path = get_jira_cli_path()
            assert path == "jira"

    def test_custom_path_from_env(self) -> None:
        """Test custom jira-cli path from environment variable."""
        with patch.dict("os.environ", {"JIRA_CLI_PATH": "/custom/path/jira"}):
            path = get_jira_cli_path()
            assert path == "/custom/path/jira"


class TestExecuteJiraCommand:
    """Tests for execute_jira_command function."""

    def test_successful_command(self, mock_subprocess_run: MagicMock) -> None:
        """Test executing a successful jira command."""
        mock_subprocess_run.return_value = MagicMock(
            stdout="success",
            stderr="",
            returncode=0,
        )

        result = execute_jira_command(["issue", "list"])

        assert result.exit_code == 0
        assert result.stdout == "success"
        assert result.stderr == ""
        mock_subprocess_run.assert_called_once()

    def test_failed_command(self, mock_subprocess_run: MagicMock) -> None:
        """Test executing a failed jira command."""
        mock_subprocess_run.return_value = MagicMock(
            stdout="",
            stderr="error message",
            returncode=1,
        )

        result = execute_jira_command(["issue", "view", "INVALID-123"])

        assert result.exit_code == 1
        assert result.stderr == "error message"

    def test_command_with_stdin_input(
        self, mock_subprocess_run: MagicMock
    ) -> None:
        """Test executing command with stdin input."""
        mock_subprocess_run.return_value = MagicMock(
            stdout="created",
            stderr="",
            returncode=0,
        )

        result = execute_jira_command(
            ["issue", "comment", "add", "TEST-123"],
            stdin_input="This is a comment",
        )

        assert result.exit_code == 0
        # Verify stdin_input was passed.
        call_kwargs = mock_subprocess_run.call_args[1]
        assert call_kwargs["input"] == "This is a comment"

    def test_command_not_found(self, mock_subprocess_run: MagicMock) -> None:
        """Test handling when jira-cli is not found."""
        mock_subprocess_run.side_effect = FileNotFoundError()

        with pytest.raises(FileNotFoundError) as exc_info:
            execute_jira_command(["issue", "list"])

        assert "jira-cli not found" in str(exc_info.value)

    def test_command_timeout(self, mock_subprocess_run: MagicMock) -> None:
        """Test that commands have a timeout set."""
        mock_subprocess_run.return_value = MagicMock(
            stdout="ok",
            stderr="",
            returncode=0,
        )

        execute_jira_command(["issue", "list"])

        # Verify timeout was passed.
        call_kwargs = mock_subprocess_run.call_args[1]
        assert call_kwargs["timeout"] == 20

    def test_command_uses_environment(
        self, mock_subprocess_run: MagicMock
    ) -> None:
        """Test that command uses current environment."""
        mock_subprocess_run.return_value = MagicMock(
            stdout="ok",
            stderr="",
            returncode=0,
        )

        with patch.dict("os.environ", {"JIRA_API_TOKEN": "test-token"}):
            execute_jira_command(["issue", "list"])

        # Verify env was passed.
        call_kwargs = mock_subprocess_run.call_args[1]
        assert "env" in call_kwargs


class TestExecuteJiraCommandJson:
    """Tests for execute_jira_command_json function."""

    def test_successful_json_command(
        self, mock_subprocess_run: MagicMock
    ) -> None:
        """Test executing a command that returns valid JSON."""
        json_response = {"key": "TEST-123", "summary": "Test ticket"}
        mock_subprocess_run.return_value = MagicMock(
            stdout=json.dumps(json_response),
            stderr="",
            returncode=0,
        )

        result = execute_jira_command_json(["issue", "view", "TEST-123"])

        assert result == json_response
        assert result["key"] == "TEST-123"

    def test_failed_command_raises_error(
        self, mock_subprocess_run: MagicMock
    ) -> None:
        """Test that failed command raises ValueError."""
        mock_subprocess_run.return_value = MagicMock(
            stdout="",
            stderr="error: ticket not found",
            returncode=1,
        )

        with pytest.raises(ValueError) as exc_info:
            execute_jira_command_json(["issue", "view", "INVALID-123"])

        assert "jira command failed" in str(exc_info.value)

    def test_invalid_json_raises_error(
        self, mock_subprocess_run: MagicMock
    ) -> None:
        """Test that invalid JSON raises ValueError."""
        mock_subprocess_run.return_value = MagicMock(
            stdout="not valid json",
            stderr="",
            returncode=0,
        )

        with pytest.raises(ValueError) as exc_info:
            execute_jira_command_json(["issue", "view", "TEST-123"])

        assert "Failed to parse jira output as JSON" in str(exc_info.value)

    def test_empty_json_response(self, mock_subprocess_run: MagicMock) -> None:
        """Test handling empty JSON object."""
        mock_subprocess_run.return_value = MagicMock(
            stdout="{}",
            stderr="",
            returncode=0,
        )

        result = execute_jira_command_json(["issue", "list"])

        assert result == {}

    def test_json_array_response(self, mock_subprocess_run: MagicMock) -> None:
        """Test handling JSON array response."""
        json_array = [{"key": "TEST-1"}, {"key": "TEST-2"}]
        mock_subprocess_run.return_value = MagicMock(
            stdout=json.dumps(json_array),
            stderr="",
            returncode=0,
        )

        result = execute_jira_command_json(["issue", "list"])

        assert result == json_array
        assert len(result) == 2
