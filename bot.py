
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
)
import json, os, datetime

TOKEN = os.getenv("TOKEN")
ADMIN_USERNAME = "m6865913"
STANDARD_LINK = "https://x.com/XNowFeed?t=ModG4mhtUibl5xh9H8dZNw&s=09"
DATA_FILE = "f4f_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "users": ["standard"],
            "links": {"standard": STANDARD_LINK},
            "approved": [],
            "pending": {},
            "admin_id": None,
            "week": datetime.date.today().isocalendar()[1]
        }
        save_data(data)

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    # Ensure all required keys exist
    if "pending" not in data:
        data["pending"] = {}
    if "approved" not in data:
        data["approved"] = []
    if "links" not in data:
        data["links"] = {"standard": STANDARD_LINK}
    if "users" not in data:
        data["users"] = ["standard"]
    if "admin_id" not in data:
        data["admin_id"] = None
    if "week" not in data:
        data["week"] = datetime.date.today().isocalendar()[1]

    save_data(data)
    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    username = user.username or f"ID:{user_id}"
    data = load_data()

    if username == ADMIN_USERNAME and not data.get("admin_id"):
        data["admin_id"] = int(user_id)
        save_data(data)
        await update.message.reply_text("✅ You are now set as admin.")

    data["pending"][user_id] = username
    save_data(data)

    chain_msg = "👥 Follow everyone below:

"
    for uid in data["users"]:
        chain_msg += f"🔗 {data['links'][uid]}
"

    chain_msg += "\n👇 Click to request approval"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 Request Approval", callback_data=f"req:{user_id}")]
    ])
    await update.message.reply_text(chain_msg, reply_markup=keyboard)

async def request_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = str(user.id)
    username = user.username or f"ID:{user_id}"
    data = load_data()

    admin_id = data.get("admin_id")
    if not admin_id:
        await query.edit_message_text("⚠️ Admin not set up.")
        return

    data["pending"][user_id] = username
    save_data(data)

    admin_msg = f"👤 @{username} (ID: {user_id}) wants to join."
    admin_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve:{user_id}"),
         InlineKeyboardButton("❌ Deny", callback_data=f"deny:{user_id}")]
    ])

    await context.bot.send_message(chat_id=admin_id, text=admin_msg, reply_markup=admin_keyboard)
    await query.edit_message_text("✅ Request sent! Wait for admin to approve.")

async def approve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    cmd, user_id = query.data.split(":")
    sender_id = str(query.from_user.id)

    if sender_id != str(data.get("admin_id")):
        await query.edit_message_text("⛔ You’re not authorized.")
        return

    if cmd == "approve":
        if user_id not in data["approved"]:
            data["approved"].append(user_id)
            save_data(data)
            await context.bot.send_message(chat_id=int(user_id),
                text="✅ Approved! Send your link using:\n/drop https://x.com/yourhandle")
        await query.edit_message_text(f"✅ Approved user {user_id}")
    elif cmd == "deny":
        await query.edit_message_text(f"❌ Denied user {user_id}")
        if user_id in data["pending"]:
            del data["pending"][user_id]
            save_data(data)

async def drop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data["approved"]:
        await update.message.reply_text("⚠️ You are not approved yet.")
        return

    if len(context.args) != 1 or not context.args[0].startswith("http"):
        await update.message.reply_text("⚠️ Usage:\n/drop https://x.com/yourhandle")
        return

    link = context.args[0]
    if user_id not in data["users"]:
        data["users"].append(user_id)
    data["links"][user_id] = link
    save_data(data)

    await update.message.reply_text("✅ Link added to the follow chain.")

async def list_chain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    msg = "📃 Current Follow Chain:\n\n"
    for uid in data["users"]:
        msg += f"{data['links'].get(uid)}\n"
    await update.message.reply_text(msg or "⚠️ No links yet.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("drop", drop))
app.add_handler(CommandHandler("list", list_chain))
app.add_handler(CallbackQueryHandler(request_approval_callback, pattern="^req:"))
app.add_handler(CallbackQueryHandler(approve_callback, pattern="^(approve|deny):"))

print("🤖 Bot is running...")
app.run_polling()
