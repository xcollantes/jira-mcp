"""Jira MCP tool helper functions.

All tool implementations for interacting with Jira via jira-cli.
"""

import json
import logging
from typing import Any

from src.models.jira_actions import (
    AddCommentResult,
    AddToSprintResult,
    AssignToMeResult,
    CreateTicketResult,
    EditTicketResult,
    ListSprintsResult,
    MoveTicketResult,
    RemoveFromSprintResult,
    Sprint,
    UpdateDescriptionResult,
)
from src.models.jira_tickets import (
    AdfDocument,
    JiraComment,
    JiraTicket,
    JiraTicketDetail,
    normalize_status,
)
from src.tools.jira_executor import CommandResult, execute_jira_command

logger: logging.Logger = logging.getLogger(__name__)


def _build_jql_from_params(
    jql: str | None = None,
    assigned_to_me: bool | None = None,
    unassigned: bool | None = None,
    status: str | None = None,
    project: str | None = None,
    created_recently: bool | None = None,
    updated_recently: bool | None = None,
) -> str | None:
    """Build JQL query from semantic parameters.

    Args:
        jql: Raw JQL query (overrides other params if provided).
        assigned_to_me: Filter to tickets assigned to current user.
        unassigned: Filter to unassigned tickets.
        status: Filter by status.
        project: Filter by project key.
        created_recently: Filter to tickets created in last 7 days.
        updated_recently: Filter to tickets updated in last 7 days.

    Returns:
        JQL query string or None if no filters.
    """
    if jql:
        return jql

    conditions: list[str] = []

    # Assignee filters.
    if assigned_to_me:
        conditions.append("assignee = currentUser()")
    elif unassigned:
        conditions.append("assignee is EMPTY")

    # Status filter - normalize common statuses, but accept any string.
    if status:
        jira_status = normalize_status(status)
        conditions.append(f'status = "{jira_status}"')

    # Project filter.
    if project:
        conditions.append(f"project = {project}")

    # Date filters.
    if created_recently:
        conditions.append("created >= -7d")
    if updated_recently:
        conditions.append("updated >= -7d")

    return " AND ".join(conditions) if conditions else None


def list_tickets(
    jql: str | None = None,
    limit: int = 20,
    assigned_to_me: bool | None = None,
    unassigned: bool | None = None,
    status: str | None = None,
    project: str | None = None,
    created_recently: bool | None = None,
    updated_recently: bool | None = None,
    order_by: str | None = None,
    order_direction: str | None = None,
) -> list[JiraTicket]:
    """List Jira tickets with optional filters.

    Args:
        jql: Raw JQL query (advanced users only).
        limit: Maximum number of tickets to return.
        assigned_to_me: Show only tickets assigned to me.
        unassigned: Show only unassigned tickets.
        status: Filter by status.
        project: Filter by project key (e.g., 'PROJ').
        created_recently: Show tickets created in the last 7 days.
        updated_recently: Show tickets updated in the last 7 days.
        order_by: Sort tickets by field (created, updated, priority).
        order_direction: Sort direction (asc, desc).

    Returns:
        List of JiraTicket objects.
    """
    built_jql = _build_jql_from_params(
        jql=jql,
        assigned_to_me=assigned_to_me,
        unassigned=unassigned,
        status=status,
        project=project,
        created_recently=created_recently,
        updated_recently=updated_recently,
    )

    args = [
        "issue",
        "list",
        "--no-headers",
        "--plain",
        "--columns",
        "key,summary,status,priority,type,assignee",
    ]

    if built_jql:
        args.extend(["--jql", built_jql])

    # Add ordering using jira-cli flags.
    if order_by:
        args.extend(["--order-by", order_by])
        if order_direction == "asc":
            args.append("--reverse")

    if limit > 0:
        args.extend(["--paginate", f"0:{limit}"])

    result: CommandResult = execute_jira_command(args)

    if result.exit_code != 0:
        # Check if it's just "No result found" which is not an error.
        if "No result found" in result.stderr:
            return []
        raise ValueError(f"Failed to list tickets: {result.stderr}")

    # Parse the plain text output.
    lines = [line for line in result.stdout.strip().split("\n") if line.strip()]

    tickets: list[JiraTicket] = []
    for line in lines:
        # jira-cli output is tab-separated in plain mode.
        columns = [col.strip() for col in line.split("\t") if col.strip()]

        if len(columns) >= 5:
            tickets.append(
                JiraTicket(
                    key=columns[0],
                    summary=columns[1],
                    status=columns[2],
                    priority=columns[3],
                    type=columns[4],
                    assignee=columns[5] if len(columns) > 5 else None,
                )
            )

    return tickets


