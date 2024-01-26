import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from decouple import config
from app import getImage

# Load environment variables from .env
TELEGRAM_TOKEN = config('TELEGRAM_TOKEN')
TAPO_USERNAME = config('TAPO_USERNAME')
TAPO_PASSWORD = config('TAPO_PASSWORD')
TAPO_IP = "192.168.1.45" # Static IP given in Edgerouter

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

# Helper to create the caption or text (possibly based on the image or lack thereof)
def get_answer(photo_url: str):
    if photo_url != "":
        "There definitely is something!"
    else:
        return "Idk, go check yourself \":D\""

# Function to fetch photo from Tapo Camera
async def fetch_tapo_photo():
    getImage()
    return "pic1.jpeg"

async def coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):

    photo_url = await fetch_tapo_photo()
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
                        text="I will tell you the status of the coffee machine in ASki with the command /coffee")

if __name__ == '__main__':

    # Create the application
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    coffee_handler = CommandHandler('coffee', coffee)
    application.add_handler(coffee_handler)

    # Daemonize
    application.run_polling()
