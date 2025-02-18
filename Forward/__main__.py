import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from config import API_ID, API_HASH, SESSION_STRING

# Replace with the source channel username or ID
SOURCE_CHANNEL = "-1002486895937"
# Replace with the message ID you want to forward
MESSAGE_ID_TO_FORWARD = 367998

# Minimum delay between loops (in seconds)
MIN_BASE_DELAY = 90  # 1.5 minutes

# Additional delay per chat to avoid flooding
CHAT_DELAY = 2  # Seconds

# Maximum number of FloodWait exceptions allowed before adjusting delay
MAX_FLOOD_WAITS = 2

# Amount to increase/decrease base_delay (in seconds)
INCREASE_STEP = 20
DECREASE_STEP = 3

# Replace with the user ID of the authorized user
AUTHORIZED_USER = 6058139652

# Replace with the channel ID where you want to send logs
LOG_CHANNEL_ID = -1002275756264

app = Client("forward_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

forwarding_task = None
forwarding_active = False


async def log_message(message: str):
    """Sends a message to the log channel."""
    try:
        await app.send_message(LOG_CHANNEL_ID, message)
    except Exception as e:
        print(f"Error sending log message: {e}")


async def forward_message():
    """Forwards the specified message to all joined chats."""
    global forwarding_task, forwarding_active, MESSAGE_ID_TO_FORWARD
    base_delay = MIN_BASE_DELAY
    while forwarding_active:
        flood_wait_count = 0
        try:
            dialogs = []
            async for dialog in app.get_dialogs():
                dialogs.append(dialog)

            for dialog in dialogs:
                chat = dialog.chat
                if chat.type in ("group", "supergroup", "channel", "private"):  # Handle all types of chats
                    try:
                        await app.forward_messages(chat.id, SOURCE_CHANNEL, MESSAGE_ID_TO_FORWARD)
                        log_msg = f"Forwarded to {chat.title or chat.username or chat.id}"
                        print(log_msg)
                        await log_message(log_msg)
                    except FloodWait as e:
                        flood_wait_count += 1
                        log_msg = f"FloodWait encountered for {chat.title or chat.username or chat.id}. Sleeping for {e.x} seconds."
                        print(log_msg)
                        await log_message(log_msg)
                        await asyncio.sleep(e.x)  # Wait for the flood period
                        try:
                            await app.forward_messages(chat.id, SOURCE_CHANNEL, MESSAGE_ID_TO_FORWARD)
                            log_msg = f"Forwarded to {chat.title or chat.username or chat.id} after FloodWait"
                            print(log_msg)
                            await log_message(log_msg)
                        except Exception as e2:
                            log_msg = f"Failed to forward to {chat.title or chat.username or chat.id} after FloodWait: {e2}"
                            print(log_msg)
                            await log_message(log_msg)
                    except Exception as e:
                        try:
                            chat_info = chat.title or str(chat.id)
                        except:
                            chat_info = str(chat.id)
                        log_msg = f"Error forwarding to {chat_info}: {e}"
                        print(log_msg)
                        await log_message(log_msg)

                    await asyncio.sleep(CHAT_DELAY)

        except Exception as e:
            log_msg = f"Error in main loop: {e}"
            print(log_msg)
            await log_message(log_msg)

        # Adjust base delay based on flood wait count
        if flood_wait_count > MAX_FLOOD_WAITS:
            base_delay += INCREASE_STEP
            log_msg = f"Too many FloodWaits ({flood_wait_count}). Increasing base delay to {base_delay} seconds."
            print(log_msg)
            await log_message(log_msg)
        else:
            if base_delay > MIN_BASE_DELAY:
                base_delay -= DECREASE_STEP
                base_delay = max(base_delay, MIN_BASE_DELAY)
                log_msg = f"Decreasing base delay to {base_delay} seconds."
                print(log_msg)
                await log_message(log_msg)

        log_msg = f"Sleeping for {base_delay} seconds..."
        print(log_msg)
        await log_message(log_msg)
        await asyncio.sleep(base_delay)

    log_msg = "Forwarding task stopped."
    print(log_msg)
    await log_message(log_msg)
    forwarding_task = None
    forwarding_active = False


@app.on_message(filters.command("start") & filters.user(AUTHORIZED_USER))
async def start_command(client: Client, message: Message):
    """Handles the /start command."""
    global forwarding_task, forwarding_active
    if forwarding_task is None:
        forwarding_active = True
        forwarding_task = asyncio.create_task(forward_message())
        await message.reply_text("Forwarding bot started.")
        await log_message("Forwarding bot started by user.")
    else:
        await message.reply_text("Forwarding bot is already running.")


@app.on_message(filters.command("stop") & filters.user(AUTHORIZED_USER))
async def stop_command(client: Client, message: Message):
    """Handles the /stop command."""
    global forwarding_task, forwarding_active
    if forwarding_task:
        forwarding_active = False
        await message.reply_text("Forwarding bot stopped.")
        await log_message("Forwarding bot stopped by user.")
    else:
        await message.reply_text("Forwarding bot is not running.")


@app.on_message(filters.command("update_message_id") & filters.user(AUTHORIZED_USER))
async def update_message_id(client: Client, message: Message):
    """Handles the /update_message_id command."""
    global MESSAGE_ID_TO_FORWARD
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.reply_text("Usage: /update_message_id <message_id>")
        return
    new_message_id = int(args[1])
    MESSAGE_ID_TO_FORWARD = new_message_id
    await message.reply_text(f"MESSAGE_ID_TO_FORWARD updated to {MESSAGE_ID_TO_FORWARD}")
    await log_message(f"MESSAGE_ID_TO_FORWARD updated to {MESSAGE_ID_TO_FORWARD} by user")


if __name__ == "__main__":
    app.run()  # Start the bot using the 'run' method
