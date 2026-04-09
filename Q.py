from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from pyzbar.pyzbar import decode
from PIL import Image
import json, os
from datetime import date

BOT_TOKEN = "8791378973:AAHbxXJKE_DgwxjWlWP9JEzLlP5vsjF15Tk"
ADMIN_ID = 8210146346
ADMIN_PASSWORD = "sani"
CHANNEL = "@saniedit9"

DATA_FILE = "data.json"
LIMIT = 3

admin_mode = {}

# ---------- DATABASE ----------
def load():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except:
        return {}

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def fix_user(data, user):
    today = str(date.today())
    if user not in data:
        data[user] = {"count":0,"date":today,"premium":False,"ban":False}
    else:
        data[user].setdefault("count",0)
        data[user].setdefault("date",today)
        data[user].setdefault("premium",False)
        data[user].setdefault("ban",False)

# ---------- JOIN CHECK ----------
async def check_join(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member","administrator","creator"]
    except:
        return False

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.effective_user.id)
    data = load()
    fix_user(data, user)

    # referral
    ref = context.args[0] if context.args else None
    if ref and ref != user:
        fix_user(data, ref)
        data[ref]["count"] = max(0, data[ref].get("count", 0) - 2)

    save(data)

    # force join
    if not await check_join(int(user), context.bot):
        btn = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL.replace('@','')}")],
            [InlineKeyboardButton("✅ Verify", callback_data="verify")]
        ]
        return await update.message.reply_text("🚫 আগে channel join করো", reply_markup=InlineKeyboardMarkup(btn))

    btn = [
        [InlineKeyboardButton("📷 Scan QR", callback_data="scan")],
        [InlineKeyboardButton("👑 Admin", callback_data="admin")]
    ]

    await update.message.reply_text(
        f"🤖 Welcome\n\n🎯 Invite:\nhttps://t.me/{context.bot.username}?start={user}",
        reply_markup=InlineKeyboardMarkup(btn)
    )

# ---------- VERIFY ----------
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user.id

    if not await check_join(user, context.bot):
        return await query.message.reply_text("❌ এখনও join করো নাই")

    btn = [
        [InlineKeyboardButton("📷 Scan QR", callback_data="scan")],
        [InlineKeyboardButton("👑 Admin", callback_data="admin")]
    ]

    await query.message.reply_text("✅ Verified!", reply_markup=InlineKeyboardMarkup(btn))

# ---------- ADMIN LOGIN ----------
async def admin_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return await query.message.reply_text("❌ Not admin")

    admin_mode[query.from_user.id] = "pass"
    await query.message.reply_text("🔐 Enter password:")

# ---------- HANDLE TEXT ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    text = update.message.text.strip()
    data = load()

    if user in admin_mode:
        state = admin_mode[user]

        if state == "pass":
            if text == ADMIN_PASSWORD:
                admin_mode[user] = "panel"

                btn = [
                    [InlineKeyboardButton("🚫 Ban", callback_data="ban")],
                    [InlineKeyboardButton("✅ Unban", callback_data="unban")],
                    [InlineKeyboardButton("🎯 Set Limit", callback_data="limit")],
                    [InlineKeyboardButton("📊 Stats", callback_data="stats")],
                    [InlineKeyboardButton("📢 Post", callback_data="post")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back")]
                ]

                return await update.message.reply_text("👑 Admin Panel", reply_markup=InlineKeyboardMarkup(btn))
            else:
                return await update.message.reply_text("❌ Wrong password")

        elif state == "ban":
            fix_user(data, text)
            data[text]["ban"] = True
            save(data)
            admin_mode[user] = "panel"
            return await update.message.reply_text("✅ Banned")

        elif state == "unban":
            fix_user(data, text)
            data[text]["ban"] = False
            save(data)
            admin_mode[user] = "panel"
            return await update.message.reply_text("✅ Unbanned")

        elif state.startswith("limit"):
            parts = state.split("|")

            if parts[1] == "id":
                admin_mode[user] = f"limit|{text}|val"
                return await update.message.reply_text("Enter limit number:")
            else:
                uid = parts[1]
                try:
                    val = int(text)
                except:
                    return await update.message.reply_text("❌ Invalid number")

                fix_user(data, uid)
                data[uid]["count"] = val
                save(data)
                admin_mode[user] = "panel"
                return await update.message.reply_text("✅ Limit set")

        elif state == "post":
            sent = 0
            for uid in data:
                try:
                    await context.bot.send_message(chat_id=int(uid), text=text)
                    sent += 1
                except:
                    pass

            admin_mode[user] = "panel"
            return await update.message.reply_text(f"✅ Sent to {sent} users")

# ---------- BUTTON ----------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user.id
    data = load()

    if query.data == "scan":
        await query.message.reply_text("📷 Send QR image")

    elif query.data == "admin":
        await admin_btn(update, context)

    elif query.data == "ban":
        admin_mode[user] = "ban"
        await query.message.reply_text("Enter user ID:")

    elif query.data == "unban":
        admin_mode[user] = "unban"
        await query.message.reply_text("Enter user ID:")

    elif query.data == "limit":
        admin_mode[user] = "limit|id"
        await query.message.reply_text("Enter user ID:")

    elif query.data == "stats":
        await query.message.reply_text(f"👥 Users: {len(data)}")

    elif query.data == "post":
        admin_mode[user] = "post"
        await query.message.reply_text("✍️ Send message:")

    elif query.data == "back":
        admin_mode[user] = None
        await query.message.reply_text("🔙 Exit admin")

# ---------- SCAN ----------
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.effective_user.id)
    data = load()
    fix_user(data, user)

    if data[user]["ban"]:
        return await update.message.reply_text("🚫 You are banned")

    # limit
    today = str(date.today())
    if data[user]["date"] != today:
        data[user]["date"] = today
        data[user]["count"] = 0

    if not data[user]["premium"]:
        if data[user]["count"] >= LIMIT:
            return await update.message.reply_text("❌ Daily limit finished")

    photo = update.message.photo[-1]
    file = await photo.get_file()
    await file.download_to_drive("qr.png")

    img = Image.open("qr.png")
    result = decode(img)

    data[user]["count"] += 1
    save(data)

    if result:
        await update.message.reply_text(result[0].data.decode("utf-8"))
    else:
        await update.message.reply_text("❌ No QR found")

# ---------- MAIN ----------
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.PHOTO, scan))

print("🔥 BOT RUNNING...")
app.run_polling()
