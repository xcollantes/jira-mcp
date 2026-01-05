"""Main entry point for the MCP server.

Point your LLM client to this file to use the MCP server.
"""

import argparse
import logging
import os
import sys
import textwrap
from typing import Annotated, Any

import dotenv
import httpx
from mcp.server.fastmcp import FastMCP

from src.tools.tool_utils import format_alert, get_alerts, get_forecast, get_weather

dotenv.load_dotenv()

logger: logging.Logger = logging.getLogger(__name__)


# Create the MCP server instance.
mcp: FastMCP = FastMCP("Jira MCP")


def setup_logging(debug: bool = False) -> None:
    """Configure logging for the MCP server."""
    level: int = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s]%(filename)s:%(levelname)s: %(message)s",
        # Use stderr to avoid corrupting stdout (used for MCP protocol).
        # https://modelcontextprotocol.io/docs/develop/build-server#logging-in-mcp-servers
        stream=sys.stderr,
    )


@mcp.tool(
    name="get_weather",
    title="Get weather forecast data for a location.",
    description="Retrieves weather forecast information from the National Weather Service API for the specified location. The location should be in the format of latitude,longitude (e.g., '47.7623,-122.2054').",
)
def get_weather_tool(
    location: Annotated[
        str,
        "Location coordinates in 'latitude,longitude' format, for example '47.7623,-122.2054'.",
    ],
) -> dict[str, Any]:
    """Get weather forecast data for a location."""

    try:
        return get_weather(location, WEATHER_API_KEY, WEATHER_API_BASE)

    except httpx.HTTPStatusError as e:
        logger.error(
            "Failed to get weather forecast data for location: %s: %s", location, e
        )
        raise e


@mcp.tool(
    name="get_alerts",
    title="Get active weather alerts for a U.S. state.",
    description="Retrieves all currently active weather alerts, warnings, and advisories issued by the National Weather Service for the specified state. This includes severe weather warnings, flood advisories, winter weather alerts, and more.",
)
async def get_alerts_tool(
    state: Annotated[str, "Two-letter U.S. state code, for example 'WA' or 'CA'."],
) -> str:
    """Get active weather alerts for a U.S. state."""

    try:
        return "\n".join(
            [
                format_alert(feature)
                for feature in get_alerts(state, WEATHER_API_KEY, WEATHER_API_BASE)[
                    "features"
                ]
            ]
        )

    except httpx.HTTPStatusError as e:
        logger.error("Failed to get active weather alerts for state: %s: %s", state, e)
        raise e


@mcp.tool(
    name="get_forecast",
    title="Get detailed weather forecast for a specific location.",
    description="Retrieves a multi-period weather forecast from the National Weather Service for the specified coordinates. The forecast includes temperature, wind conditions, and detailed descriptions for the next 5 forecast periods (typically covering the next 2-3 days).",
)
async def get_forecast_tool(
    latitude: Annotated[float, "Latitude in decimal degrees, for example 47.7623."],
    longitude: Annotated[float, "Longitude in decimal degrees, for example -122.2054."],
) -> str:
    """Get detailed weather forecast for a specific location."""

    try:
        forecast_data: dict[str, Any] = await get_forecast(
            latitude, longitude, USER_AGENT, WEATHER_API_BASE
        )

        # Format the periods into a readable forecast.
        periods: list[dict[str, Any]] = forecast_data.get("properties", {}).get(
            "periods", []
        )
        forecasts: list[str] = []
        for period in periods[:5]:  # Only show next 5 periods.
            forecast: str = textwrap.dedent(
                f"""
            {period["name"]}:
            Temperature: {period["temperature"]}°{period["temperatureUnit"]}
            Wind: {period["windSpeed"]} {period["windDirection"]}
            Forecast: {period["detailedForecast"]}
            """
            )
            forecasts.append(forecast)

        logger.debug("Forecast data: %s", forecasts)
        return "\n".join(forecasts)

    except httpx.HTTPStatusError as e:
        logger.error(
            "Failed to get detailed weather forecast for location: %s: %s",
            latitude,
            longitude,
            e,
        )
        raise e


def main() -> None:
    """Main entry point for the MCP server."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="MCP Weather Server: Provides weather tools for LLM clients."
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")

    args: argparse.Namespace = parser.parse_args()

    setup_logging(args.debug)

    logger.info("Starting MCP Weather server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