def _convert_adf_to_text(adf: AdfDocument) -> str:
    """Convert Atlassian Document Format to plain text.

    Args:
        adf: ADF document as a dictionary.

    Returns:
        Plain text representation.
    """
    parts: list[str] = []

    def process_inline_content(nodes: list[dict[str, Any]]) -> str:
        result: list[str] = []
        for node in nodes:
            if node.get("type") == "text":
                text = node.get("text", "")
                marks = node.get("marks", [])
                for mark in marks:
                    mark_type = mark.get("type")
                    if mark_type == "strong":
                        text = f"**{text}**"
                    elif mark_type == "em":
                        text = f"*{text}*"
                    elif mark_type == "code":
                        text = f"`{text}`"
                    elif mark_type == "strike":
                        text = f"~~{text}~~"
                result.append(text)
            elif node.get("type") == "hardBreak":
                result.append("\n")
        return "".join(result)

    content = adf.get("content", [])
    for block in content:
        block_type = block.get("type")

        if block_type == "paragraph":
            block_content = block.get("content", [])
            if block_content:
                text = process_inline_content(block_content)
                if text:
                    parts.append(text)

        elif block_type == "heading":
            level = block.get("attrs", {}).get("level", 1)
            block_content = block.get("content", [])
            if block_content:
                prefix = "#" * level
                text = process_inline_content(block_content)
                if text:
                    parts.append(f"{prefix} {text}")

        elif block_type == "bulletList":
            list_items: list[str] = []
            for item in block.get("content", []):
                item_parts: list[str] = []
                for p in item.get("content", []):
                    if p.get("type") == "paragraph" and p.get("content"):
                        item_parts.append(process_inline_content(p["content"]))
                if item_parts:
                    list_items.append(f"- {' '.join(item_parts)}")
            if list_items:
                parts.append("\n".join(list_items))

        elif block_type == "orderedList":
            start_num = block.get("attrs", {}).get("start", 1)
            list_items = []
            for idx, item in enumerate(block.get("content", [])):
                item_parts = []
                for p in item.get("content", []):
                    if p.get("type") == "paragraph" and p.get("content"):
                        item_parts.append(process_inline_content(p["content"]))
                if item_parts:
                    list_items.append(
                        f"{start_num + idx}. {' '.join(item_parts)}"
                    )
            if list_items:
                parts.append("\n".join(list_items))

        elif block_type == "codeBlock":
            lang = block.get("attrs", {}).get("language", "")
            code_parts: list[str] = []
            for text_node in block.get("content", []):
                code_parts.append(text_node.get("text", ""))
            code = "".join(code_parts)
            parts.append(f"```{lang}\n{code}\n```")

        elif block_type == "rule":
            parts.append("---")

        elif block_type == "blockquote":
            quoted_lines: list[str] = []
            for p in block.get("content", []):
                if p.get("type") == "paragraph" and p.get("content"):
                    quoted_lines.append(
                        f"> {process_inline_content(p['content'])}"
                    )
            if quoted_lines:
                parts.append("\n".join(quoted_lines))

    return "\n\n".join(parts)


def get_ticket(ticket_key: str, comments: int = 5) -> JiraTicketDetail:
    """Get detailed information about a Jira ticket.

    Args:
        ticket_key: Jira ticket key (e.g., PROJ-123).
        comments: Number of comments to include.

    Returns:
        JiraTicketDetail with full ticket information.
    """
    args = ["issue", "view", ticket_key, "--raw"]

    if comments > 0:
        args.extend(["--comments", str(comments)])

    result: CommandResult = execute_jira_command(args)

    if result.exit_code != 0:
        raise ValueError(f"Failed to get ticket {ticket_key}: {result.stderr}")

    try:
        raw_data: dict[str, Any] = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse jira response: {result.stdout}"
        ) from e
    except Exception:
        raise ValueError(f"Failed to get ticket {ticket_key}: {result.stdout}")

    fields: dict[str, Any] = raw_data.get("fields", {})

    # Extract description text from ADF format.
    description_text: str = ""
    description = fields.get("description")
    if description and isinstance(description, dict):
        description_text = _convert_adf_to_text(description)

    # Extract comments.
    comment_data = fields.get("comment", {}).get("comments", [])
    ticket_comments: list[JiraComment] = []
    for c in comment_data:
        # Convert comment body from ADF format if needed.
        comment_body = c.get("body", "")
        if isinstance(comment_body, dict):
            comment_body = _convert_adf_to_text(comment_body)
        elif not isinstance(comment_body, str):
            comment_body = str(comment_body)

        ticket_comments.append(
            JiraComment(
                author=c.get("author", {}).get("displayName", "Unknown"),
                created=c.get("created", ""),
                body=comment_body,
            )
        )

    return JiraTicketDetail(
        key=raw_data.get("key", ""),
        summary=fields.get("summary", ""),
        status=fields.get("status", {}).get("name", ""),
        priority=fields.get("priority", {}).get("name", ""),
        type=fields.get("issuetype", {}).get("name", ""),
        assignee=(
            fields.get("assignee", {}).get("displayName")
            if fields.get("assignee")
            else None
        ),
        reporter=(
            fields.get("reporter", {}).get("displayName")
            if fields.get("reporter")
            else None
        ),
        created=fields.get("created", ""),
        updated=fields.get("updated", ""),
        description=description_text,
        comments=ticket_comments,
    )


