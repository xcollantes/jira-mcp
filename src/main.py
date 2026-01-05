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
from mcp.server.fastmcp import FastMCP

from src.tools.tool_utils import jira_issue_list

dotenv.load_dotenv()

JIRA_API_KEY: str = os.getenv("JIRA_API_KEY")
JIRA_AUTH_TYPE: str = os.getenv("JIRA_AUTH_TYPE")

if not JIRA_API_KEY or not JIRA_AUTH_TYPE:
    raise ValueError(
        "JIRA_API_KEY and JIRA_AUTH_TYPE must be set. See README.md for instructions to setup your Jira API key and authentication type."
    )

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
    name="jira_issue_list",
    title="List all issues in Jira.",
    description="Lists all issues in Jira.",
)
def jira_issue_list_tool() -> dict[str, Any]:
    """List all issues in Jira."""

    try:
        return jira_issue_list()
    except ValueError as e:
        logger.error("Error in listing issues in Jira: %s", e)
        raise e

@mcp.tool(


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
