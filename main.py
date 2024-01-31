import logging
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from decouple import config
from app import getImage
from functions import howto, howtolong

# Load environment variables from .env
TELEGRAM_TOKEN = config('TELEGRAM_TOKEN')
ADMIN_PASSWD = config('ADMIN_PASSWD')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

# Admin functions, these functions are not given to the general user. (security through obscurity)

# Admin help
async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="\
These are the admin commands:\n\
 - /adminhelp see this text.\n\
 - /givemessage <password>;<general-message>\n\
 - /clearmessage <password>\n\
Givemessage is used to give a general info message that is displayed to users when using /coffee.\n\
Clearmessage clears this message")

# Clear general message
async def clear_general_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_content = update.message.text
    if (message_content == None) or (not ADMIN_PASSWD in message_content):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="This method clears the general info message to display to users.\nUsage: /clearmessage <password>")
        return

    context.bot_data["general-message"] = ""
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Cleared the general message")
    return

# Give general message
async def give_general_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_content = update.message.text
    if (message_content == None) or (not ADMIN_PASSWD in message_content):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You shouldn't be here!")
        return

    content = message_content.split(";")
    if len(content) != 2:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="This method gives a general info message to display to users.\nUsage: /givemessage <password>;<message here>")

    context.bot_data["general-message"] = content[1]
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Added '" + content[1] + "' as the general message.")
    return

# User functions

# Helper to create the caption or text (possibly based on the image or lack thereof)
def get_answer(photo_url: str) -> str :
    if photo_url != "":
        "There definitely is something!"
    else:
        return "Something's wrong, I can feel it!"

# Function to fetch photo from Tapo Camera
async def fetch_tapo_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    latest = context.bot_data.get("latest-time")

    # First time calling function. Initialize latest as 25 seconds before,
    # so that a new image will be fetched.
    if latest == None:
        latest = time.time() - 25
        context.bot_data["latest-time"] = time.time()

    # Don't fetch a new image more often than every 20 seconds.
    if time.time() - latest < 20:
        return "/mnt/ramdisk/newest.jpeg"

    caption_text = "This might take a while..."
    await context.bot.send_message(chat_id=update.effective_chat.id, text=caption_text)

    # If getting an image fails, don't give an old image.
    if getImage():
        context.bot_data["latest-time"] = time.time()
        return "/mnt/ramdisk/newest.jpeg"
    else:
        return ""

# Handle asking for coffee status.
async def coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):

    photo_url = ""
    caption_text = "Something went wrong.."
    photo_url = await fetch_tapo_photo(update, context)
    #caption_text = get_answer(photo_url)
    general_message = context.bot_data.get("general-message")
    if (general_message != None) or (general_message == ""):
        caption_text = context.bot_data.get("general-message")

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

    gm_handler = CommandHandler("givemessage", give_general_message)
    application.add_handler(gm_handler)

    cm_handler = CommandHandler("clearmessage", clear_general_message)
    application.add_handler(cm_handler)

    ahelp_handler = CommandHandler("adminhelp", admin_help)
    application.add_handler(ahelp_handler)

    # Run application
    application.run_polling()
