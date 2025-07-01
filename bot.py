import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "6559745280"))

CHANNELS = [
    ("Channel 1", "https://t.me/ThePterodactylMeme"),
    ("Channel 2", "https://t.me/animalin_tm_empire"),
    ("Channel 3", "https://t.me/EARNING_SOME"),
    ("Channel 4", "https://t.me/+T-VXIUFE3X44YTll"),
    ("Channel 5", "https://t.me/+CXZizIywslVkMzI1")
]

user_data = {}
broadcast_mode = set()

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    # Initialize new user
    if user_id not in user_data:
        user_data[user_id] = {
            "joined": False,
            "balance": 0,
            "referrals": [],
            "referrer": None
        }

        # Handle referral
        if args:
            try:
                referrer_id = int(args[0])
                if referrer_id != user_id:
                    if referrer_id not in user_data:
                        user_data[referrer_id] = {
                            "joined": False,
                            "balance": 0,
                            "referrals": [],
                            "referrer": None
                        }
                    user_data[user_id]["referrer"] = referrer_id
                    user_data[referrer_id]["balance"] += 5
                    user_data[referrer_id]["referrals"].append(user_id)
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 You earned ₹5 from a referral!\n💰 New balance: ₹{user_data[referrer_id]['balance']}"
                    )
            except Exception as e:
                logging.error(f"Referral error: {e}")

    await send_channel_buttons(update, context)

async def send_channel_buttons(update, context):
    buttons = [[InlineKeyboardButton(name, url=url)] for name, url in CHANNELS]
    buttons.append([InlineKeyboardButton("✅ All Joined", callback_data="check_channels")])

    message = (
        "👋 Welcome! Join all the channels below to instantly get ₹10 signup bonus.\n\n"
        "Then share your referral link and earn ₹5 for every friend who joins!"
    )

    if update.message:
        await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(buttons))
    elif update.callback_query:
        await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(buttons))

async def check_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    joined_all = True
    for _, url in CHANNELS:
        if '+' in url:
            continue
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
        await query.message.reply_text(
            f"🔗 Here is your referral link:\nhttps://t.me/RaferXD_robot?start={user_id}\n\n"
            "Invite friends and get ₹5 per referral!"
        )
    else:
        await query.message.reply_text("⚠️ Please join all channels to get your bonus.")
        await send_channel_buttons(update, context)
    await query.answer()

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"🔗 Your referral link:\nhttps://t.me/RaferXD_robot?start={user_id}")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = user_data.get(user_id, {}).get("balance", 0)
    await update.message.reply_text(f"💰 Your current balance: ₹{bal}")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = user_data.get(user_id, {}).get("balance", 0)
    if bal < 50:
        await update.message.reply_text("❌ Minimum withdrawal amount is ₹50.")
        return

    await update.message.reply_text("🧾 Please send your UPI ID to process the withdrawal.")

    async def collect_upi(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
        upi = upd.message.text
        await upd.message.reply_text("✅ Withdrawal request received. It will be processed within 24 hours.")
        await ctx.bot.send_message(
            chat_id=OWNER_ID,
            text=f"💸 Withdrawal Request:\nUser: {upd.effective_user.mention_html()}\n"
                 f"Amount: ₹{bal}\nUPI: {upi}",
            parse_mode="HTML"
        )
        ctx.application.remove_handler(handler)

    handler = MessageHandler(filters.TEXT & filters.USER(user_id), collect_upi)
    context.application.add_handler(handler)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return
    button = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")]])
    await update.message.reply_text("🔧 Admin Panel", reply_markup=button)

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id == OWNER_ID:
        broadcast_mode.add(user_id)
        await query.message.reply_text("📬 Send the message to broadcast:")
    await query.answer()

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in broadcast_mode:
        for uid in user_data:
            try:
                await context.bot.send_message(uid, update.message.text)
            except:
                pass
        await update.message.reply_text("✅ Broadcast sent to all users.")
        broadcast_mode.remove(user_id)

# Create app
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("invite", invite))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("withdraw", withdraw))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast))
app.add_handler(CallbackQueryHandler(check_channels, pattern="check_channels"))
app.add_handler(CallbackQueryHandler(broadcast_handler, pattern="broadcast"))

if __name__ == "__main__":
    print("Bot is running...")
    app.run_polling()
