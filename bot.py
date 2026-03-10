import os
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = "8329638234:AAEbMHpY6TraitN3bMqsI7hLSR38NUr2jJ8"

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def is_direct_video_url(url: str) -> bool:
    url = url.lower().strip()
    return url.startswith("http://") or url.startswith("https://") and ".mp4" in url


def download_file(url: str, path: str):
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()

    content_type = r.headers.get("content-type", "").lower()
    if "video" not in content_type and not url.lower().endswith(".mp4"):
        raise ValueError("هذا الرابط ليس فيديو مباشر.")

    with open(path, "wb") as f:
        for chunk in r.iter_content(1024 * 256):
            if chunk:
                f.write(chunk)


def main_menu():
    keyboard = [
        [InlineKeyboardButton("طريقة الاستخدام", callback_data="help")],
        [InlineKeyboardButton("فحص الرابط", callback_data="check")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "هلا بيك 🌷\n\n"
        "هذا البوت يستقبل روابط فيديو مباشرة ويرسلها إلك داخل تليگرام.\n\n"
        "أرسل رابط فيديو مباشر بصيغة mp4."
    )
    await update.message.reply_text(text, reply_markup=main_menu())


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        await query.message.reply_text(
            "طريقة الاستخدام:\n\n"
            "1) أرسل رابط يبدأ بـ http أو https\n"
            "2) لازم يكون رابط فيديو مباشر\n"
            "3) الأفضل ينتهي بـ .mp4\n\n"
            "مثال:\n"
            "https://filesamples.com/samples/video/mp4/sample_640x360.mp4"
        )

    elif query.data == "check":
        await query.message.reply_text(
            "دز الرابط هنا، وأنا أفحصه وأگلك إذا مباشر أو لا."
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    if not (text.startswith("http://") or text.startswith("https://")):
        await update.message.reply_text("دز رابط صحيح يبدأ بـ http أو https")
        return

    if ".mp4" not in text.lower():
        await update.message.reply_text(
            "هذا الرابط غالبًا مو فيديو مباشر.\n"
            "أرسل رابط مباشر ينتهي بـ .mp4"
        )
        return

    msg = await update.message.reply_text("جاري التحميل...")

    try:
        file_path = os.path.join(DOWNLOAD_DIR, "video.mp4")
        download_file(text, file_path)

        if os.path.getsize(file_path) == 0:
            raise ValueError("تم تنزيل ملف فارغ.")

        await msg.edit_text("تم التحميل، جاري الإرسال...")

        with open(file_path, "rb") as f:
            await update.message.reply_video(video=f)

        os.remove(file_path)

    except Exception as e:
        await msg.edit_text(f"صار خطأ: {e}")


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("الأمر غير معروف. اكتب /start")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

print("Bot running...")
app.run_polling()