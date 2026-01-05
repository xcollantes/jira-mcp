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


def format_alert(feature: dict[str, Any]) -> str:
    props = feature["properties"]
    return textwrap.dedent(
        f"""
    Event: {props.get("event", "Unknown")}
    Area: {props.get("areaDesc", "Unknown")}
    Severity: {props.get("severity", "Unknown")}
    Description: {props.get("description", "No description available")}
    Instructions: {props.get("instruction", "No specific instructions provided")}
    """
    )


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


def example_tool_cli() -> dict[str, Any]:
    """Example tool to demonstrate how to use the tool helper functions in the
    CLI.

    Some actual ability may exist in the command line. This example shows how to
    call some CLI program and return the output to the LLM.
    """

    command: list[str] = ["ls", "-l"]

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


def get_weather(location: str, api_key: str, weather_api_base: str) -> dict[str, Any]:
    """Get weather forecast data for a location."""

    response: httpx.Response = httpx.get(
        f"{weather_api_base}/points/{location}/forecast",
        params={"apikey": api_key},
    )
    response.raise_for_status()
    return response.json()


def get_alerts(state: str, api_key: str, weather_api_base: str) -> dict[str, Any]:
    """Get active weather alerts for a U.S. state."""

    response: httpx.Response = httpx.get(
        f"{weather_api_base}/alerts/active/area/{state}",
        params={"apikey": api_key},
    )
    response.raise_for_status()
    return response.json()


async def get_forecast(
    latitude: float,
    longitude: float,
    user_agent: str,
    weather_api_base: str,
) -> dict[str, Any]:
    """Get detailed weather forecast for a specific location."""

    # First get the forecast grid endpoint.
    points_url: str = f"{weather_api_base}/points/{latitude},{longitude}"
    points_data: dict[str, Any] = await _make_request(points_url, user_agent)

    if not points_data:
        raise ValueError("Unable to fetch forecast data for this location.")

    # Get the forecast URL from the points response.
    forecast_url: str = points_data["properties"]["forecast"]

    logger.debug("Forecast URL: %s", forecast_url)

    forecast_data: dict[str, Any] = await _make_request(forecast_url, user_agent)

    if not forecast_data:
        raise ValueError("Unable to fetch detailed forecast.")

    return forecast_data
