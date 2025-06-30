import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)

BOT_TOKEN = "7893288883:AAEki6XqSMd7ClGjOkrTcZbU0vFBTBdBOiw"
OWNER_ID = 6559745280
BOT_USERNAME = "RaferXD_robot"

CHANNELS = [
    ("Channel 1", "https://t.me/ThePterodactylMeme"),
    ("Channel 2", "https://t.me/animalin_tm_empire"),
    ("Channel 3", "https://t.me/EARNING_SOME"),
    ("Channel 4", "https://t.me/+T-VXIUFE3X44YTll"),
    ("Channel 5", "https://t.me/+CXZizIywslVkMzI1"),
]

user_data = {}
broadcast_mode = set()
pending_withdraw = {}
ASK_UPI = range(1)

logging.basicConfig(level=logging.INFO)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        user_data[user_id] = {"joined": False, "balance": 0, "referrals": [], "referrer": None}
        args = context.args
        if args:
            referrer_id = int(args[0])
            if referrer_id != user_id and referrer_id in user_data:
                if user_id not in user_data[referrer_id]["referrals"]:
                    user_data[user_id]["referrer"] = referrer_id
                    user_data[referrer_id]["balance"] += 5
                    user_data[referrer_id]["referrals"].append(user_id)
                    await context.bot.send_message(
                        referrer_id,
                        f"🎉 You earned ₹5! New balance: ₹{user_data[referrer_id]['balance']}"
                    )
    await send_channel_buttons(update, context)

# Send join buttons
async def send_channel_buttons(update, context):
    buttons = [[InlineKeyboardButton(name, url=url)] for name, url in CHANNELS]
    buttons.append([InlineKeyboardButton("✅ All Joined", callback_data="check_channels")])
    if update.message:
        await update.message.reply_text("👋 Please join these channels:", reply_markup=InlineKeyboardMarkup(buttons))
    elif update.callback_query:
        await update.callback_query.message.reply_text("👋 Please join these channels:", reply_markup=InlineKeyboardMarkup(buttons))

# Check channels
async def check_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    joined_all = True

    for _, url in CHANNELS:
        if '+' in url:
            continue  # Skip private invite links
        channel_username = url.split("/")[-1]
        try:
            member = await context.bot.get_chat_member(f"@{channel_username}", user_id)
            if member.status == "left":
                joined_all = False
                break
        except:
            joined_all = False
            break

    if joined_all:
        if not user_data[user_id]["joined"]:
            user_data[user_id]["joined"] = True
            user_data[user_id]["balance"] += 10
            await query.message.reply_text("✅ You have joined all channels! ₹10 signup bonus added.")
        if user_data[user_id]["balance"] >= 50:
            await query.message.reply_text("⚠️ You can now withdraw ₹50 or more.")
        await query.message.reply_text(
            f"🔗 Here is your referral link:\n"
            f"https://t.me/{BOT_USERNAME}?start={user_id}\n\n"
            f"Invite friends and get ₹5 per referral!"
        )
    else:
        await query.message.reply_text("⚠️ Please join all channels to get your bonus.")
        await send_channel_buttons(update, context)
    await query.answer()

# /balance
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = user_data.get(user_id, {}).get("balance", 0)
    await update.message.reply_text(f"💰 Your current balance: ₹{balance}")

# /invite
async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"🔗 Your referral link:\n"
        f"https://t.me/{BOT_USERNAME}?start={user_id}\n\n"
        f"Refer friends and get ₹5 each!"
    )

# /admin
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        buttons = [[InlineKeyboardButton("📢 Broadcast", callback_data="broadcast_mode")]]
        await update.message.reply_text("🔐 Admin Panel", reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await update.message.reply_text("❌ You are not authorized.")

# Handle broadcast
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "check_channels":
        await check_channels(update, context)
    elif query.data == "broadcast_mode":
        if query.from_user.id == OWNER_ID:
            broadcast_mode.add(query.from_user.id)
            await query.message.reply_text("✍️ Send the broadcast message now.")
        await query.answer()

# Handle broadcast messages
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in broadcast_mode:
        msg = update.message.text
        broadcast_mode.remove(user_id)
        count = 0
        for uid in user_data:
            try:
                await context.bot.send_message(uid, f"📢 Broadcast:\n\n{msg}")
                count += 1
            except:
                continue
        await update.message.reply_text(f"✅ Broadcast sent to {count} users.")
    else:
        await update.message.reply_text("🤖 I didn’t understand that. Use /start")

# /withdraw
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = user_data.get(user_id, {})
    balance = user.get("balance", 0)

    if balance < 50:
        await update.message.reply_text("❌ Minimum withdrawal is ₹50. Invite more to earn!")
        return ConversationHandler.END

    await update.message.reply_text("💳 Please send your UPI ID to receive payment:")
    pending_withdraw[user_id] = balance
    return ASK_UPI

# Handle UPI input
async def get_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    upi_id = update.message.text
    amount = pending_withdraw.get(user_id, 0)

    if "@" not in upi_id:
        await update.message.reply_text("❌ Invalid UPI ID. Please try again.")
        return ASK_UPI

    await update.message.reply_text("✅ Your withdrawal request has been received. It will be processed within 24 hours.")
    await context.bot.send_message(
        OWNER_ID,
        f"📥 Withdrawal Request\nUser ID: {user_id}\nAmount: ₹{amount}\nUPI ID: {upi_id}"
    )

    user_data[user_id]["balance"] = 0
    pending_withdraw.pop(user_id, None)
    return ConversationHandler.END

# Build the bot
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Add handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("invite", invite))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

# Withdraw handler
withdraw_handler = ConversationHandler(
    entry_points=[CommandHandler("withdraw", withdraw)],
    states={ASK_UPI: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_upi)]},
    fallbacks=[],
)
app.add_handler(withdraw_handler)

# Start the bot
if __name__ == "__main__":
    app.run_polling()
      
