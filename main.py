import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from decouple import config
from functions import howto, howtolong, coffee
import time
from random import randrange, seed
import portalocker
import datetime

# Load environment variables from .env
TELEGRAM_TOKEN = config('TELEGRAM_TOKEN')
ADMIN_PASSWD = config('ADMIN_PASSWD')
STORE = config('STORE')
DATABASE = config('DATABASE')
DATABASE2 = config('DATABASE2')
rating_times = ['daily', 'weekly', 'all-time']

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
 - /givemessage <password> <general-message>\n\
 - /clearmessage <password>\n\
Givemessage is used to give a general info message that is displayed to users when using /coffee.\n\
Clearmessage clears this message")

# Clear general message
async def clear_general_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_content = update.message.text

    # Require password in message
    if (message_content == None) or (not ADMIN_PASSWD in message_content):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="This method clears the general info message to display to users.\nUsage: /clearmessage <password>")
        return

    # Clear message and tell it in message.
    context.bot_data["general-message"] = ""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Cleared the general message")
    return

# Give general message
async def give_general_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Require password
    message_content = update.message.text
    if (message_content == None) or not(ADMIN_PASSWD in message_content):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You shouldn't be here!")
        return

    # Require a valid message
    content = message_content.split(' ')
    if len(content) <= 2:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="This method gives a general info message to display to users.\nUsage: /givemessage <password> <message here>")

    # If second word in message is not password, then the password would be in the info message.
    if content[1] != ADMIN_PASSWD:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /givemessage <password> <message here>")
        return

    # Change message and tell it in message.
    context.bot_data["general-message"] = " ".join(content[2:])
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Added '" + " ".join(content[2:]) + "' as the general message.")
    return

# User functions

# Handle rating coffee
async def rate_coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Message should contain something
    message_content = update.message.text
    if message_content == None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Something went wrong!")
        return

    # Message should have precisely the command and a single digit integer 0-5
    content = message_content.split(' ')
    if len(content) != 2:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="This method can be used to insert a coffee /rating.\nUsage: /rate <rating of ASki's coffee from 0 to 5 as an integer>")
        return

    # Rest of the message is the rating, it should be convertible to Int.
    raw = content[1]
    try:
        rating = int(raw)
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Your coffee rating should be a single digit integer between 0-5!")
        return
        
    if len(raw) > 1 or rating > 5:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Your coffee rating should be a single digit integer between 0-5!")

    # Allow only one rating per 10 minutes
    latest_rating: int = context.user_data.get("latest-rating")
    if latest_rating != None and (time.time() - latest_rating) < 60*10:
        time_until = ( (latest_rating + 10*60) - time.time() ) / float(60)
        response = f'Hol\' up! Only one coffee rating every 10 minutes.. Still {time_until:.3f} minutes till the next one, go taste some coffee!'
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
        return
    
    # Record the rating
    if rating_backend(rating, context):
        context.user_data["latest-rating"] = time.time()
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Recorded coffee rating: " + raw)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Something went wrong..")

# Handle storing the ratings
def rating_backend(rating: int, context: ContextTypes.DEFAULT_TYPE, clear_day = False, clear_week = False) -> bool:
    # If this is the first time recording a rating per bot lifetime, read them from disk
    if context.bot_data.get("ratings-in-ram") is None:
        read_ratings_from_disk(context)
        context.bot_data["ratings-in-ram"] = True

    # Get Ratings from bot data
    ratings = []
    for time in rating_times:
        points = context.bot_data.get(f'total-{time}')
        count = context.bot_data.get(f'n-{time}')

        # First time, init
        if points is None or count is None:
            context.bot_data[f'total-{time}'] = rating
            context.bot_data[f'n-{time}'] = 1
        # Add rating and increment count
        else:
            if clear_day and time == 'daily':
                context.bot_data[f'total-{time}'] = 0
                context.bot_data[f'n-{time}'] = 0
            elif clear_week and time == 'weekly':
                context.bot_data[f'total-{time}'] = 0
                context.bot_data[f'n-{time}'] = 0
            elif clear_day or clear_week:
                pass
            else:
                context.bot_data[f'total-{time}'] += rating
                context.bot_data[f'n-{time}'] += 1
 
        ratings.append(context.bot_data[f'total-{time}'])
        ratings.append(context.bot_data[f'n-{time}'])

    # Write the rating data to DB
    try:
        with portalocker.Lock(DATABASE2, 'w') as db_file:
            for line in ratings:
                db_file.write("%d\n" % line)
            return True
    except:
        return False
    
def clear_daily(context: ContextTypes.DEFAULT_TYPE):
    rating_backend(0, context, True)
    pass

def clear_weekly(context: ContextTypes.DEFAULT_TYPE):
    rating_backend(0, context, False, True)
    pass

