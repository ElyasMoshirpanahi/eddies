import logging
import azure.functions as func
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Define a few command handlers
async def start(update: Update, context):
    await update.message.reply_text('Hello! I am a simple bot.')

async def echo(update: Update, context):
    await update.message.reply_text(update.message.text)

async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Entrypoint for Azure Function"""
    logger.info('Python HTTP trigger function processed a request.')

    # Initialize bot and application

    # Configuration
    TOKEN = "6385990167:AAHTRuFOBTKX4vgmBkj6uI8CNFCgW7mO0dw"
    SUPER_ADMIN_ID = 80741935  # Replace with the actual super admin's user ID
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

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
