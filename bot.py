import logging
import os
import firebase_admin
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters, ConversationHandler
)
from firebase_admin import credentials, db

# Load ENV variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "6559745280"))

# Firebase setup
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://earn-kro-ac76f-default-rtdb.firebaseio.com/'
})
db_ref = db.reference("users")
banned_ref = db.reference("banned_users")

# Channel list
CHANNELS = [
    ("JOIN 🕯️", "https://t.me/+T-VXIUFE3X44YTll"),
    ("JOIN 🕯️", "https://t.me/EARNING_SOME"),
    ("JOIN 🕯️", "https://t.me/+CXZizIywslVkMzI1"),
    ("JOIN 🕯️", "https://t.me/ThePterodactylMeme")
]

# Logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
broadcast_mode = set()
BAN_WAITING_ID = 1

# Utility Functions
def is_banned(user_id):
    banned = banned_ref.get() or {}
    return str(user_id) in banned

def ignore_banned(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if is_banned(user_id):
            return
        return await func(update, context)
    return wrapper

def get_user_data(user_id):
    return db_ref.child(str(user_id)).get() or {
        "joined": False,
        "balance": 0,
        "referrals": [],
        "referrer": None
    }

def save_user_data(user_id, data):
    db_ref.child(str(user_id)).set(data)

# Handlers
@ignore_banned
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    data = get_user_data(user_id)

    if not data["referrer"] and args:
        referrer_id = int(args[0])
        if referrer_id != user_id:
            ref_data = get_user_data(referrer_id)
            ref_data["balance"] += 5
            ref_data["referrals"].append(user_id)
            save_user_data(referrer_id, ref_data)
            await context.bot.send_message(
                referrer_id,
                f"🎉 You earned ₹5 from a referral!\n💰 Balance: ₹{ref_data['balance']}"
            )
            data["referrer"] = referrer_id

    save_user_data(user_id, data)
    await send_channel_buttons(update, context)

async def send_channel_buttons(update, context):
    buttons = [[InlineKeyboardButton(name, url=url)] for name, url in CHANNELS]
    buttons.append([InlineKeyboardButton("✅ All Joined", callback_data="check_channels")])
    message = "👋 Join all channels below to get ₹10 signup bonus. Share your link to earn ₹5 per referral."

    if update.message:
        await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(buttons))
    elif update.callback_query:
        await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(buttons))

@ignore_banned
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

    data = get_user_data(user_id)
    if joined_all:
        if not data["joined"]:
            data["joined"] = True
            data["balance"] += 10
            save_user_data(user_id, data)
            await query.message.reply_text("✅ Joined all channels! ₹10 added.")
        await query.message.reply_text(f"🔗 Referral link:\nhttps://t.me/RaferXD_robot?start={user_id}")
    else:
        await query.message.reply_text("⚠️ Join all channels to get bonus.")
        await send_channel_buttons(update, context)

    await query.answer()

@ignore_banned
async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"🔗 Your referral link:\nhttps://t.me/RaferXD_robot?start={user_id}")

@ignore_banned
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user_data(user_id)
    await update.message.reply_text(f"💰 Your current balance: ₹{data['balance']}")

@ignore_banned
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user_data(user_id)
    bal = data.get("balance", 0)
    if bal < 50:
        await update.message.reply_text("❌ Minimum withdrawal is ₹50.")
        return

    await update.message.reply_text("🧾 Send your UPI ID:")

    async def collect_upi(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
        upi = upd.message.text
        await upd.message.reply_text("✅ Request received. Will be processed in 24 hours.")
        await ctx.bot.send_message(
            chat_id=OWNER_ID,
            text=f"💸 Withdrawal Request:\nUser: {upd.effective_user.mention_html()}\nTelegram ID: <code>{user_id}</code>\nAmount: ₹{bal}\nUPI: <code>{upi}</code>",
            parse_mode="HTML"
        )
        ctx.application.remove_handler(handler)

    handler = MessageHandler(filters.TEXT & filters.USER(user_id), collect_upi)
    context.application.add_handler(handler)

@ignore_banned
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("📛 Ban", callback_data="ban_user")]
    ])
    await update.message.reply_text("🔧 Admin Panel", reply_markup=buttons)

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id == OWNER_ID:
        broadcast_mode.add(query.from_user.id)
        await query.message.reply_text("📬 Send the broadcast message:")
        await query.answer()

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in broadcast_mode:
        all_users = db_ref.get() or {}
        for uid in all_users:
            if not is_banned(uid):
                try:
                    await context.bot.send_message(uid, update.message.text)
                except:
                    pass
        await update.message.reply_text("✅ Broadcast sent.")
        broadcast_mode.remove(update.effective_user.id)

async def ban_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != OWNER_ID:
        return
    await query.message.reply_text("🛑 Send the user ID to ban:")
    await query.answer()
    return BAN_WAITING_ID

async def process_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.text.strip()
    banned_ref.update({uid: True})
    await update.message.reply_text(f"✅ User {uid} banned successfully.")
    return ConversationHandler.END

# App Builder
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Command Handlers
app.add_handler(CommandHandler("start", ignore_banned(start)))
app.add_handler(CommandHandler("invite", ignore_banned(invite)))
app.add_handler(CommandHandler("balance", ignore_banned(balance)))
app.add_handler(CommandHandler("withdraw", ignore_banned(withdraw)))
app.add_handler(CommandHandler("admin", admin))

# Callback Query Handlers
app.add_handler(CallbackQueryHandler(ignore_banned(check_channels), pattern="check_channels"))
app.add_handler(CallbackQueryHandler(ignore_banned(broadcast_handler), pattern="broadcast"))

# Message Handlers
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ignore_banned(handle_broadcast)))

# Ban Conversation Handler
ban_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(ban_button_handler, pattern="ban_user")],
    states={BAN_WAITING_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_ban)]},
    fallbacks=[]
)
app.add_handler(ban_conv)

if __name__ == "__main__":
    print("Bot is running...")
    app.run_polling()
