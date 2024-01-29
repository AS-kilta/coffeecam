
from telegram import Update
from telegram.ext import ContextTypes

# This file contains functions that prob. don't need to be edited.

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
