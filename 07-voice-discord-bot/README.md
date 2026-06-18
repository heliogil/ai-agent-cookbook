# 07 — Voice Discord Bot

Send audio or text messages; the bot transcribes, thinks, and replies with both text and speech.

## Setup

```bash
pip install -r requirements.txt
export DISCORD_BOT_TOKEN=your_discord_token
export MINIMAX_API_KEY=your_key
python bot.py
```

Optional:
```bash
export TTS_VOICE=alloy          # alloy | echo | fable | onyx | nova | shimmer
export MINIMAX_BASE_URL=https://api.minimax.io/anthropic/v1
```

## Usage

1. Mention the bot or DM it with a text message → receive text reply + MP3
2. Attach an audio file (voice message) → bot transcribes it, replies with text + MP3

```
User: @VoiceBot what's the weather like?
Bot:  I don't have real-time data, but I can help with general questions!
      [reply.mp3 attached]

User: [sends voice-message.ogg]
Bot:  *Heard: quando é que o jogo começa?*
      O jogo começa às 20h conforme o horário agendado.
      [reply.mp3 attached]
```

## How it works

```
audio attachment  →  Whisper STT  →  MiniMax M3  →  TTS  →  text + MP3
text message      →               →  MiniMax M3  →  TTS  →  text + MP3
```

1. **Trigger**: mention or DM
2. **Audio path**: download attachment → temp file → Whisper transcription
3. **Text path**: strip mention from message content
4. **Reply**: MiniMax M3 chat (≤ 3 sentences) → TTS → `discord.File`

## Extend it

**Add conversation memory**: Store last N turns per user in a dict keyed by `msg.author.id`.

**Language detection**: Let Whisper auto-detect language by removing the `language="pt"` parameter.

**Voice channels**: Use `discord.py`'s voice client to join a voice channel and stream audio directly instead of uploading files.
