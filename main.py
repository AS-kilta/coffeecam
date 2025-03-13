import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler, MessageHandler
from decouple import config
from functions import howto, howtolong, coffee
from coffeeReq import start_c, amount, cancel, request_coffee, cancel_request, make_timeout
from rate import clear_daily, clear_weekly, start_r, get_rating, rating, rate_timeout
import time
from random import randrange, seed
import portalocker
import datetime
import telegram.ext.filters as filters
import aiohttp
import asyncio
import json

AMOUNT = range(1)

# Load environment variables from .env

TELEGRAM_TOKEN = config('TELEGRAM_TOKEN')
ADMIN_PASSWD = config('ADMIN_PASSWD')
STORE = config('STORE')
DATABASE = config('DATABASE')

GENERAL_MESSAGE = 'general-message'
LATEST_QUOTE = 'latest-quote'

OLLAMA_URL = config('OLLAMA_URL')

# Enable logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

# Admin functions, these functions are not given to the general user. (security through obscurity)

# Admin help

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\
These are the admin commands:\n\
 - /adminhelp see this text.\n\
 - /givemessage <password> <general-message>\n\
 - /clearmessage <password>\n\
Givemessage is used to give a general info message that is displayed to users when using /coffee.\n\
Clearmessage clears this message")

# Clear general message

async def clear_general_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_content = update.message.text

    # Require password in message

    if (message_content == None) or (not ADMIN_PASSWD in message_content):
        await update.message.reply_text("This command clears the general info message to display to users.\nUsage: /clearmessage <password>")
        return

    # Clear message and tell it in message.

    context.bot_data[GENERAL_MESSAGE] = ""
    await update.message.reply_text("Cleared the general message")
    return

# Give general message

async def give_general_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Require password

    message_content = update.message.text
    if (message_content == None) or not(ADMIN_PASSWD in message_content):
        await update.message.reply_text("You shouldn't be here!")
        return

    # Require a valid message

    content = message_content.split(' ')
    if len(content) <= 2:
        await update.message.reply_text("This command gives a general info message to display to users.\nUsage: /givemessage <password> <message here>")

    # If second word in message is not password, then the password would be in the info message.

    if content[1] != ADMIN_PASSWD:
        await update.message.reply_text("Usage: /givemessage <password> <message here>")
        return

    # Change message and tell it in message.

    context.bot_data[GENERAL_MESSAGE] = " ".join(content[2:])
    await update.message.reply_text("Added '" + " ".join(content[2:]) + "' as the general message.")
    return

# User functions

# Handle inserting a coffee quote

async def insert_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Message should contain something

    message_content = update.message.text
    if message_content == None:
        await update.message.reply_text("Something went wrong!")
        return

    # Message should have at least the command and one other word

    content = message_content.split()
    if len(content) < 2:
        await update.message.reply_text("This command can be used to insert a /quote.\nUsage: /addq <your quote or thought that may or may not have something to do with coffee>")
        return

    # Join rest of the message as the quote, quote should be at least 10 chars long

    quote = " ".join(content[1:])
    if len(quote) < 10:
        await update.message.reply_text("Your quote should be at least 10 characters long")
        return
    
    if "movie" in quote.lower() and "bee" in quote.lower() and "script" in quote.lower():
        await update.message.reply_text("Bro I'm not putting the Bee Movie script in here")
        return
    
    if len(quote) > 200:
        await update.message.reply_text("Your quote should be at most 200 characters long")
        return

    # Allow only one quote per 2 hours

    latest_quote: int = context.user_data.get(LATEST_QUOTE)
    if latest_quote != None and (time.time() - latest_quote) < 60*60*2:
        time_until = ( (latest_quote + 60*60*2) - time.time() ) / float(60)
        response = f'Hol\' up! Only one coffee quote every 2 hours.. Still {time_until:.2f} minutes till the next one, go drink some coffee!'
        await update.message.reply_text(response)
        return

    # Aquire a lock for both the temp file in ram, and the persistent file in disk, and write it there

    try:
        with portalocker.Lock(STORE, 'a') as output_file:
            portalocker.lock(output_file, portalocker.LOCK_EX)
            output_file.write(quote)
            with portalocker.Lock(DATABASE, 'a') as db_file:
                db_file.write(quote + "\n")
                context.user_data[LATEST_QUOTE] = time.time()
                await update.message.reply_text("Added '" + quote + "' as a quote.")
    except:
        await update.message.reply_text("Something went wrong...")

# Handle giving a random coffee quote

async def coffee_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with portalocker.Lock(STORE, 'r') as output_file:
            lines = output_file.readlines()
            length = len(lines)

            # File was empty

            if length < 1:
                await update.message.reply_text("There don't seem to be any coffee quotes? Get to writing with /addq")
                return

            # Randomize a single quote

            seed(time.process_time())
            index = randrange(0, length, 1)
            quote = lines[index]
            await update.message.reply_text(quote)
    except:
        await update.message.reply_text("Something went really wrong..")

