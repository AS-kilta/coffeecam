from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler
import time
from telegram import Update

AMOUNT = range(1)
QUEUE = 'queue'
MAKING_COFFEE = 'making-coffee'
LATEST_REQUEST = 'latest-request'

# Functions related to the coffee queue

# Handle requesting coffee

async def request_coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Allow only one request per 15 minutes (This is also the request lifetime)

    if has_pending_request(context):
        latest_request = context.user_data.get(LATEST_REQUEST)
        time_until = ( (latest_request + 15*60) - time.time() ) / float(60)
        response = f'Hol\' up! Only one coffee request every 15 minutes.. Your last request is still valid for {time_until:.3f} minutes! If you made it by accident, you can /cancelrequest'
        await update.message.reply_text(response)
        return
 
    context.user_data[LATEST_REQUEST] = time.time()
    all = context.bot_data.get(QUEUE, [])

    # Requests have: (User id, chat id, message id, expiry time)

    all.append((update.effective_user.id, update.effective_chat.id, update.effective_message.id, time.time() + 60*15))
    context.bot_data[QUEUE] = all

    await update.message.reply_text("Coffee request counted!")
    pass

# Helper to check if user has a pending request

def has_pending_request(context: ContextTypes.DEFAULT_TYPE) -> bool:
    latest_request: float = context.user_data.get(LATEST_REQUEST)
    if latest_request != None and (time.time() - latest_request) < 60*15:
        all = context.bot_data.get(QUEUE, [])
        for request in all:
            if request[0] == context._user_id:
                return True
    return False

# Handle canceling coffee request

async def cancel_request(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # If user doesn't have a pending request, say it

    if not has_pending_request(context):
        await update.message.reply_text("No request for coffee registered from you in the last 15 minutes!")
        return

    # If there are no requests, something went wrong
    # (at least the current user to cancel should still have a valid request)

    all = context.bot_data.get(QUEUE)
    if all is None:
        await update.message.reply_text("Something went wrong..")
        return

    # Delete the request from queue and inform user.

    for i, req in enumerate(all):
        if req[0] == update.effective_user.id:
            del all[i]
            context.bot_data[QUEUE] = all
            context.user_data[LATEST_REQUEST] = None
            await update.message.reply_text("Coffee request cancelled!")
            return
    await update.message.reply_text("Something went wrong..")
    return

# End conversation regarding making coffee, when timeout is reached.

async def make_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.bot_data[MAKING_COFFEE] = False
    await update.message.reply_text("Too slow!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Start a conversation regarding making coffee.

async def start_c(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    # Only one person can make coffee (have this conversation) at a time
    block = context.bot_data.get(MAKING_COFFEE, False)
    if block:
        await update.message.reply_text("Someone is already about to make coffee.")
        return ConversationHandler.END
    context.bot_data[MAKING_COFFEE] = True

    clean_queue(update, context)

    # Possible replies

    reply_keyboard = [["0", "2", "4", "6", "8", "10", "/cancel"]]
    await update.message.reply_text(
        f"Respond with how many cups of coffee you are making (in addition to possible people you counted in ASki), or /cancel\nCurrently {len(context.bot_data.get(QUEUE, []))} people want coffee according to my calculations.",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="0-10"
        ),
    )
    return AMOUNT

# Handle the amount of coffee to be made

async def amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    raw = update.message.text

    # Amount should be convertible to int, else request amount again

    try:
        amount = int(raw)
    except:
        await update.message.reply_text("The coffee amount should be an integer between 0-10! Try again.")
        return AMOUNT
    
    # Bail and don't do anything if amount is zero

    if amount == 0:
        await update.message.reply_text(
        "So you didn't want to make coffee after all? No problem, come back any time!",
        reply_markup=ReplyKeyboardRemove(),
        )
        context.bot_data[MAKING_COFFEE] = False
        return ConversationHandler.END

    # Ask for the amount again, if the amount is something other than 0-10

    if len(raw) > 1 and not (amount <= 10 and amount >= 0) :
        await update.message.reply_text("The coffee amount should be an integer between 0-10! Try again.")
        return AMOUNT
    
    # Remove users from the front of the queue based on the number of cups made.

    all = context.bot_data.get(QUEUE, [])

    for i in range(min(amount//2, len(all))):

        # Inform the users that were in the front of the queue, then delete them

        # Requests have: (User id, chat id, message id, expiry time)

        await context.bot.send_message(chat_id=all[i][1], reply_to_message_id=all[i][2], text="Someone is making coffee!")
        del all[i]

    context.bot_data[QUEUE] = all

    # Inform the user

    await update.message.reply_text(
        f"{amount} cups registered!",
        reply_markup=ReplyKeyboardRemove(),
        )
    context.bot_data[MAKING_COFFEE] = False
    return ConversationHandler.END

# Clean queue from entries that have timed out

def clean_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Safe case that queue is empty

    all = context.bot_data.get(QUEUE, [])

    # Delete timed out requests

    for i, req in enumerate(all):
        if time.time() > req[3]:
            del all[i]
    context.bot_data[QUEUE] = all

# Cancel conversation

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "See ya!", reply_markup=ReplyKeyboardRemove()
    )
    context.bot_data[MAKING_COFFEE] = False
    return ConversationHandler.END
