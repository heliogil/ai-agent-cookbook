"""
Discord bot with tool use — MiniMax M3
Run: pip install -r requirements.txt && python bot.py
"""
import os, asyncio, subprocess
import discord
from openai import AsyncOpenAI

DISCORD_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
MINIMAX_KEY   = os.environ["MINIMAX_API_KEY"]
BASE_URL      = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/anthropic/v1")

client_ai = AsyncOpenAI(api_key=MINIMAX_KEY, base_url=BASE_URL)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a safe, read-only shell command and return stdout.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative file path"}
                },
                "required": ["path"],
            },
        },
    },
]

ALLOWED_COMMANDS = {"ls", "pwd", "echo", "date", "whoami", "df", "free", "uptime"}

def run_tool(name: str, args: dict) -> str:
    if name == "bash":
        cmd = args["command"].strip()
        first_word = cmd.split()[0] if cmd.split() else ""
        if first_word not in ALLOWED_COMMANDS:
            return f"[blocked] '{first_word}' is not in the allowed command list."
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout or result.stderr or "(no output)"

    if name == "read_file":
        path = args["path"]
        if not os.path.exists(path):
            return f"[error] file not found: {path}"
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()[:4000]

    return f"[error] unknown tool: {name}"


async def agent_reply(user_message: str, history: list) -> str:
    messages = history + [{"role": "user", "content": user_message}]

    for _ in range(5):  # max tool rounds
        response = await client_ai.chat.completions.create(
            model="MiniMax-M3",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content or "(no response)"

        messages.append(msg)
        for call in msg.tool_calls:
            result = run_tool(call.function.name, eval(call.function.arguments))
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": result,
            })

    return "(max tool rounds reached)"


intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
history: list = []

@bot.event
async def on_ready():
    print(f"Bot ready: {bot.user}")

@bot.event
async def on_message(message: discord.Message):
    global history
    if message.author == bot.user:
        return
    if not (bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel)):
        return

    text = message.content.replace(f"<@{bot.user.id}>", "").strip()
    if not text:
        return

    async with message.channel.typing():
        reply = await agent_reply(text, history[-10:])
        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": reply})

    for chunk in [reply[i:i+1900] for i in range(0, len(reply), 1900)]:
        await message.channel.send(chunk)

bot.run(DISCORD_TOKEN)
