import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
import time
from config import API_ID, API_HASH, SESSION_STRING

# Replace with the source channel username or ID (e.g., "my_channel" or -1001234567890)
SOURCE_CHANNEL = "adstesting3"

# Replace with the message ID you want to forward. Use 1 if you want to forward the most recent one
MESSAGE_ID_TO_FORWARD = 2

# Minimum delay between main loops (in seconds). Adjust this based on testing.
MIN_BASE_DELAY = 90  # 1.5 minutes. Use with CAUTION. Start much higher if unsure.

# Additional delay per chat to avoid flooding. Adjust this value based on your experience
CHAT_DELAY = 2  # Seconds - Reduced to allow for faster overall sending.

# Maximum number of FloodWait exceptions allowed in a single loop before increasing BASE_DELAY
MAX_FLOOD_WAITS = 2  # React more quickly to FloodWaits

# Amount to increase and decrease base_delay (in seconds)
INCREASE_STEP = 20
DECREASE_STEP = 3

# Replace with the user ID of the authorized user who can start/stop the bot
AUTHORIZED_USER = 6058139652 # Replace with the actual user ID

# Replace with the channel ID where you want to send logs
LOG_CHANNEL_ID = -1002275756264 # Replace with your actual channel ID (must start with -100)

app = Client("forward_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

forwarding_task = None  # Global variable to hold the forwarding task
forwarding_active = False # Global variable to show running status

async def log_message(message: str):
    """Sends a message to the log channel."""
    try:
        await app.send_message(LOG_CHANNEL_ID, message)
    except Exception as e:
        print(f"Error sending log message: {e}")  # Log to console if logging fails

async def forward_message():
    """Forwards the specified message from the source channel to all joined chats,
       dynamically adjusting the base delay based on FloodWait occurrences."""
    global forwarding_task, forwarding_active
    base_delay = MIN_BASE_DELAY  # Start with the minimum delay
    while forwarding_active: #loop until stop
        flood_wait_count = 0  # Reset count for each loop
        try:
            dialogs = []
            async for dialog in app.get_dialogs():
                dialogs.append(dialog)

            for dialog in dialogs:  # Iterate normally to have better control on the loop
                chat = dialog.chat
                if chat.type in ("group", "supergroup", "channel"):
                    try:
                        await app.forward_messages(chat.id, SOURCE_CHANNEL, MESSAGE_ID_TO_FORWARD)
                        log_msg = f"Forwarded to {chat.title or chat.username or chat.id}"
                        print(log_msg)
                        await log_message(log_msg)
                    except FloodWait as e:
                        flood_wait_count += 1
                        log_msg = f"FloodWait encountered for {chat.title or chat.username or chat.id}. Sleeping for {e.value} seconds."
                        print(log_msg)
                        await log_message(log_msg)
                        await asyncio.sleep(e.value)
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
                        log_msg = f"Error forwarding to {chat.title or chat.username or chat.id}: {e}"
                        print(log_msg)
                        await log_message(log_msg)

                    await asyncio.sleep(CHAT_DELAY)  # Small delay between chats

        except Exception as e:
            log_msg = f"Error in main loop: {e}"
            print(log_msg)
            await log_message(log_msg)

        # Dynamic base delay adjustment
        if flood_wait_count > MAX_FLOOD_WAITS:
            base_delay += INCREASE_STEP  # Increase base delay by 20 seconds (was 30)
            log_msg = f"Too many FloodWaits ({flood_wait_count}). Increasing base delay to {base_delay} seconds."
            print(log_msg)
            await log_message(log_msg)
        else:
             # Optionally, decrease base_delay if no FloodWaits occur (but not below MIN_BASE_DELAY)
             if base_delay > MIN_BASE_DELAY:
                 base_delay -= DECREASE_STEP # Decrease by 3 seconds (was 5)
                 base_delay = max(base_delay, MIN_BASE_DELAY) #Ensure base delay not fall below minimum base delay
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
        await log_message("Forwarding bot started by user.") #log the start command
    else:
        await message.reply_text("Forwarding bot is already running.")

@app.on_message(filters.command("stop") & filters.user(AUTHORIZED_USER))
async def stop_command(client: Client, message: Message):
    """Handles the /stop command."""
    global forwarding_task, forwarding_active
    if forwarding_task:
        forwarding_active = False #stop the loop
        await message.reply_text("Forwarding bot stopped.")
        await log_message("Forwarding bot stopped by user.") #log the stop command
    else:
        await message.reply_text("Forwarding bot is not running.")

if __name__ == "__main__":
    print("Bot started. Remember to fill in your API credentials, source channel, and message ID.")
    app.start()
    app.idle()
