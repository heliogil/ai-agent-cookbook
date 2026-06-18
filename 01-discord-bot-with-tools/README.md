# 01 — Discord Bot with Tools

A Discord bot that can run shell commands and read files using MiniMax M3 tool use. Under 100 lines.

## What it does

- Responds to DMs and `@mentions`
- Has two tools: `bash` (allowlisted commands only) and `read_file`
- Keeps last 10 messages as conversation history
- Handles multi-round tool calls automatically

## Setup

```bash
pip install -r requirements.txt

export MINIMAX_API_KEY=your_key
export DISCORD_BOT_TOKEN=your_bot_token
python bot.py
```

## Create a Discord bot

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. New Application → Bot → Reset Token → copy token
3. OAuth2 → URL Generator → scopes: `bot` → permissions: `Send Messages`, `Read Message History`
4. Open the generated URL to add the bot to your server

## Extend it

Add a tool to the `TOOLS` list and handle it in `run_tool()`. Example — web search:

```python
{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web and return top results.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
}
```

## Security note

The `bash` tool uses an allowlist (`ALLOWED_COMMANDS`). Never allow arbitrary shell execution in a shared Discord server.
