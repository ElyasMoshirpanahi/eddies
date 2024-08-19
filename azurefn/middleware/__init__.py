import logging

import azure.functions as func
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import json
import logging
from telegram import Update, Chat
from telegram.error import TelegramError
from telegram.ext import ContextTypes
from telegram import Update, Chat
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import json
import logging

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Configuration
TOKEN = "6385990167:AAHTRuFOBTKX4vgmBkj6uI8CNFCgW7mO0dw"
SUPER_ADMIN_ID = 80741935  # Replace with the actual super admin's user ID

# File to store admin IDs, group ID, and channel ID
CONFIG_FILE = "bot_config.json"

# Load configuration from file
def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"admins": [], "group_id": None, "channel_id": None}

# Save configuration to file
def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)

# Initialize configuration
config = load_config()

# Helper function to check if a user is an admin or super admin
def is_authorized(user_id):
    return user_id == SUPER_ADMIN_ID or user_id in config["admins"]

# Command handler for when the bot is started
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_authorized(user_id):
        await update.message.reply_text(
            "خوش امدید دستورات کنونی ربات:\n"
            "/help - نشان دادن منوی راهنما\n"
            "/register_admin - افزودن ادمین های جدید (فقط سوپرادمین مجاز به این دستور است)\n"
            "/register_ids - ست کردن هماهنگی ارسال پیام با استفاده از ایدی گروه و کانال به ترتیب"
            "/check_config - نشان دادن تنظیمات کنونی شما"
        )
    else:
        await update.message.reply_text("شما مجاز به استفاده ی این ربات نیستید لطفا با @retrotechdeveloper در تماس باشید.")

# Command handler for the help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_authorized(user_id):
        await update.message.reply_text(
            "دستور های موجود:\n"
            "\n/help - نشان دادن این منو\n"
            "\n/register_admin \n افزودن ادمین های جدید (فقط سوپرادمین مجاز به این دستور است) "
            "\n/register_ids \n ست کردن هماهنگی ارسال پیام با استفاده از ایدی گروه و کانال به ترتیب"
            "\n/check_config \n نشان دادن تنظیمات کنونی شما"
            "\n\n\n\nطریقه ی استفاده \n"
            "ابتدا با استفاده از ربات @myidbot \n"
            " ایدی گروه و کانال خود را به ترتیب کپی کرده و با استفاده از دستور /register_ids  ربات را فعال کنید"
            "برای دیدن تنظیمات و ایدی های اد شده از دستور چک کانفیگ استفاده کنید "
            "مثال:\n\n /register_ids group_id channel id "
        )
    else:
        await update.message.reply_text("شما مجاز به استفاده ی این ربات نیستید لطفا با @retrotechdeveloper در تماس باشید.")

# Command handler for registering admins (super admin only)
async def register_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the command is sent by the super admin
    if update.effective_user.id != SUPER_ADMIN_ID:
        await update.message.reply_text("شما مجاز به استفاده ی این دستور نیستید.")
        return

    # Check if a user ID is provided
    if not context.args:
        await update.message.reply_text("Please provide a user ID to register as an admin.")
        return

    # Get the user ID to register
    new_admin_id = int(context.args[0])

    # Add the new admin to the config
    if new_admin_id not in config["admins"]:
        config["admins"].append(new_admin_id)
        save_config(config)
        await update.message.reply_text(f"Admin with ID {new_admin_id} has been registered.")
    else:
        await update.message.reply_text(f"Admin with ID {new_admin_id} is already registered.")

# Command handler for registering group and channel IDs (admin only)
async def register_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the command is sent by an admin or super admin
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("شما مجاز به استفاده ی این دستور نیستید.")
        return

    # Check if both group ID and channel ID are provided
    if len(context.args) != 2:
        await update.message.reply_text("لطفا دستور را این گونه وارد کنید  دستور ایدی گروه ایدی کانال")
        return

    # Get the group ID and channel ID
    group_id, channel_id = map(int, context.args)

    # Update the config
    config["group_id"] = group_id
    config["channel_id"] = channel_id
    config["registering_admin"] = update.effective_user.id  # Store the ID of the admin registering the IDs
    save_config(config)

    await update.message.reply_text("Group ID and Channel ID have been registered.")

