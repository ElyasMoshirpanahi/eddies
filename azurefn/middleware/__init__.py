import logging
import azure.functions as func
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import json
import os
from azure.storage.blob import BlobServiceClient

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SUPER_ADMIN_ID = int(os.environ["SUPER_ADMIN_ID"])
# STORAGE_CONNECTION_STRING = os.environ["AzureWebJobsStorage"]
# CONTAINER_NAME = "bot-config"
MAIN_FILE   = "bot_config.json"
CONFIG_FILE = "/tmp/bot_config.json"



os.system(f"cp {MAIN_FILE} {CONFIG_FILE}")
# Blob Storage functions
# def get_blob_service_client():
#     return BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)

def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"admins": [], "group_id": None, "channel_id": None}

# Save configuration to file
def save_config(config):
    with open(CONFIG_FILE, "a") as file:
        json.dump(config, file)


# Helper function
def is_authorized(user_id):
    config = load_config()
    return user_id == SUPER_ADMIN_ID or user_id in config["admins"]

# Command handlers
async def start(update: Update, context):
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

async def help_command(update: Update, context):
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

async def register_admin(update: Update, context):
    if update.effective_user.id != SUPER_ADMIN_ID:
        await update.message.reply_text("شما مجاز به استفاده ی این دستور نیستید.")
        return

    if not context.args:
        await update.message.reply_text("Please provide a user ID to register as an admin.")
        return

    new_admin_id = int(context.args[0])
    config = load_config()

    if new_admin_id not in config["admins"]:
        config["admins"].append(new_admin_id)
        save_config(config)
        await update.message.reply_text(f"Admin with ID {new_admin_id} has been registered.")
    else:
        await update.message.reply_text(f"Admin with ID {new_admin_id} is already registered.")

async def register_ids(update: Update, context):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("شما مجاز به استفاده ی این دستور نیستید.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("لطفا دستور را این گونه وارد کنید  دستور ایدی گروه ایدی کانال")
        return

    group_id, channel_id = map(int, context.args)
    config = load_config()
    config["group_id"] = group_id
    config["channel_id"] = channel_id
    config["registering_admin"] = update.effective_user.id
    save_config(config)

    await update.message.reply_text("Group ID and Channel ID have been registered.")

async def check_config(update: Update, context):
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

async def copy_to_channel(update: Update, context):
    config = load_config()
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id != config.get("registering_admin") or chat_id != config["group_id"]:
        return

    if not config["channel_id"] or not update.message:
        return

    try:
        original_text = update.message.text
        await context.bot.send_message(
            chat_id=config["channel_id"],
            text=original_text
        )
        logger.info(f"Message successfully sent to channel {config['channel_id']}")
    except Exception as e:
        logger.error(f"Error sending message to channel: {str(e)}")

async def error_handler(update: object, context):
    logger.error(f"Exception while handling an update: {context.error}")

async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Entrypoint for Azure Function"""
    logger.info('Python HTTP trigger function processed a request.')

    # Initialize bot and application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("register_admin", register_admin))
    application.add_handler(CommandHandler("register_ids", register_ids))
    application.add_handler(CommandHandler("check_config", check_config))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, copy_to_channel))
    application.add_error_handler(error_handler)

    # Process update
    try:
        update = Update.de_json(req.get_json(), application.bot)
        await application.initialize()
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Error processing update: {str(e)}")
        return func.HttpResponse("Error", status_code=500)

    return func.HttpResponse("OK")

# Azure Functions entry point
def azure_function_handler(req: func.HttpRequest) -> func.HttpResponse:
    return func.AsgiMiddleware(main).handle(req)