def read_ratings_from_disk(context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        # portalocker.Lock the input file in read mode
        with portalocker.Lock(DATABASE2, 'r') as input_file:
            # Read the content of the input file
            file_content = input_file.read().split()
            print(file_content)

            if len(file_content) != 6:
                return False
            context.bot_data[f'total-{rating_times[0]}'] = int(file_content[0])
            context.bot_data[f'n-{rating_times[0]}'] = int(file_content[1])

            context.bot_data[f'total-{rating_times[1]}'] = int(file_content[2])
            context.bot_data[f'n-{rating_times[1]}'] = int(file_content[3])

            context.bot_data[f'total-{rating_times[2]}'] = int(file_content[4])
            context.bot_data[f'n-{rating_times[2]}'] = int(file_content[5])

            return True

    except:
        print(f"Error: The file was not found.")
    return False

# Handle rating coffee
async def get_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Calculate and give ratings
    if context.bot_data.get("ratings-in-ram") is None:
        if not read_ratings_from_disk(context):
            await context.bot.send_message(chat_id=update.effective_chat.id, text="There are no ratings for ASki's coffee, get to tasting")
            return
        else:
            context.bot_data["ratings-in-ram"] = True
    
    ratings = []
    for time in rating_times:
        ratings.append(context.bot_data[f'total-{time}'])
        ratings.append(context.bot_data[f'n-{time}'])

    # Calculate ratings
    avg = []
    for i in range(0, len(ratings), 2):
        if ratings[i + 1] == 0:
            avg.append(0)
        else:
            avg.append(ratings[i] / ratings[i + 1])

    # Give ratings to user
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Current coffee ratings:\n\
Today\'s average:\n\
        - {avg[0]:.2f}     (count: {ratings[1]})\n\
Weekly average:\n\
        - {avg[1]:.2f}     (count: {ratings[3]})\n\
All-time average:\n\
        - {avg[2]:.4f} (count: {ratings[5]})')

# Handle inserting a coffee quote
async def insert_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Message should contain something
    message_content = update.message.text
    if message_content == None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Something went wrong!")
        return

    # Message should have at least the command and one other word
    content = message_content.split(' ')
    if len(content) < 2:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="This method can be used to insert a /quote.\nUsage: /addq <your quote or thought that may or may not have something to do with coffee>")
        return

    # Join rest of the message as the quote, quote should be at least 10 chars long
    quote = " ".join(content[1:])
    if len(quote) < 10:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Your quote should be at least 10 characters long")
        return

    # Allow only one quote per 2 hours
    latest_quote: int = context.user_data.get("latest-quote")
    if latest_quote != None and (time.time() - latest_quote) < 60*60*2:
        time_until = ( (latest_quote + 60*60*2) - time.time() ) / float(60)
        response = f'Hol\' up! Only one coffee quote every 2 hours.. Still {time_until:.3f} minutes till the next one, go drink some coffee!'
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
        return

    # Aquire a lock for both the temp file in ram, and the persistent file in disk, and write it there
    try:
        with portalocker.Lock(STORE, 'a') as output_file:
            portalocker.lock(output_file, portalocker.LOCK_EX)
            output_file.write(quote)
            with portalocker.Lock(DATABASE, 'a') as db_file:
                db_file.write(quote + "\n")
                context.user_data["latest-quote"] = time.time()
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Added '" + quote + "' as a quote.")
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Something went wrong...")

# Handle giving a random coffee quote
async def coffee_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with portalocker.Lock(STORE, 'r') as output_file:
            lines = output_file.readlines()
            length = len(lines)

            # File was empty
            if length < 1:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="There don't seem to be any coffee quotes? Get to writing with /addq")

            # Randomize a single quote
            seed(time.process_time())
            index = randrange(0, length, 1)
            quote = lines[index]
            await context.bot.send_message(chat_id=update.effective_chat.id, text=quote)
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Something went really wrong..")

# Handle start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="\
I will tell you the status of the coffee machine in ASki!\n\
Available commands:\n\
 - /help See this message.\n\
 - /coffee See the coffee machine.\n\
 - /rate Rate ASki's coffee.\n\
 - /rating See the rating stats of ASki's coffee.\n\
 - /howto Things to remember when making coffee.\n\
 - /howtolong How to make coffee.\n\
 - /addq Insert a coffee quote.\n\
 - /q Randomly give one coffee quote.")

def read_persistent_to_ram(disk_path: str, ram_path: str):
    try:
        file_content = ""
        # portalocker.Lock the input file in read mode
        with portalocker.Lock(disk_path, 'r') as input_file:
            # Read the content of the input file
            file_content = input_file.read()

        # portalocker.Lock the output file in write mode
        with portalocker.Lock(ram_path, 'w+') as output_file:
            # Write the content to the output file
            output_file.write(file_content)

        print(f"Content successfully copied from {disk_path} to {ram_path}")

    except FileNotFoundError:
        print(f"Error: The file at {disk_path} was not found.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

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

    gt_handler = CommandHandler("addq", insert_quote)
    application.add_handler(gt_handler)

    ct_handler = CommandHandler("q", coffee_quote)
    application.add_handler(ct_handler)

    rating_handler = CommandHandler("rating", get_rating)
    application.add_handler(rating_handler)

    rate_handler = CommandHandler("rate", rate_coffee)
    application.add_handler(rate_handler)

    # Run application
    application.run_polling()