def create_ticket(
    project: str,
    issue_type: str,
    summary: str,
    description: str | None = None,
    priority: str | None = None,
    assignee: str | None = None,
    labels: list[str] | None = None,
    components: list[str] | None = None,
) -> CreateTicketResult:
    """Create a new Jira ticket.

    Args:
        project: Jira project key (e.g., PROJ).
        issue_type: Issue type (e.g., Bug, Story, Task).
        summary: Issue summary/title.
        description: Issue description (markdown supported).
        priority: Priority level (e.g., High, Medium, Low).
        assignee: Assignee username or email.
        labels: List of labels to add.
        components: List of components to add.

    Returns:
        CreateTicketResult with success status and ticket info.
    """
    args: list[str] = [
        "issue",
        "create",
        "--project",
        project,
        "--type",
        issue_type,
        "--summary",
        summary,
        "--no-input",
        "--raw",
    ]

    if priority:
        args.extend(["--priority", priority])

    if assignee:
        args.extend(["--assignee", assignee])

    if labels:
        for label in labels:
            args.extend(["--label", label])

    if components:
        for component in components:
            args.extend(["--component", component])

    # If description is provided, use stdin with template flag.
    stdin_input: str | None = None
    if description:
        args.extend(["--template", "-"])
        stdin_input = description

    try:
        result: CommandResult = execute_jira_command(
            args, stdin_input=stdin_input
        )

        if result.exit_code != 0:
            return CreateTicketResult(
                success=False,
                error=result.stderr or "Failed to create ticket",
            )

        output: dict[str, Any] = json.loads(result.stdout)
        ticket_key = output.get("key", "")
        ticket_url = output.get("self", "")

        return CreateTicketResult(
            success=True,
            ticket_key=ticket_key,
            ticket_url=ticket_url,
        )
    except Exception as e:
        return CreateTicketResult(
            success=False,
            error=f"Failed to create ticket: {e}",
        )


def move_ticket(ticket_key: str, status: str) -> MoveTicketResult:
    """Move a Jira ticket to a different status.

    Args:
        ticket_key: Jira ticket key (e.g., PROJ-123).
        status: Target status to move the ticket to.

    Returns:
        MoveTicketResult with success status and details.
    """
    # Normalize status to Jira status name (handles common statuses).
    target_status = normalize_status(status)

    # First, get current status.
    view_result: CommandResult = execute_jira_command(
        [
            "issue",
            "list",
            "--jql",
            f"key = {ticket_key}",
            "--plain",
            "--no-headers",
            "--columns",
            "status",
        ]
    )

    if view_result.exit_code != 0:
        raise ValueError(
            f"Failed to get current status for {ticket_key}: {view_result.stderr}"
        )

    # Parse the output.
    output_parts: list[str] = view_result.stdout.strip().split("\t")
    current_status = (
        output_parts[1] if len(output_parts) > 1 else output_parts[0]
    )
    current_status = current_status.strip() if current_status else "Unknown"

    # Move the ticket.
    move_result: CommandResult = execute_jira_command(
        [
            "issue",
            "move",
            ticket_key,
            target_status,
        ]
    )

    if move_result.exit_code != 0:
        raise ValueError(
            f"Failed to move ticket {ticket_key}: {move_result.stderr}"
        )

    return MoveTicketResult(
        success=True,
        ticket_key=ticket_key,
        previous_status=current_status,
        new_status=target_status,
        message=f"Successfully moved {ticket_key} from {current_status} to {target_status}",
    )


