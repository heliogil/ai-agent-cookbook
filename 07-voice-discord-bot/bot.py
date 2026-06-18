"""
Voice Discord bot — Whisper STT → MiniMax M3 → TTS reply.
Run: pip install -r requirements.txt && python bot.py
"""
import os, io, asyncio, tempfile
from pathlib import Path
import discord
from openai import AsyncOpenAI

DISCORD_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
MINIMAX_KEY   = os.environ["MINIMAX_API_KEY"]
BASE_URL      = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/anthropic/v1")
TTS_VOICE     = os.environ.get("TTS_VOICE", "alloy")

ai      = AsyncOpenAI(api_key=MINIMAX_KEY, base_url=BASE_URL)
intents = discord.Intents.default()
intents.message_content = True
bot     = discord.Client(intents=intents)


async def transcribe(audio_bytes: bytes, filename: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as f:
        f.write(audio_bytes)
        tmp = f.name
    try:
        with open(tmp, "rb") as f:
            resp = await ai.audio.transcriptions.create(
                model="whisper-1", file=f, language="pt"
            )
        return resp.text
    finally:
        Path(tmp).unlink(missing_ok=True)


async def reply_text(prompt: str) -> str:
    resp = await ai.chat.completions.create(
        model="MiniMax-M3",
        messages=[
            {"role": "system", "content": "You are a concise, helpful voice assistant. Keep replies under 3 sentences."},
            {"role": "user",   "content": prompt},
        ],
    )
    return resp.choices[0].message.content


async def synthesise(text: str) -> bytes:
    resp = await ai.audio.speech.create(model="tts-1", voice=TTS_VOICE, input=text)
    return resp.content


@bot.event
async def on_ready():
    print(f"Voice bot ready: {bot.user}")


@bot.event
async def on_message(msg: discord.Message):
    if msg.author == bot.user:
        return
    if not (bot.user.mentioned_in(msg) or isinstance(msg.channel, discord.DMChannel)):
        return

    # Voice message (audio attachment)
    audio = next((a for a in msg.attachments if a.content_type and "audio" in a.content_type), None)
    if audio:
        async with msg.channel.typing():
            audio_bytes = await audio.read()
            transcript  = await transcribe(audio_bytes, audio.filename)
            await msg.channel.send(f"*Heard: {transcript}*")
            text  = await reply_text(transcript)
            audio_reply = await synthesise(text)
            await msg.channel.send(
                content=text,
                file=discord.File(io.BytesIO(audio_reply), filename="reply.mp3")
            )
        return

    # Text message
    text_input = msg.content.replace(f"<@{bot.user.id}>", "").strip()
    if not text_input:
        return

    async with msg.channel.typing():
        reply = await reply_text(text_input)
        audio_reply = await synthesise(reply)
        await msg.channel.send(
            content=reply,
            file=discord.File(io.BytesIO(audio_reply), filename="reply.mp3")
        )


bot.run(DISCORD_TOKEN)
