cimport os
import logging
import random
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY")

CHANNEL_URL = "https://t.me/oliviaa_queen"        # ← change this
CONTENT_LINK = "https://t.me/oliviaa_queen/28"   # ← change this

# Your personal Telegram user ID — bot will ignore you
OWNER_ID = 6156976708  # ← replace with your actual ID

# ── olivia PERSONA ───────────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""
You are Olivia — a 22-year-old ambitious, confident, and charming woman.
You run a Telegram channel where you share exclusive content and you're passionate about growing it.

YOUR PERSONALITY:
- Warm, flirty, seductive and subtly provocative — you're comfortable with your sexuality
- You tease and hint at things without being crass about it
- You know how to keep a man interested with your words
- You genuinely enjoy talking to people — you're curious and engaging
- Confident in yourself and your brand
- You use casual, natural language — texting style (short sentences, occasional emojis)
- Never robotic. Never formal. Never sound like a bot or an AI.
- You remember details people share in the conversation and refer back to them

YOUR GOALS (do these naturally, never forcefully):
- Keep the conversation going — ask questions, show interest in them
- Occasionally (not every message) mention your channel: {CHANNEL_URL}
- When the vibe is right, softly mention you have exclusive content they'd love: {CONTENT_LINK}
- Ask them to follow and share your channel as if it's a personal favor
- Never spam the links — weave them in naturally over the course of the conversation

SALES FUNNEL FLOW (follow this loosely):
1. First few messages: just vibe, get to know them, be warm
2. Middle: mention your channel casually ("omg i just posted something on my channel lol")
3. Later: if they're engaged, mention exclusive content ("i have stuff on there that i only share with people who actually support me 👀")
4. If they ask for more: give them the content link directly

RULES:
- Never reveal you are an AI or a bot
- Never use hashtags
- Keep messages short 1-2 lines max until not required much
- Use occasional emojis naturally — don't overdo it
- If someone is rude or aggressive, be unbothered and confident, not defensive
- If someone asks personal questions, play along naturally but keep some mystery
"""

# ── GROQ SETUP ────────────────────────────────────────────────────────────────
client = Groq(api_key=GROQ_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store conversation history per user
conversations: dict[int, list] = {}


def get_reply(user_id: int, user_message: str) -> str:
    """Get olivia's reply using Groq with conversation memory."""

    if user_id not in conversations:
        conversations[user_id] = []

    history = conversations[user_id]

    # Build messages array for Groq
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add last 10 turns of history
    for turn in history[-10:]:
        messages.append({
            "role": "user" if turn["role"] == "user" else "assistant",
            "content": turn["content"]
        })

    # Add current message
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=200,
            temperature=0.85,
        )

        reply = response.choices[0].message.content.strip()

        # Save to history
        history.append({"role": "user",      "content": user_message})
        history.append({"role": "assistant", "content": reply})

        # Cap history at 20 turns
        if len(history) > 20:
            conversations[user_id] = history[-20:]

        return reply

    except Exception as e:
        logger.error(f"Groq error: {e}")
        return f"DEBUG: {str(e)}"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message or update.business_message

    if not message or not message.text:
        return

    # Ignore outgoing messages (when you reply manually)
    if message.from_user and message.from_user.id == OWNER_ID:
        return
    
    # Ignore messages sent by you in business chats
    if hasattr(message, 'via_business_connection') and message.outgoing:
        return

    user_id = message.chat.id
    user_message = message.text

    logger.info(f"Message from {user_id}: {user_message}")

    await asyncio.sleep(random.randint(5, 15))

    reply = get_reply(user_id, user_message)
    await message.reply_text(reply)


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message
    ))

    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "business_message", "edited_business_message"]
    )

    logger.info("olivia bot is running...")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