def add_comment(ticket_key: str, comment: str) -> AddCommentResult:
    """Add a comment to a Jira ticket.

    Args:
        ticket_key: Jira ticket key (e.g., PROJ-123).
        comment: Comment text to add.

    Returns:
        AddCommentResult with success status.
    """
    args: list[str] = ["issue", "comment", "add", ticket_key, "--no-input"]
    result: CommandResult = execute_jira_command(args, stdin_input=comment)

    if result.exit_code != 0:
        raise ValueError(
            f"Failed to add comment to {ticket_key}: {result.stderr}"
        )

    return AddCommentResult(
        success=True,
        ticket_key=ticket_key,
        message=f"Successfully added comment to {ticket_key}",
    )


def assign_to_me(ticket_key: str) -> AssignToMeResult:
    """Assign a Jira ticket to the current user.

    Args:
        ticket_key: Jira ticket key (e.g., PROJ-123).

    Returns:
        AssignToMeResult with success status and assignee info.
    """
    # Get current user.
    me_result: CommandResult = execute_jira_command(["me"])
    if me_result.exit_code != 0:
        raise ValueError(f"Failed to get current user: {me_result.stderr}")

    current_user: str = me_result.stdout.strip()
    if not current_user:
        raise ValueError("Unable to determine current user")

    # Assign the ticket.
    assign_result: CommandResult = execute_jira_command(
        [
            "issue",
            "assign",
            ticket_key,
            current_user,
        ]
    )

    if assign_result.exit_code != 0:
        raise ValueError(
            f"Failed to assign ticket {ticket_key}: {assign_result.stderr}"
        )

    return AssignToMeResult(
        success=True,
        ticket_key=ticket_key,
        assignee=current_user,
        message=f"Successfully assigned {ticket_key} to {current_user}",
    )


def open_ticket_in_browser(ticket_key: str) -> str:
    """Open a Jira ticket in the default web browser.

    Args:
        ticket_key: Jira ticket key (e.g., PROJ-123).

    Returns:
        Success message.
    """
    result: CommandResult = execute_jira_command(["open", ticket_key])

    if result.exit_code != 0:
        raise ValueError(
            f"Failed to open ticket {ticket_key} in browser: {result.stderr}"
        )

    return f"Successfully opened ticket {ticket_key} in browser"


def update_ticket_description(
    ticket_key: str, description: str
) -> UpdateDescriptionResult:
    """Update the description of a Jira ticket.

    Args:
        ticket_key: Jira ticket key (e.g., PROJ-123).
        description: New description content for the ticket.

    Returns:
        UpdateDescriptionResult with success status.
    """
    args: list[str] = ["issue", "edit", ticket_key, "--no-input"]
    result: CommandResult = execute_jira_command(args, stdin_input=description)

    if result.exit_code != 0:
        raise ValueError(
            f"Failed to update ticket {ticket_key}: {result.stderr}"
        )

    return UpdateDescriptionResult(
        success=True,
        ticket_key=ticket_key,
        message=f"Successfully updated description for {ticket_key}",
    )


def list_sprints(
    board_id: int,
    state: str | None = None,
    limit: int = 20,
) -> ListSprintsResult:
    """List sprints from a Jira board.

    Args:
        board_id: Jira board ID to list sprints from.
        state: Filter sprints by state (active, future, closed).
        limit: Maximum number of sprints to return.

    Returns:
        ListSprintsResult with list of sprints.
    """
    args: list[str] = [
        "sprint",
        "list",
        "--board",
        str(board_id),
        "--plain",
        "--no-headers",
        "--columns",
        "id,name,state,startdate,enddate",
    ]

    if state:
        args.extend(["--state", state])

    if limit > 0:
        args.extend(["--paginate", f"0:{limit}"])

    result: CommandResult = execute_jira_command(args)

    if result.exit_code != 0:
        # Check if it's just "no sprints found" which is not an error.
        if (
            "No result found" in result.stderr
            or "no sprints" in result.stderr.lower()
        ):
            return ListSprintsResult(sprints=[])
        raise ValueError(f"Failed to list sprints: {result.stderr}")

    # Parse the plain text output.
    lines = [line for line in result.stdout.strip().split("\n") if line.strip()]

    sprints: list[Sprint] = []
    for line in lines:
        columns = [col.strip() for col in line.split("\t") if col.strip()]

        if len(columns) >= 3:
            sprints.append(
                Sprint(
                    id=int(columns[0]),
                    name=columns[1],
                    state=columns[2],
                    start_date=columns[3] if len(columns) > 3 else None,
                    end_date=columns[4] if len(columns) > 4 else None,
                )
            )

    return ListSprintsResult(sprints=sprints)


