import time
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from config import API_ID, API_HASH, SESSION_STRING
# Define your bot token and the user ID of the authorized user

AUTHORIZED_USER_ID = 6058139652 # Replace with the authorized user's ID
CHANNEL_ID = "-1002486895937"  # Replace with the channel ID you want to forward messages from

# Create a Pyrogram Client instance
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# Function to forward the message to all joined groups
async def forward_message_to_all_groups(message):
    # Get all the chat IDs of the groups the bot is in
    async for chat in app.get_chats():
        if chat.type == "supergroup" or chat.type == "group":
            try:
                # Forward the message to each group
                await app.forward_messages(chat.id, message.chat.id, message.message_id)
                time.sleep(1)  # To prevent too many requests at once, handle flood wait
            except FloodWait as e:
                print(f"Flood wait: Sleeping for {e.x} seconds.")
                time.sleep(e.x)  # Handle flood wait
            except Exception as e:
                print(f"Error forwarding message: {e}")

# Handler to forward messages from the specific channel to all groups
@app.on_message(filters.chat(CHANNEL_ID))
async def forward_channel_message(client, message):
    # Forward the message to all groups
    await forward_message_to_all_groups(message)

# Command handler for the userbot (only authorized user can run this)
@app.on_message(filters.command("forward") & filters.user(AUTHORIZED_USER_ID))
async def forward_command(client, message):
    # Make sure there is a message to forward
    if len(message.command) < 2:
        await message.reply("Please provide the message ID you want to forward.")
        return

    # Get the target message ID to forward
    try:
        message_id = int(message.command[1])
        target_message = await message.chat.get_message(message_id)
    except ValueError:
        await message.reply("Invalid message ID.")
        return
    except Exception as e:
        await message.reply(f"Error: {e}")
        return

    # Call the function to forward the message to all groups
    await forward_message_to_all_groups(target_message)
    await message.reply("Message forwarded to all groups.")

# Start the bot
app.run()
