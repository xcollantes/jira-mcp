"""Jira MCP: Example tool helper functions.

Example tool definition in main.py:

```python
@mcp.tool(
    name="todo_example_tool",
    title="A tool to complete a task.",
    description="A tool to complete a task.",
)
def todo_example_tool(task: Annotated[str, "A task to complete."]) -> str:

    # Perform some action.

    return "Task completed successfully."
```
"""

import logging
import subprocess
import textwrap
from typing import Any

import httpx


logger: logging.Logger = logging.getLogger(__name__)


async def _make_request(url: str, user_agent: str) -> Any:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                headers={
                    "User-Agent": user_agent,
                    "Accept": "application/geo+json",
                },
                timeout=10,
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error("HTTP error occurred: %s", e)
            raise e


def jira_issue_list() -> dict[str, Any]:
    """List all issues in Jira."""

    command: list[str] = ["jira", "issue", "list"]

    logger.debug("Running command: %s", command)
    process_output: subprocess.CompletedProcess[str] = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    logger.debug("Command output: %s", process_output)

    if process_output.returncode != 0:
        raise ValueError(f"Error in running command: {process_output.stderr}")

    return process_output.stdout
