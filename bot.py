import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = "YOUR_BOT_TOKEN"
OWNER_ID = 123456789
CHANNELS = [
    ("Channel 1", "https://t.me/ThePterodactylMeme"),
    ("Channel 2", "https://t.me/animalin_tm_empire"),
    ("Channel 3", "https://t.me/lazy_guys_here"),
    ("Channel 4", "https://t.me/your_channel4")
    ("Channel 5", "https://t.me/ThePterodactylMeme"),
]
user_data = {}
broadcast_mode = set()

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        user_data[user_id] = {"joined": False, "balance": 0, "referrals": [], "referrer": None}
        args = context.args
        if args:
            referrer_id = int(args[0])
            if referrer_id != user_id and referrer_id in user_data:
                user_data[user_id]["referrer"] = referrer_id
                user_data.setdefault(referrer_id, {"joined": False, "balance": 0, "referrals": [], "referrer": None})
                user_data[referrer_id]["balance"] += 5
                user_data[referrer_id]["referrals"].append(user_id)
                await context.bot.send_message(referrer_id, f"🎉 You earned ₹5! New balance: ₹{user_data[referrer_id]['balance']}")
    await send_channel_buttons(update, context)

async def send_channel_buttons(update, context):
    buttons = [
        [InlineKeyboardButton(name, url=url)] for name, url in CHANNELS
    ]
    buttons.append([InlineKeyboardButton("✅ All Joined", callback_data="check_channels")])
    if update.message:
        await update.message.reply_text("👋 Please join these channels:", reply_markup=InlineKeyboardMarkup(buttons))
    elif update.callback_query:
        await update.callback_query.message.reply_text("👋 Please join these channels:", reply_markup=InlineKeyboardMarkup(buttons))

async def check_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    joined_all = True
    for _, url in CHANNELS:
        channel_username = url.split("/")[-1]
        try:
            member = await context.bot.get_chat_member(f"@{channel_username}", user_id)
            if member.status in ["left"]:
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
        await query.message.reply_text(f"🔗 Here is your referral link:\nhttps://t.me/YOUR_BOT_USERNAME?start={user_id}\n\nInvite friends and get ₹5 per referral!")
    else:
        await query.message.reply_text("⚠️ Please join all channels to get your bonus.")
        await send_channel_buttons(update, context)
    await query.answer()

# Other handlers remain same as before

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(check_channels, pattern="check_channels"))

# (Add other handlers as previously)

if __name__ == "__main__":
    app.run_polling() Your bot.py code here (use previously updated code)
