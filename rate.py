from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
import portalocker
from telegram.ext import ContextTypes, ConversationHandler
import time
from telegram import Update
from decouple import config

DATABASE2 = config('DATABASE2')
rating_times = ['daily', 'weekly', 'all-time']
AMOUNT = range(1)
RATINGS_IN_RAM = 'ratings-in-ram'
LATEST_RATING = 'latest-rating'
# Handle rating coffee

async def start_r(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Allow only one rating per 10 minutes

    latest_rating: int = context.user_data.get(LATEST_RATING)
    if latest_rating != None and (time.time() - latest_rating) < 60*10:
        time_until = ( (latest_rating + 10*60) - time.time() ) / float(60)
        response = f'Hol\' up! Only one coffee rating every 10 minutes.. Still {time_until:.3f} minutes till the next one, go taste some coffee!'
        await update.message.reply_text(response)
        return

    # Possible replies

    reply_keyboard = [["0", "1", "2", "3", "4", "5", "/cancel"]]
    await update.message.reply_text(
        f"How would you rate the last cup of ASki's coffee you tasted?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="0-5"
        ),
    )
    return AMOUNT

# Handle user response

async def rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    raw = update.message.text

    # Amount should be convertible to int, else request amount again

    try:
        rating = int(raw)
    except:
        await update.message.reply_text("The Coffee rating should be an integer between 0-5! Try again")
        return AMOUNT

    # Amount should be between 0-5, else request amount again

    if len(raw) > 1 or rating > 5 :
        await update.message.reply_text("The Coffee rating should be an integer between 0-5! Try again.")
        return AMOUNT
    
    # Record the rating

    if rating_backend(rating, context):
        context.user_data[LATEST_RATING] = time.time()
        await update.message.reply_text("Recorded coffee rating: " + raw, ReplyKeyboardRemove())
    else:
        await update.message.reply_text("Something went wrong..", ReplyKeyboardRemove())
    return ConversationHandler.END

# Handle storing the ratings

def rating_backend(rating: int, context: ContextTypes.DEFAULT_TYPE, clear_day = False, clear_week = False) -> bool:

    # If this is the first time recording a rating per bot lifetime, read them from disk

    if not context.bot_data.get(RATINGS_IN_RAM, False):
        read_ratings_from_disk(context)
        context.bot_data[RATINGS_IN_RAM] = True

    # Get Ratings from bot data

    ratings = []
    for time in rating_times:
        points = context.bot_data.get(f'total-{time}', 0)
        count = context.bot_data.get(f'n-{time}', 0)

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
    
# Helper to clear Daily rating

def clear_daily(context: ContextTypes.DEFAULT_TYPE):
    rating_backend(0, context, True)
    pass

# Helper to clear Weekly rating

def clear_weekly(context: ContextTypes.DEFAULT_TYPE):
    rating_backend(0, context, False, True)
    pass

# Read ratings from disk Should be used only once per bot lifetime

def read_ratings_from_disk(context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:

        # Lock the input file in read mode

        with portalocker.Lock(DATABASE2, 'r') as input_file:

            # Read the content of the input file

            file_content = input_file.read().split()
            print(file_content)

            if len(file_content) != 6:
                return False

            # HARDCODED file structure

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


# Give ratings

async def get_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Calculate and give ratings

    if not context.bot_data.get(RATINGS_IN_RAM, False):
        if not read_ratings_from_disk(context):
            await update.message.reply_text("There are no ratings for ASki's coffee, get to tasting")
            return
        else:
            context.bot_data[RATINGS_IN_RAM] = True
    
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

    await update.message.reply_text(f'Current coffee ratings:\n\
Today\'s average:\n\
                    - {avg[0]:.2f}     (count: {ratings[1]})\n\
Weekly average:\n\
                    - {avg[1]:.2f}     (count: {ratings[3]})\n\
All-time average:\n\
                    - {avg[2]:.4f} (count: {ratings[5]})')
    return