
import time
from telegram import Update
from telegram.ext import ContextTypes
from app import getImage

# This file contains functions that prob. don't need to be edited.

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

    caption_text = "This will take a few seconds..."
    await context.bot.send_message(chat_id=update.effective_chat.id, text=caption_text)

    # If getting an image fails, don't give an old image.

    if getImage():
        context.bot_data["latest-time"] = time.time()
        return "/mnt/ramdisk/newest.jpeg"
    else:
        return ""

# Handle asking for coffee status.

async def coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Fetch image

    photo_url = ""
    photo_url = await fetch_tapo_photo(update, context)

    # Give general message

    general_message = context.bot_data.get("general-message", "")
    if general_message != "":
        caption_text = context.bot_data.get("general-message")

    # Overwrite general message, if no photo

    if photo_url == "":
        caption_text = "Sorry, I wasn't able to get an image :/"

    # Send the photo to the user

    if photo_url != "":
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo_url, caption=caption_text)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=caption_text)

# Quick tips to remember when making coffee in ASki.

async def howto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Have you used a coffee machine before? If not, maybe read /howtolong :)\n\n\
 - The smaller measure is one cup, while the larger is two cups.\n\
 - Please pour the water into the machine with a separate jug, as the coffee pot is usually not quite clean.\n\
 - If there are other people in ASki, remember to ask, if they would like some coffee as well!\n\
 - Lastly, remember to open the drip lock!")

# How to make coffee with a coffee machine.

async def howtolong(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Have you used a coffee machine before? If yes, /howto might be enough :D\n\n\
Instructions for Making Coffee with a Moccamaster Coffee Machine:\n\
What You'll Need:\n\
\n\
  - Moccamaster coffee machine\n\
  - Pre-ground coffee\n\
  - Water\n\
  - Coffee filter\n\
  - Coffee mug\n\
\n\
Steps:\n\
  0. Prepare to prepare coffee:\n\
    Prepare yourself mentally for the process!\n\
    If it sounds straining, remember that you will get to enjoy coffee later!\n\
\n\
  1. Prepare the Coffee Filter:\n\
    Open the coffee filter compartment on your Moccamaster.\n\
    Place a paper coffee filter in the basket. Make sure it fits snugly.\n\
\n\
  2. Add Pre-Ground Coffee to the Filter:\n\
    Measure the appropriate amount of pre-ground coffee based on the desired amount of coffee.\n\
    Remember, that the smaller scoop is one cup, while the bigger scoop is two cups!\n\
    Add the measured pre-ground coffee to the coffee filter.\n\
\n\
  3. Fill the Water Tank:\n\
    Open the water tank lid on the top of the coffee machine.\n\
    Fill the water tank with cold, clean water. The water level should match the desired number of cups you want to brew.\n\
\n\
  4. Position the Coffee Carafe:\n\
    Place the coffee carafe or pot on the warming plate beneath the coffee filter.\n\
\n\
  5. Start the Brewing Process:\n\
    Turn on the Moccamaster by pressing the power switch.\n\
    The machine will start brewing the coffee. The water will heat up and drip over the pre-ground coffee, extracting the flavors.\n\
    Remember to open the drip lock!\n\
\n\
  6. Wait for Brewing to Complete:\n\
    Allow the machine to complete the brewing process. This usually takes a few minutes.\n\
\n\
  7. Serve and Enjoy:\n\
    Once the brewing is complete, carefully remove the coffee carafe from the warming plate.\n\
    Pour the freshly brewed coffee into your mug.\n\
\n\
  8. Clean Up:\n\
    Turn off the Moccamaster.\n\
    Discard the used coffee filter.\n\
    Rinse the coffee carafe and other removable parts with warm water.\n\
\n\
  9. Optional Additions:\n\
    Customize your coffee with sugar, milk, or any other additions based on personal preference.")
