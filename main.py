import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from decouple import config

# Load environment variables from .env
TELEGRAM_TOKEN = config('TELEGRAM_TOKEN')
TAPO_USERNAME = config('TAPO_USERNAME')
TAPO_PASSWORD = config('TAPO_PASSWORD')

# Tapo Camera API endpoint
TAPO_API_URL = 'http://tapo_camera_ip/api'

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Helper to create the caption or text (possibly based on the image or lack thereof)
def get_answer():

    # Fetch photo from Tapo Camera
    return "Idk, go check yourself \":D\""

# Function to fetch photo from Tapo Camera
def fetch_tapo_photo():
    # Implement logic to authenticate and fetch photo from Tapo Camera API
    # Use TAPO_API_URL, TAPO_USERNAME, and TAPO_PASSWORD
    # Example: photo_url = requests.get(api_url).json()['photo_url']
    return ""

async def coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    photo_url = fetch_tapo_photo()
    caption_text = get_answer()
    
    # Send the photo to the user
    if photo_url != "":
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo_url, caption=caption_text)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=caption_text)

# Handle start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="I will tell you the status of the Coffee machine in ASki with the command /coffee")

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
