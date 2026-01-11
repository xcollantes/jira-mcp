# Jira MCP Documentation

This folder contains the documentation site for Jira MCP, built with [Mintlify](https://mintlify.com).

## Development

Install the [Mintlify CLI](https://www.npmjs.com/package/mint) to preview documentation changes locally:

```bash
npm i -g mint
```

Run the following command in this directory where `docs.json` is located:

```bash
mint dev
```

View your local preview at `http://localhost:3000`.

## Publishing changes

Changes are deployed to production automatically after pushing to the default branch.

## Troubleshooting

- If your dev environment isn't running: Run `mint update` to ensure you have the most recent version of the CLI.
- If a page loads as a 404: Make sure you are running in a folder with a valid `docs.json`.
