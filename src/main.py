"""Main entry point for the Jira MCP server.

Point your LLM client to this file to use the MCP server.
"""

import argparse
import logging
import os
import sys
import textwrap
from typing import Annotated

import dotenv
from mcp.server.fastmcp import FastMCP

from src.tools.tool_utils import (
    JiraTicket,
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

dotenv.load_dotenv()


if not os.getenv("JIRA_API_TOKEN") or not os.getenv("JIRA_AUTH_TYPE"):
    raise ValueError(
        "JIRA_API_TOKEN and JIRA_AUTH_TYPE must be set for `jira-cli`, the dependent tool this MCP server uses. See README.md for instructions to setup your Jira API key and authentication type."
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
    name="list_tickets",
    title="Search and list Jira tickets with filters.",
    description="List Jira tickets with optional filters. Supports JQL queries, semantic filters (assigned to me, unassigned, by status, by project), date filters (created/updated recently), and sorting options.",
)
def list_tickets_tool(
    jql: Annotated[
        str | None,
        "Raw JQL query (advanced users only). Overrides other filters if provided.",
    ] = None,
    limit: Annotated[int, "Maximum number of tickets to return (default 20)."] = 20,
    assigned_to_me: Annotated[bool | None, "Show only tickets assigned to me."] = None,
    unassigned: Annotated[bool | None, "Show only unassigned tickets."] = None,
    status: Annotated[
        str | None,
        "Filter by status. Common values: Open, In Progress, Done, Closed. Your Jira may have custom statuses.",
    ] = None,
    project: Annotated[str | None, "Filter by project key (e.g., 'PROJ')."] = None,
    created_recently: Annotated[
        bool | None, "Show tickets created in the last 7 days."
    ] = None,
    updated_recently: Annotated[
        bool | None, "Show tickets updated in the last 7 days."
    ] = None,
    order_by: Annotated[
        str | None, "Sort tickets by field (created, updated, priority)."
    ] = None,
    order_direction: Annotated[str | None, "Sort direction (asc, desc)."] = None,
) -> str:
    """Search and list Jira tickets with filters."""
    try:
        tickets: list[JiraTicket] = list_tickets(
            jql=jql,
            limit=limit,
            assigned_to_me=assigned_to_me,
            unassigned=unassigned,
            status=status,
            project=project,
            created_recently=created_recently,
            updated_recently=updated_recently,
            order_by=order_by,
            order_direction=order_direction,
        )

        if not tickets:
            return "No tickets found."

        ticket_list: list[str] = []
        for t in tickets:
            assignee_str = f" | Assignee: {t.assignee}" if t.assignee else ""
            ticket_list.append(
                f"{t.key}: {t.summary}\n  Status: {t.status} | Priority: {t.priority} | Type: {t.type}{assignee_str}"
            )

        return "\n\n".join(ticket_list)

    except Exception as e:
        logger.error("Error listing tickets: %s", e)
        return f"Error listing tickets: {e}"


@mcp.tool(
    name="get_ticket",
    title="Get detailed information about a specific Jira ticket.",
    description="Retrieve detailed information about a Jira ticket including summary, status, priority, type, assignee, reporter, dates, description, and comments.",
)
def get_ticket_tool(
    ticket_key: Annotated[str, "Jira ticket key (e.g., PROJ-123)."],
    comments: Annotated[int, "Number of comments to include (default 5)."] = 5,
) -> str:
    """Get detailed information about a specific Jira ticket."""
    try:
        ticket = get_ticket(ticket_key, comments)

        comments_text = "No comments"
        if ticket.comments:
            comments_text = "\n\n".join(
                f"- **{c.author}** ({c.created}):\n  {c.body}" for c in ticket.comments
            )

        return textwrap.dedent(
            f"""**{ticket.key}: {ticket.summary}**

            **Details:**
            - Status: {ticket.status}
            - Priority: {ticket.priority}
            - Type: {ticket.type}
            - Assignee: {ticket.assignee or "Unassigned"}
            - Reporter: {ticket.reporter or "Unknown"}
            - Created: {ticket.created}
            - Updated: {ticket.updated}

            **Description:**
            {ticket.description or "No description provided"}

            **Comments ({len(ticket.comments)}):**
            {comments_text}"""
        )

    except Exception as e:
        logger.error("Error getting ticket %s: %s", ticket_key, e)
        return f"Error getting ticket {ticket_key}: {e}"


@mcp.tool(
    name="create_ticket",
    title="Create a new Jira ticket.",
    description="Create a new Jira ticket with project, type, summary, and optional description, priority, assignee, labels, and components.",
)
def create_ticket_tool(
    project: Annotated[str, "Jira project key (e.g., PROJ)."],
    issue_type: Annotated[str, "Issue type (e.g., Bug, Story, Task)."],
    summary: Annotated[str, "Issue summary/title."],
    description: Annotated[
        str | None, "Issue description (markdown supported)."
    ] = None,
    priority: Annotated[str | None, "Priority level (e.g., High, Medium, Low)."] = None,
    assignee: Annotated[str | None, "Assignee username or email."] = None,
    labels: Annotated[list[str] | None, "List of labels to add."] = None,
    components: Annotated[list[str] | None, "List of components to add."] = None,
) -> str:
    """Create a new Jira ticket."""
    try:
        result = create_ticket(
            project=project,
            issue_type=issue_type,
            summary=summary,
            description=description,
            priority=priority,
            assignee=assignee,
            labels=labels,
            components=components,
        )

        if not result.success:
            return f"Failed to create ticket: {result.error}"

        return (
            f"Successfully created ticket {result.ticket_key}\nURL: {result.ticket_url}"
        )

    except Exception as e:
        logger.error("Error creating ticket: %s", e)
        return f"Error creating ticket: {e}"


@mcp.tool(
    name="move_ticket",
    title="Move a Jira ticket to a different status.",
    description="Move a Jira ticket to a different status. The available statuses depend on your Jira project's workflow configuration.",
)
def move_ticket_tool(
    ticket_key: Annotated[str, "Jira ticket key (e.g., PROJ-123)."],
    status: Annotated[
        str,
        "Target status. Common values: Open, In Progress, Done, Closed. Your Jira may have custom statuses.",
    ],
) -> str:
    """Move a Jira ticket to a different status."""
    try:
        result = move_ticket(ticket_key, status)
        return result.message

    except Exception as e:
        logger.error("Error moving ticket %s: %s", ticket_key, e)
        return f"Error moving ticket {ticket_key}: {e}"


@mcp.tool(
    name="add_comment",
    title="Add a comment to a Jira ticket.",
    description="Add a comment to an existing Jira ticket. The comment text supports multi-line content.",
)
def add_comment_tool(
    ticket_key: Annotated[str, "Jira ticket key (e.g., PROJ-123)."],
    comment: Annotated[str, "Comment text to add to the ticket."],
) -> str:
    """Add a comment to a Jira ticket."""
    try:
        result = add_comment(ticket_key, comment)
        return result.message

    except Exception as e:
        logger.error("Error adding comment to %s: %s", ticket_key, e)
        return f"Error adding comment to {ticket_key}: {e}"


@mcp.tool(
    name="assign_to_me",
    title="Assign a Jira ticket to the current user.",
    description="Assign a Jira ticket to yourself (the currently authenticated user).",
)
def assign_to_me_tool(
    ticket_key: Annotated[str, "Jira ticket key (e.g., PROJ-123)."],
) -> str:
    """Assign a Jira ticket to the current user."""
    try:
        result = assign_to_me(ticket_key)
        return result.message

    except Exception as e:
        logger.error("Error assigning ticket %s: %s", ticket_key, e)
        return f"Error assigning ticket {ticket_key}: {e}"


@mcp.tool(
    name="open_ticket_in_browser",
    title="Open a Jira ticket in the default web browser.",
    description="Open a Jira ticket in your default web browser for viewing in the Jira web interface.",
)
def open_ticket_in_browser_tool(
    ticket_key: Annotated[str, "Jira ticket key (e.g., PROJ-123)."],
) -> str:
    """Open a Jira ticket in the default web browser."""
    try:
        return open_ticket_in_browser(ticket_key)

    except Exception as e:
        logger.error("Error opening ticket %s in browser: %s", ticket_key, e)
        return f"Error opening ticket {ticket_key} in browser: {e}"


@mcp.tool(
    name="update_ticket_description",
    title="Update the description of a Jira ticket.",
    description="Update the description of an existing Jira ticket. The description supports multi-line content and markdown formatting.",
)
def update_ticket_description_tool(
    ticket_key: Annotated[str, "Jira ticket key (e.g., PROJ-123)."],
    description: Annotated[str, "New description content for the ticket."],
) -> str:
    """Update the description of a Jira ticket."""
    try:
        result = update_ticket_description(ticket_key, description)
        return result.message

    except Exception as e:
        logger.error("Error updating description for %s: %s", ticket_key, e)
        return f"Error updating description for {ticket_key}: {e}"


@mcp.tool(
    name="list_sprints",
    title="List sprints from a Jira board.",
    description="List all sprints from a Jira board. Can filter by sprint state (active, future, closed).",
)
def list_sprints_tool(
    board_id: Annotated[int, "Jira board ID to list sprints from."],
    state: Annotated[
        str | None,
        "Filter sprints by state (active, future, closed).",
    ] = None,
    limit: Annotated[int, "Maximum number of sprints to return (default 20)."] = 20,
) -> str:
    """List sprints from a Jira board."""
    try:
        result = list_sprints(board_id=board_id, state=state, limit=limit)

        if not result.sprints:
            return "No sprints found."

        sprint_list: list[str] = []
        for s in result.sprints:
            date_info = ""
            if s.start_date:
                date_info += f" | Start: {s.start_date}"
            if s.end_date:
                date_info += f" | End: {s.end_date}"
            sprint_list.append(
                f"Sprint {s.id}: {s.name}\n  State: {s.state}{date_info}"
            )

        return "\n\n".join(sprint_list)

    except Exception as e:
        logger.error("Error listing sprints for board %d: %s", board_id, e)
        return f"Error listing sprints: {e}"


@mcp.tool(
    name="add_to_sprint",
    title="Add a Jira ticket to a sprint.",
    description="Add a Jira ticket to a specific sprint by sprint ID. Use list_sprints to find available sprint IDs.",
)
def add_to_sprint_tool(
    ticket_key: Annotated[str, "Jira ticket key (e.g., PROJ-123)."],
    sprint_id: Annotated[int, "Sprint ID to add the ticket to."],
) -> str:
    """Add a Jira ticket to a sprint."""
    try:
        result = add_to_sprint(ticket_key, sprint_id)
        return result.message

    except Exception as e:
        logger.error("Error adding %s to sprint %d: %s", ticket_key, sprint_id, e)
        return f"Error adding {ticket_key} to sprint: {e}"


@mcp.tool(
    name="remove_from_sprint",
    title="Remove a Jira ticket from its current sprint.",
    description="Remove a Jira ticket from its current sprint. The ticket will be moved to the backlog.",
)
def remove_from_sprint_tool(
    ticket_key: Annotated[str, "Jira ticket key (e.g., PROJ-123)."],
) -> str:
    """Remove a Jira ticket from its current sprint."""
    try:
        result = remove_from_sprint(ticket_key)
        return result.message

    except Exception as e:
        logger.error("Error removing %s from sprint: %s", ticket_key, e)
        return f"Error removing {ticket_key} from sprint: {e}"


@mcp.tool(
    name="edit_ticket",
    title="Edit fields on a Jira ticket.",
    description="Edit various fields on a Jira ticket including summary, priority, assignee, labels, components, fix versions, parent, and custom fields.",
)
def edit_ticket_tool(
    ticket_key: Annotated[str, "Jira ticket key (e.g., PROJ-123)."],
    summary: Annotated[str | None, "New summary/title for the ticket."] = None,
    priority: Annotated[
        str | None, "New priority level (e.g., High, Medium, Low)."
    ] = None,
    assignee: Annotated[
        str | None,
        "New assignee username or email (use empty string to unassign).",
    ] = None,
    labels: Annotated[
        list[str] | None, "Labels to set on the ticket (replaces existing labels)."
    ] = None,
    add_labels: Annotated[list[str] | None, "Labels to add to the ticket."] = None,
    remove_labels: Annotated[
        list[str] | None, "Labels to remove from the ticket."
    ] = None,
    components: Annotated[list[str] | None, "Components to set on the ticket."] = None,
    fix_versions: Annotated[
        list[str] | None, "Fix versions to set on the ticket."
    ] = None,
    parent: Annotated[
        str | None, "Parent issue key (for subtasks/child issues)."
    ] = None,
    custom_fields: Annotated[
        dict[str, str] | None, "Custom fields to set (key-value pairs)."
    ] = None,
) -> str:
    """Edit fields on a Jira ticket."""
    try:
        result = edit_ticket(
            ticket_key=ticket_key,
            summary=summary,
            priority=priority,
            assignee=assignee,
            labels=labels,
            add_labels=add_labels,
            remove_labels=remove_labels,
            components=components,
            fix_versions=fix_versions,
            parent=parent,
            custom_fields=custom_fields,
        )
        return result.message

    except Exception as e:
        logger.error("Error editing ticket %s: %s", ticket_key, e)
        return f"Error editing ticket {ticket_key}: {e}"


def main() -> None:
    """Main entry point for the MCP server."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Jira MCP Server: Provides Jira tools for LLM clients via jira-cli."
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")

    args: argparse.Namespace = parser.parse_args()

    setup_logging(args.debug)
    logger.debug("Logging is DEBUG: %s", args.debug)

    logger.info("Starting Jira MCP server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