async def check_bot_permissions(bot, chat_id):
    try:
        chat = await bot.get_chat(chat_id)
        bot_member = await chat.get_member(bot.id)
        permissions = []

        if chat.type == Chat.CHANNEL:
            if bot_member.status == 'administrator':
                can_post = getattr(bot_member, 'can_post_messages', None)
                permissions.append("post messages" if can_post else "cannot post messages")
            else:
                permissions.append("not an administrator (cannot post messages)")
        else:  # For groups
            if bot_member.status == 'administrator':
                permissions.append("administrator")
                permissions.append("can send messages")
                permissions.append("can read messages")
            elif bot_member.status == 'member':
                permissions.append("regular member (default group permissions apply)")
            else:
                permissions.append(f"unexpected member status: {bot_member.status}")

        return f"Bot permissions in chat {chat_id} ({chat.type}): {', '.join(permissions)}"
    except Exception as e:
        return f"Error checking permissions in chat {chat_id}: {str(e)}"

async def copy_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("copy_to_channel function called")

    if update.effective_user is None:
        logger.warning("Update received with no effective user")
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id if update.effective_chat else None

    logger.info(f"Message received from user {user_id} in chat {chat_id}")

    # Check if the message is from the admin who registered the IDs
    if user_id != config.get("registering_admin"):
        logger.info(f"Message not from the registering admin. Ignoring.")
        return

    if chat_id != config["group_id"]:
        logger.info(f"Message not in registered group. Received in {chat_id}, expected {config['group_id']}")
        return

    if not config["channel_id"]:
        logger.error("Channel ID is not set")
        return

    if not update.message:
        logger.warning("Update has no message")
        return

    logger.info(f"Attempting to send message to channel {config['channel_id']}")
    try:
        # Get the original message text
        original_text = update.message.text

        # Send the message as the bot's own message
        result = await context.bot.send_message(
            chat_id=config["channel_id"],
            text=original_text
        )
        logger.info(f"Message successfully sent to channel {config['channel_id']}")
    except Exception as e:
        logger.error(f"Error sending message to channel: {str(e)}")

    # Log the message details
    logger.info(f"Message details: {update.message.to_dict()}")

async def check_config(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("شما مجاز به استفاده ی این دستور نیستید.")
        return
    config = load_config()
    config_str = f"تنظیمات کنونی :\n"
    config_str += f"ادمین ها: {config['admins']}\n"
    config_str += f"ایدی گروه: {config['group_id']}\n"
    config_str += f"ایدی کانال: {config['channel_id']}\n"
    config_str += f"ایدی ادمین ها: {config.get('registering_admin', 'Not set')}\n"

    await update.message.reply_text(config_str)

    # Check bot permissions
    group_permissions = await check_bot_permissions(context.bot, config["group_id"])
    channel_permissions = await check_bot_permissions(context.bot, config["channel_id"])
    await update.message.reply_text(group_permissions)
    await update.message.reply_text(channel_permissions)

def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception while handling an update: {context.error}")
    logger.exception(context.error)


async def main(req: func.HttpRequest) -> func.HttpResponse:
    # Parse the incoming update
    update = Update.de_json(req.get_json(), bot)
    
    # Process the update
    await application.process_update(update)
    
    return func.HttpResponse("OK")

# Initialize the bot and application globally
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
bot = Bot(TOKEN)
application = ApplicationBuilder().token(TOKEN).build()

# Add all your handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("register_admin", register_admin))
application.add_handler(CommandHandler("register_ids", register_ids))
application.add_handler(CommandHandler("check_config", check_config))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, copy_to_channel))
application.add_error_handler(error_handler)