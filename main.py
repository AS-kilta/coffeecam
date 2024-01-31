import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from decouple import config
from functions import howto, howtolong, coffee
import time
from random import randrange
import portalocker

# Load environment variables from .env
TELEGRAM_TOKEN = config('TELEGRAM_TOKEN')
ADMIN_PASSWD = config('ADMIN_PASSWD')
THOUGHTS = config('THOUGHTS')
DATABASE = config('DATABASE')

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

# Handle inserting a coffee thought
async def insert_thought(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    message_content = update.message.text
    if message_content == None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Something went wrong!")

    content = message_content.split(';')
    if len(content) != 2:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="This method can be used to insert a /coffeethought.\nUsage: /insertthought ;<your quote or thought that may or may not have something to do with coffee>")
        return
    thought = content[1]

    if len(thought) < 10:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Your thought should be at least 10 characters long")
        return

    latest_thought: int = context.user_data.get("latest-thought")
    if latest_thought != None and (time.time() - latest_thought) < 60*60*2:
        time_until = ( (latest_thought + 60*60*2) - time.time() ) / float(60)
        response = f'Hol\' up! Only one coffee thought every 2 hours.. Still {time_until:.3f} minutes till the next one, go drink some coffee!'
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
        return

    with portalocker.Lock(THOUGHTS, 'r+') as output_file:
        portalocker.lock(output_file, portalocker.LOCK_EX)
        output_file.write(thought)
        with portalocker.Lock(DATABASE, 'r+') as db_file:
            db_file.write(thought + "\n")
            context.user_data["latest-thought"] = time.time()
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Added '" + thought + "' as a coffeethought.")

# Handle giving a random coffee thought
async def coffee_thought(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with portalocker.Lock(THOUGHTS, 'r') as output_file:
        lines = output_file.readlines()
        length = len(lines)
        if length < 1:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="There don't seem to be any coffee thoughts? Get to writing with /insertthought")

        index = randrange(0, length, 1)
        thought = lines[index]
        await context.bot.send_message(chat_id=update.effective_chat.id, text=thought)

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
 - /howtolong How to make coffee.\n\
 - /insertthought Insert a coffee thought.\n\
 - /coffeethought Randomly give one coffee thought.")

# Initialize and run the bot
if __name__ == '__main__':

    # Create the application
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    try:
        file_content = ""
        # portalocker.Lock the input file in read mode
        with portalocker.Lock(DATABASE, 'r') as input_file:
            # Read the content of the input file
            file_content = input_file.read()

        # portalocker.Lock the output file in write mode
        with portalocker.Lock(THOUGHTS, 'w+') as output_file:
            # Write the content to the output file
            output_file.write(file_content)

        print(f"Content successfully copied from {DATABASE} to {THOUGHTS}")

    except FileNotFoundError:
        print(f"Error: The file at {DATABASE} was not found.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

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

    gt_handler = CommandHandler("insertthought", insert_thought)
    application.add_handler(gt_handler)

    ct_handler = CommandHandler("coffeethought", coffee_thought)
    application.add_handler(ct_handler)

    # Run application
    application.run_polling()
