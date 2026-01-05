# mcp-template

MCP template.

## Development

### TODOs

Find `# TODO` comments and implement them.

### Logging

Do not use `print` statements for logging. Use the logging module instead.
Writing to stdout will corrupt the JSON-RPC messages and break your server.

## Docstrings / Tool decorator parameters

MCP.tools decorator parameters are especially important as this is the human
readable text that the LLM has context of. This will be treated as part of the
prompt when fed to the LLM and this will decide when to use each tool.

## Installation

### Option 1: Development setup with uv

Get repo:

```bash
git clone https://github.com/xcollantes/mcp-template.git  # TODO: Change to your own repository.
cd mcp-template
```

Install UV: <https://docs.astral.sh/uv/getting-started/installation/>

### Option 2: Install globally with pipx

```bash
# Install pipx if you haven't already
brew install pipx
pipx ensurepath

# Clone and install the MCP server
git clone https://github.com/xcollantes/mcp-template.git  # TODO: Change to your own repository.
cd mcp-template
pipx install -e .
```

Now you can run the MCP server directly:

```bash
mcp-template --help
mcp-template --debug  # Run with debug logging
```

### Option 3: Manual setup

Add MCP server to your choice of LLM client:

**NOTE:** You will need to look up for your specific client on how to add MCPs.

Usually the JSON file for the LLM client will look like this:

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": ["--directory", "/ABSOLUTE/PATH/TO/REPO", "run", "python", "-m", "src.main"]
    }
  }
}
```

This will tell your LLM client application that there's a tool that can be
called by calling `uv --directory /ABSOLUTE/PATH/TO/REPO run python -m src.main`.

## How it works

1. You enter some questions or prompt to a LLM Client such as the Claude
   Desktop, Cursor, Windsurf, or ChatGPT.
2. The client sends your question to the LLM model (Sonnet, Grok, ChatGPT)
3. LLM analyzes the available tools and decides which one(s) to use
   - The LLM you're using will have a context of the tools and what each tool
     is meant for in human language.
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

## Architecture

MCP follows a client-server architecture where an **MCP host** (an AI
application like Cursor or ChatGPT desktop) establishes connections to one or
more **MCP servers**. The **MCP host** accomplishes this by creating one **MCP
client** for each **MCP server**. Each MCP client maintains a dedicated
connection with its corresponding MCP server.

<https://modelcontextprotocol.io/docs/learn/architecture>