# Handle start command

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\
I will tell you the status of the coffee machine in ASki!\n\
Available commands:\n\
 - /help See this message.\n\
 - /coffee See the coffee machine.\n\
 - /request Request coffee (expires in 15 mins)\n\
 - /cancelrequest Cancel request\n\
 - /make Make coffee.\n\
 - /rate Rate ASki's coffee.\n\
 - /rating See the rating stats of ASki's coffee.\n\
 - /howTo Things to remember when making coffee.\n\
 - /howToLong How to make coffee.\n\
 - /addq Insert a coffee quote.\n\
 - /q Randomly give one coffee quote.\n\
 - /aiq Get a coffee quote from the ASki LLM.")

def read_persistent_to_ram(disk_path: str, ram_path: str):
    try:
        file_content = ""

        # Lock the input file in read mode

        with portalocker.Lock(disk_path, 'r') as input_file:

            # Read the content of the input file

            file_content = input_file.read()

        # Lock the output file in write mode

        with portalocker.Lock(ram_path, 'w+') as output_file:

            # Write the content to the output file

            output_file.write(file_content)

        print(f"Content successfully copied from {disk_path} to {ram_path}")

    except FileNotFoundError:
        print(f"Error: The file at {disk_path} was not found.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

async def ai_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Define the payload
    prompt = "These are the coffee quotes so far in ASki:\n\n"

    try:
        with portalocker.Lock(STORE, 'r') as output_file:
            lines = output_file.readlines()
            prompt += "\n".join(lines)
    except:
        print("ei oo filee")
        prompt += "No coffee quotes so far in ASki."

    prompt += "Finally, here is current time to randomize your input a bit more " + str(time.time()) + "\n"

    data = {
        "model": "aski-llm",
        "prompt": prompt,
        "stream": False  # Set to True for streaming response
    }

    timeout = aiohttp.ClientTimeout(total=60)  # 60 seconds timeout

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try: 
            caption_text = "This might take up to a minute.."
            await context.bot.send_message(chat_id=update.effective_chat.id, text=caption_text)

            async with session.post(OLLAMA_URL, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    await update.message.reply_text(result["response"])
                    print("resp:", result["response"])
                else:
                    await update.message.reply_text("The AI seems to be sleeping..")
        except asyncio.TimeoutError:
            await update.message.reply_text("The AI was too slow..")

# Timeout a conversation, and remove possible keyboard

def timeout(update, context):
    update.message.reply_text('timeout reached, hope to see you next time',reply_markup=ReplyKeyboardRemove())

# Initialize and run the bot

if __name__ == '__main__':

    # Create the application

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Read ratings and quotes to ram

    read_persistent_to_ram(DATABASE, STORE)
    
    # Add periodically running jobs to clear daily and weekly ratings
    # Daily is cleared every day at 3 am UTC, weekly is cleared every week on Monday at 3 am UTC

    time_to_clear = datetime.time(hour=3, minute=0)
    application.job_queue.run_daily(clear_daily, time_to_clear)
    application.job_queue.run_daily(clear_weekly, time_to_clear, days=[0])

    # Gather handlers in a list
    handlers = []

    handlers.append(CommandHandler('start', start))

    handlers.append(CommandHandler('help', start))

    handlers.append(CommandHandler('coffee', coffee))

    handlers.append(CommandHandler('howto', howto))

    handlers.append(CommandHandler('howtolong', howtolong))

    handlers.append(CommandHandler("givemessage", give_general_message))

    handlers.append(CommandHandler("clearmessage", clear_general_message))

    handlers.append(CommandHandler("adminhelp", admin_help))

    handlers.append(CommandHandler("addq", insert_quote))

    handlers.append(CommandHandler("q", coffee_quote))

    handlers.append(CommandHandler("quote", coffee_quote))

    handlers.append(CommandHandler("rating", get_rating))

    handlers.append(CommandHandler("request", request_coffee))

    handlers.append(CommandHandler("cancelRequest", cancel_request))

    handlers.append(CommandHandler("aiq", ai_quote))

    # Conversation handler for making coffee

    handlers.append(ConversationHandler(
        entry_points=[CommandHandler("make", start_c)],
        states={
            AMOUNT: [MessageHandler( ~filters.COMMAND & filters.TEXT, amount)],
            ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL, make_timeout)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=60
        )
    )

    # Conversation handler for rating coffee

    handlers.append(ConversationHandler(
        entry_points=[CommandHandler("rate", start_r)],
        states={
            AMOUNT: [MessageHandler( ~filters.COMMAND & filters.TEXT, rating)],
            ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL, rate_timeout)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=60
        )
    )

    # Add the handlers

    application.add_handlers(handlers)

    # Run application
    application.run_polling()
