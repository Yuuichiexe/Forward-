import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.enums import ChatType
from config import API_ID, API_HASH, SESSION_STRING

# Setup logging for debugging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define authorized user ID and interval for forwarding
AUTHORIZED_USER_ID = 6058139652  # Replace with your Telegram ID
FORWARD_INTERVAL = 60 # Time in seconds between each forwarding cycle

# Initialize the Pyrogram Client
app = Client("Hhootspoot", api_id=20222660, api_hash="5788f1f4a93f2de28835a0cf1b0ebae4", session_string="BAE0ksQAngC-6r20gJlK7hIiepnxUTEYSc2b_mYwhsj_K29xk7j7eRog0evkSafa-Lk0HNVok9jn1dQJc2o3xYjzmO7cM2Qi-s-r_dkUNE30PP0_gqyMAQ1_E0LShAL07mrYsezQjH9DWsHgfnXtPJQsTjhd8lA7Cgg_VMmOOR6Hrpf_sXfl6evUETrCuspYnMQLLAwbLzD74jpmwaFar4vYoxY5cz42LOjfzjbXJ6It74L9bxOxF9nXQlzJ3TYijGG4_p8wywtWKhc8gDgZqyT3ltmGl5GuDVeu7oyi8TYZvQGVRkk_2biBrQfG89EsQ2q0CLxprISPcKfw0bLQ3ggpLNKAAAAAG-9-oTAA")

# Global variables
forwarding_active = False
forwarding_message = None  # Store the message to be forwarded

async def list_chats():
    async with app:
        async for dialog in app.get_dialogs():
            print(f"Chat ID: {dialog.chat.id} | Name: {dialog.chat.title} | Type: {dialog.chat.type}")

async def get_groups(client):
    """Fetch all groups and supergroups the bot has joined."""
    groups = []
    
    async for dialog in client.get_dialogs():
        chat = dialog.chat
        print(f"Checking Chat: {chat.title} | Type: {chat.type} | ID: {chat.id}")

        # ✅ Correct way to filter groups
        if chat.type in [ChatType.SUPERGROUP, ChatType.GROUP]:
            groups.append(chat.id)

    logging.info(f"✅ Found {len(groups)} groups: {groups}")
    
    if not groups:
        logging.error("❌ No groups found! Check bot permissions.")
    
    return groups


async def forward_message_to_all_groups(client):
    """Forward the stored message to all joined groups."""
    global forwarding_message
    if not forwarding_message:
        logging.warning("⚠️ No message stored for forwarding.")
        return

    groups = await get_groups(client)
    
    if not groups:
        logging.error("❌ No groups found! Check bot permissions.")
        return

    for group_id in groups:
        try:
            # ✅ Correct the message ID attribute
            await client.forward_messages(group_id, forwarding_message.chat.id, forwarding_message.id)
            logging.info(f"📤 Message forwarded to group {group_id}")
            await asyncio.sleep(2)  # Avoid hitting Telegram's flood limit
        except FloodWait as e:
            logging.warning(f"⏳ Flood wait triggered! Sleeping for {e.value} seconds.")
            await asyncio.sleep(e.value)
        except Exception as e:
            logging.error(f"⚠️ Error forwarding to {group_id}: {e}")


async def start_forwarding(client):
    """Continuously forward the message every FORWARD_INTERVAL seconds."""
    global forwarding_active
    forwarding_active = True

    while forwarding_active:
        logging.info("🔄 Forwarding message to all groups...")
        await forward_message_to_all_groups(client)
        await asyncio.sleep(FORWARD_INTERVAL)  # Wait before the next cycle

@app.on_message(filters.command("forward") & filters.user(AUTHORIZED_USER_ID))
async def forward_command(client, message):
    """Handles the /forward command when replying to a message."""
    global forwarding_active, forwarding_message

    if not message.reply_to_message:
        await message.reply("⚠️ Please reply to a message you want to forward.")
        return

    if forwarding_active:
        await message.reply("⚠️ Forwarding is already running. Use /stop to stop it.")
        return

    # Store the replied message
    forwarding_message = message.reply_to_message

    # Start the forwarding loop
    asyncio.create_task(start_forwarding(client))

    await message.reply(f"✅ Forwarding started! The message will be forwarded every {FORWARD_INTERVAL} seconds.")

@app.on_message(filters.command("stop") & filters.user(AUTHORIZED_USER_ID))
async def stop_command(client, message):
    """Handles the /stop command."""
    global forwarding_active
    if not forwarding_active:
        await message.reply("⚠️ No forwarding process is running.")
        return

    forwarding_active = False
    logging.info("🛑 Forwarding process stopped.")
    await message.reply("🛑 Forwarding stopped.")

# Start the bot
app.run()
