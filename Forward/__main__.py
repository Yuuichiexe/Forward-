import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from config import API_ID, API_HASH, SESSION_STRING

# Define authorized user ID and interval for forwarding
AUTHORIZED_USER_ID = 6058139652  # Replace with your Telegram ID
FORWARD_INTERVAL = 20  # Time in seconds between each forwarding cycle

# Initialize the Pyrogram Client
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# Global variable to control the forwarding loop
forwarding_active = False
forwarding_message = None  # Store the message to be forwarded

async def get_groups():
    """Fetch all groups and supergroups the bot has joined."""
    groups = []
    async for dialog in app.get_dialogs():
        if dialog.chat.type in ["supergroup", "group"]:
            groups.append(dialog.chat.id)
    return groups

async def forward_message_to_all_groups():
    """Forward the stored message to all joined groups."""
    global forwarding_message
    if not forwarding_message:
        return

    groups = await get_groups()
    
    for group_id in groups:
        try:
            await app.forward_messages(group_id, forwarding_message.chat.id, forwarding_message.message_id)
            await asyncio.sleep(1)  # Avoid hitting Telegram's flood limit
        except FloodWait as e:
            print(f"Flood wait: Sleeping for {e.value} seconds.")
            await asyncio.sleep(e.value)  # Handle flood wait
        except Exception as e:
            print(f"Error forwarding to {group_id}: {e}")

async def start_forwarding():
    """Continuously forward the message every FORWARD_INTERVAL seconds."""
    global forwarding_active
    forwarding_active = True

    while forwarding_active:
        await forward_message_to_all_groups()
        await asyncio.sleep(FORWARD_INTERVAL)  # Wait before the next cycle

@app.on_message(filters.command("forward") & filters.user(AUTHORIZED_USER_ID))
async def forward_command(client, message):
    """Handles the /forward command when replying to a message."""
    global forwarding_active, forwarding_message

    if not message.reply_to_message:
        await message.reply("Please reply to a message you want to forward.")
        return

    if forwarding_active:
        await message.reply("Forwarding is already running. Use /stop to stop it.")
        return

    # Store the replied message
    forwarding_message = message.reply_to_message

    # Start the forwarding loop
    asyncio.create_task(start_forwarding())

    await message.reply("Forwarding started. The message will be forwarded every 20 seconds.")

@app.on_message(filters.command("stop") & filters.user(AUTHORIZED_USER_ID))
async def stop_command(client, message):
    """Handles the /stop command."""
    global forwarding_active
    if not forwarding_active:
        await message.reply("No forwarding process is running.")
        return

    forwarding_active = False
    await message.reply("Forwarding stopped.")

# Start the bot
app.run()
