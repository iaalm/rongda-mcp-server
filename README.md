# rongda-mcp-server

## MCP setup
```json
{
  "mcpServers": {
    "rongda": {
      "command": "pipx",
      "args": ["run", "rongda-mcp-server"],
      "env": {
        "RD_USER": "",
        "RD_PASS": ""
      }
    }
  }
}
```

or 

```json
{
  "mcpServers": {
    "rongda": {
      "command": "/path/to/rongda-mcp-server",
      "args": [],
      "env": {
        "RD_USER": "",
        "RD_PASS": ""
      }
    }
  }
}
```

## Dev
```
uv sync
```