# Jira MCP

Jira MCP for controlling Jira through Jira Command Line.

## Installation

### Install jira-cli

The MCP server uses the `jira-cli` to execute Jira commands.

Follow the installation instructions for your operating system:
<https://github.com/ankitpokhrel/jira-cli?tab=readme-ov-file#installation>

### Get Jira API Key

Depending on your implementation of Jira (Cloud or Self-Hosted), you will need
to use a different authentication type.

Add these to your `.bashrc` or `.zshrc` file, or other shell configuration file.

```bash
# https://id.atlassian.com/manage-profile/security/api-tokens
export JIRA_API_KEY=""

# `bearer` for token,
# `basic` for Jira account API token
# `password` for Jira account password
export JIRA_AUTH_TYPE="basic"
```

Make sure to `source` the file after adding the credentials.

```bash
source ~/.bashrc
```

Other ways to add credentials to your environment:
<https://github.com/ankitpokhrel/jira-cli/discussions/356>

### Start Jira CLI

```bash
jira init
```

This should initialize the Jira CLI by asking for your Jira URL and credentials.

### Test Jira CLI

```bash
jira issue list
```

This should return a list of issues in Jira.

### MCP Server: Option 1: Download binaries

Download the latest release for your operating system from the [Releases
page](https://github.com/xcollantes/jira-mcp/releases).

| Operating System | Binary |
|------------------|--------|
| Linux | `jira-mcp-linux` |
| Windows | `jira-mcp-windows.exe` |
| macOS (Apple Silicon M1/M2/M3) | `jira-mcp-macos-arm64-apple-silicon` |
| macOS (Intel) | `jira-mcp-macos-x64` |

#### Linux

```bash
# Download the binary
curl -L -o jira-mcp https://github.com/xcollantes/jira-mcp/releases/latest/download/jira-mcp-linux

# Make it executable
chmod +x jira-mcp

# Move to a directory in your PATH (optional)
sudo mv jira-mcp /usr/local/bin/
```

Add to your LLM client configuration:

```json
{
  "mcpServers": {
    "jira": {
      "command": "/usr/local/bin/jira-mcp"
    }
  }
}
```

#### macOS

```bash
# For Apple Silicon (M1/M2/M3)
curl -L -o jira-mcp https://github.com/xcollantes/jira-mcp/releases/latest/download/jira-mcp-macos-arm64-apple-silicon

# For Intel Macs
curl -L -o jira-mcp https://github.com/xcollantes/jira-mcp/releases/latest/download/jira-mcp-macos-x64

# Make it executable
chmod +x jira-mcp

# Move to a directory in your PATH (optional)
sudo mv jira-mcp /usr/local/bin/
```

**Note:** macOS may block the binary on first run. If you see a security
warning, go to **System Settings > Privacy & Security** and click **Allow
Anyway**, or run:

```bash
xattr -d com.apple.quarantine /usr/local/bin/jira-mcp
```

Add to your LLM client configuration:

```json
{
  "mcpServers": {
    "jira": {
      "command": "/usr/local/bin/jira-mcp"
    }
  }
}
```

#### Windows

1. Download `jira-mcp-windows.exe` from the [Releases
   page](https://github.com/xcollantes/jira-mcp/releases).
2. Move the executable to a convenient location (e.g., `C:\Program
   Files\jira-mcp\`).

Add to your LLM client configuration:

```json
{
  "mcpServers": {
    "jira": {
      "command": "C:\\Program Files\\jira-mcp\\jira-mcp-windows.exe"
    }
  }
}
```

### MCP Server: Option 2: Development setup with uv

Get repo:

```bash
git clone https://github.com/xcollantes/jira-mcp.git
cd jira-mcp
```

Add MCP server to your choice of LLM client:

**NOTE:** You will need to look up for your specific client on how to add MCPs.

Usually the JSON file for the LLM client will look like this:

```json
{
  "mcpServers": {
    "jira": {
      "command": "uv",
      "args": ["--directory", "/ABSOLUTE/PATH/TO/REPO/ROOT", "run", "python", "-m", "src.main"]
    }
  }
}
```

This will tell your LLM client application that there's a tool that can be
called by calling `uv --directory /ABSOLUTE/PATH/TO/REPO run python -m
src.main`.

Install UV: <https://docs.astral.sh/uv/getting-started/installation/>

### MCP Server: Option 3: Install globally with pipx

```bash
# Install pipx if you haven't already
brew install pipx
pipx ensurepath

# Clone and install the MCP server
git clone https://github.com/xcollantes/jira-mcp.git
cd jira-mcp
pipx install -e .
```

## How it works

1. You enter some questions or prompt to a LLM Client such as the Claude
   Desktop, Cursor, Windsurf, or ChatGPT.
2. The client sends your question to the LLM model (Sonnet, Grok, ChatGPT)
3. LLM analyzes the available tools and decides which one(s) to use
   - The LLM you're using will have a context of the tools and what each tool is
     meant for in human language.
   - Alternatively without MCPs, you could include in the prompt the endpoints
     and a description on each endpoint for the LLM to "call on". Then you could
     copy and paste the text commands into the terminal on your machine.
   - MCPs provide a more deterministic and standardized method on LLM-to-server
     interactions.
4. The client executes the chosen tool(s) through the MCP server.
   - The MCP server is either running local on your machine or an endpoint
     hosting the MCP server remotely.
5. The results are sent back to LLM.
6. LLM formulates a natural language response and one or both of the following
   happen:
   - The response is displayed to you with data from the MCP server
   - Some action is performed using the MCP server

## Development

### Logging

Do not use `print` statements for logging. Use the logging module instead.
Writing to stdout will corrupt the JSON-RPC messages and break your server.

## Docstrings / Tool decorator parameters

MCP.tools decorator parameters are especially important as this is the human
readable text that the LLM has context of. This will be treated as part of the
prompt when fed to the LLM and this will decide when to use each tool.

## Architecture

MCP follows a client-server architecture where an **MCP host** (an AI
application like Cursor or ChatGPT desktop) establishes connections to one or
more **MCP servers**. The **MCP host** accomplishes this by creating one **MCP
client** for each **MCP server**. Each MCP client maintains a dedicated
connection with its corresponding MCP server.

<https://modelcontextprotocol.io/docs/learn/architecture>

## Pitfalls / Troubleshooting

## Edit the jira-cli config file

On MacOS:

```text
/Users/<your-username>/.config/.jira/.config.yml
```

## 404 error when using `jira init`

If you get a 404 error when using `jira init`, you may need to edit the jira-cli
config file to point to the correct Jira instance. There are only 3 possible
values for the auth type so try each one. `basic`, `password`, or `bearer`.
