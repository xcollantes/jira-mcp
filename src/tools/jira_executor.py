"""Jira CLI executor utility for running jira-cli commands."""

import json
import logging
import os
import subprocess
from typing import Any

from pydantic import BaseModel, Field

logger: logging.Logger = logging.getLogger(__name__)


class CommandResult(BaseModel):
    """Result of a jira-cli command execution."""

    stdout: str = Field(description="The stdout of the jira-cli command.")
    stderr: str = Field(description="The stderr of the jira-cli command.")
    exit_code: int = Field(description="The exit code of the jira-cli command.")


def get_jira_cli_path() -> str:
    """Get the path to the jira-cli executable."""
    return os.getenv("JIRA_CLI_PATH", "jira")


def execute_jira_command(
    args: list[str], stdin_input: str | None = None
) -> CommandResult:
    """Execute a jira-cli command and return the result.

    Args:
        args: Command arguments to pass to jira-cli.
        stdin_input: Optional input to pass to stdin.

    Returns:
        CommandResult with stdout, stderr, and exit_code.

    Raises:
        JiraCliError: If jira-cli is not found.
    """
    jira_path: str = get_jira_cli_path()
    command: str = [jira_path] + args

    logger.debug("Running jira command: %s", " ".join(command))

    try:
        process: subprocess.CompletedProcess[str] = subprocess.run(
            command,
            capture_output=True,
            text=True,
            input=stdin_input,
            timeout=20,  # In seconds.
            env=os.environ,  # Needed for the JIRA_API_KEY environment variable to be set.
        )

        result: CommandResult = CommandResult(
            stdout=process.stdout,
            stderr=process.stderr,
            exit_code=process.returncode,
        )

        logger.debug("Command result: exit_code=%d", result.exit_code)

        return result

    except FileNotFoundError:
        raise FileNotFoundError(
            f"jira-cli not found at path: {jira_path}. "
            "Please install jira-cli or set JIRA_CLI_PATH environment variable.",
        )


def execute_jira_command_json(args: list[str]) -> Any:
    """Execute a jira-cli command and parse JSON output.

    Args:
        args: Command arguments to pass to jira-cli.

    Returns:
        Parsed JSON response.

    Raises:
        JiraCliError: If command fails.
        ValueError: If JSON parsing fails.
    """
    result: CommandResult = execute_jira_command(args)

    if result.exit_code != 0:
        raise ValueError(f"jira command failed: {result.stderr}")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse jira output as JSON: {result.stdout}"
        ) from e