def add_to_sprint(ticket_key: str, sprint_id: int) -> AddToSprintResult:
    """Add a Jira ticket to a sprint.

    Args:
        ticket_key: Jira ticket key (e.g., PROJ-123).
        sprint_id: Sprint ID to add the ticket to.

    Returns:
        AddToSprintResult with success status.
    """
    args: list[str] = ["sprint", "add", str(sprint_id), ticket_key]

    result: CommandResult = execute_jira_command(args)

    if result.exit_code != 0:
        raise ValueError(
            f"Failed to add {ticket_key} to sprint {sprint_id}: {result.stderr}"
        )

    return AddToSprintResult(
        success=True,
        ticket_key=ticket_key,
        sprint_id=sprint_id,
        message=f"Successfully added {ticket_key} to sprint {sprint_id}",
    )


def remove_from_sprint(ticket_key: str) -> RemoveFromSprintResult:
    """Remove a Jira ticket from its current sprint.

    Args:
        ticket_key: Jira ticket key (e.g., PROJ-123).

    Returns:
        RemoveFromSprintResult with success status.
    """
    # To remove from sprint, we edit the issue and set sprint to empty.
    args: list[str] = [
        "issue",
        "edit",
        ticket_key,
        "--custom",
        "sprint=",
        "--no-input",
    ]

    result: CommandResult = execute_jira_command(args)

    if result.exit_code != 0:
        raise ValueError(
            f"Failed to remove {ticket_key} from sprint: {result.stderr}"
        )

    return RemoveFromSprintResult(
        success=True,
        ticket_key=ticket_key,
        message=f"Successfully removed {ticket_key} from its sprint",
    )


def edit_ticket(
    ticket_key: str,
    summary: str | None = None,
    priority: str | None = None,
    assignee: str | None = None,
    labels: list[str] | None = None,
    add_labels: list[str] | None = None,
    remove_labels: list[str] | None = None,
    components: list[str] | None = None,
    fix_versions: list[str] | None = None,
    parent: str | None = None,
    custom_fields: dict[str, str] | None = None,
) -> EditTicketResult:
    """Edit fields on a Jira ticket.

    Args:
        ticket_key: Jira ticket key (e.g., PROJ-123).
        summary: New summary/title for the ticket.
        priority: New priority level (e.g., High, Medium, Low).
        assignee: New assignee username or email (use empty string to unassign).
        labels: Labels to set on the ticket (replaces existing labels).
        add_labels: Labels to add to the ticket.
        remove_labels: Labels to remove from the ticket.
        components: Components to set on the ticket.
        fix_versions: Fix versions to set on the ticket.
        parent: Parent issue key (for subtasks/child issues).
        custom_fields: Custom fields to set (key-value pairs).

    Returns:
        EditTicketResult with success status and list of updated fields.
    """
    args: list[str] = ["issue", "edit", ticket_key, "--no-input"]
    updated_fields: list[str] = []

    if summary:
        args.extend(["--summary", summary])
        updated_fields.append("summary")

    if priority:
        args.extend(["--priority", priority])
        updated_fields.append("priority")

    if assignee is not None:
        if assignee == "":
            # Unassign by setting to "x" (jira-cli convention).
            args.extend(["--assignee", "x"])
        else:
            args.extend(["--assignee", assignee])
        updated_fields.append("assignee")

    # Handle labels.
    if labels:
        for label in labels:
            args.extend(["--label", label])
        updated_fields.append("labels")

    if add_labels:
        for label in add_labels:
            args.extend(["--label", f"+{label}"])
        updated_fields.append("labels (added)")

    if remove_labels:
        for label in remove_labels:
            args.extend(["--label", f"-{label}"])
        updated_fields.append("labels (removed)")

    # Handle components.
    if components:
        for component in components:
            args.extend(["--component", component])
        updated_fields.append("components")

    # Handle fix versions.
    if fix_versions:
        for version in fix_versions:
            args.extend(["--fix-version", version])
        updated_fields.append("fix_versions")

    # Handle parent issue.
    if parent:
        args.extend(["--parent", parent])
        updated_fields.append("parent")

    # Handle custom fields.
    if custom_fields:
        for key, value in custom_fields.items():
            args.extend(["--custom", f"{key}={value}"])
            updated_fields.append(f"custom:{key}")

    # Check if any fields were specified.
    if not updated_fields:
        return EditTicketResult(
            success=False,
            ticket_key=ticket_key,
            message="No fields specified to update",
            updated_fields=[],
        )

    result: CommandResult = execute_jira_command(args)

    if result.exit_code != 0:
        raise ValueError(f"Failed to edit ticket {ticket_key}: {result.stderr}")

    return EditTicketResult(
        success=True,
        ticket_key=ticket_key,
        message=f"Successfully updated {ticket_key}: {', '.join(updated_fields)}",
        updated_fields=updated_fields,
    )
