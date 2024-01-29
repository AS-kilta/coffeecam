import logging
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from decouple import config
from app import getImage
from functions import howto, howtolong

# Load environment variables from .env
TELEGRAM_TOKEN = config('TELEGRAM_TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

# Helper to create the caption or text (possibly based on the image or lack thereof)
def get_answer(photo_url: str) -> str :
    if photo_url != "":
        "There definitely is something!"
    else:
        return "Something's wrong, I can feel it!"

# Function to fetch photo from Tapo Camera
def fetch_tapo_photo(context: ContextTypes.DEFAULT_TYPE) -> str:
    latest = context.bot_data.get("latest-time")

    # First time calling function. Initialize latest as 25 seconds before,
    # so that a new image will be fetched.
    if latest == None:
        latest = time.time() - 25
        context.bot_data["latest-time"] = time.time()

    # Don't fetch a new image more often than every 20 seconds.
    if time.time() - latest < 20:
        return "/mnt/ramdisk/newest.jpeg"

    # If getting an image fails, don't give an old image.
    if getImage():
        context.bot_data["latest-time"] = time.time()
        return "/mnt/ramdisk/newest.jpeg"
    else:
        return ""

# Handle asking for coffee status.
async def coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption_text = "This might take a while..."
    await context.bot.send_message(chat_id=update.effective_chat.id, text=caption_text)

    photo_url = ""
    photo_url = fetch_tapo_photo(context)
    caption_text = get_answer(photo_url)

    # Send the photo to the user
    if photo_url != "":
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo_url, caption=caption_text)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=caption_text)

# Handle start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="\
I will tell you the status of the coffee machine in ASki!\n\
Available commands:\n\
 - /help See this message.\n\
 - /coffee See the coffee machine.\n\
 - /howto Things to remember when making coffee.\n\
 - /howtolong How to make coffee.")

if __name__ == '__main__':

    # Create the application
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    help_handler = CommandHandler('help', start)
    application.add_handler(help_handler)

    coffee_handler = CommandHandler('coffee', coffee)
    application.add_handler(coffee_handler)

    howto_handler = CommandHandler('howto', howto)
    application.add_handler(howto_handler)

    howtolong_handler = CommandHandler('howtolong', howtolong)
    application.add_handler(howtolong_handler)

    # Run application
    application.run_polling()
