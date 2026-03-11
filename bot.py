import os
import uuid
import yt_dlp

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = "8329638234:AAGYyRC8UOqmfifTeo-_3OmuPSsWrur0EAI"

VIDEO_LIMIT_MB = 49
VIDEO_LIMIT_BYTES = VIDEO_LIMIT_MB * 1024 * 1024


def cleanup_file(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def find_final_file(prepared_name: str) -> str:
    base, _ = os.path.splitext(prepared_name)
    for ext in [".mp4", ".mkv", ".webm", ".mov", ".mp3", ".m4a"]:
        candidate = base + ext
        if os.path.exists(candidate):
            return candidate
    return prepared_name


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تحميل فيديو", callback_data="video")],
        [InlineKeyboardButton("تحميل صوت", callback_data="audio")],
        [InlineKeyboardButton("مساعدة", callback_data="help")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "video"
    await update.message.reply_text(
        "هلا 🌷\n"
        "اختار من الأزرار:\n"
        "• تحميل فيديو\n"
        "• تحميل صوت\n\n"
        "وبعدين دز الرابط.",
        reply_markup=main_menu()
    )


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "video":
        context.user_data["mode"] = "video"
        await query.message.reply_text("تم اختيار تحميل فيديو. هسه دز الرابط.")
    elif query.data == "audio":
        context.user_data["mode"] = "audio"
        await query.message.reply_text("تم اختيار تحميل صوت. هسه دز الرابط.")
    elif query.data == "help":
        await query.message.reply_text(
            "الاستخدام:\n"
            "1) اختار فيديو أو صوت\n"
            "2) دز الرابط\n\n"
            "إذا كان الملف صغير ينرسل كفيديو.\n"
            "إذا كان كبير ينرسل كملف."
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = (update.message.text or "").strip()

    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("دز رابط صحيح.")
        return

    mode = context.user_data.get("mode", "video")

    if mode == "audio":
        await download_audio(update, context, url)
    else:
        await download_video(update, context, url)


async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    status = await update.message.reply_text("جاري تحميل الفيديو...")

    unique = str(uuid.uuid4())
    outtmpl = f"{unique}.%(ext)s"
    filename = ""

    try:
        ydl_opts = {
            "outtmpl": outtmpl,
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "noplaylist": True,
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = find_final_file(ydl.prepare_filename(info))
            title = info.get("title", "video")

        file_size = os.path.getsize(filename)

        with open(filename, "rb") as f:
            if file_size <= VIDEO_LIMIT_BYTES:
                await update.message.reply_video(
                    video=f,
                    caption=title[:1000]
                )
            else:
                await update.message.reply_document(
                    document=f,
                    filename=os.path.basename(filename),
                    caption=f"{title}\nالحجم كبير، انرسل كملف."
                )

        await status.delete()

    except Exception:
        await status.edit_text("ما كدر احمل الفيديو من هذا الرابط.")
    finally:
        cleanup_file(filename)


async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    status = await update.message.reply_text("جاري تحميل الصوت...")

    unique = str(uuid.uuid4())
    outtmpl = f"{unique}.%(ext)s"
    filename = ""

    try:
        ydl_opts = {
            "outtmpl": outtmpl,
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = find_final_file(ydl.prepare_filename(info))
            title = info.get("title", "audio")

        with open(filename, "rb") as f:
            await update.message.reply_audio(
                audio=f,
                title=title[:256]
            )

        await status.delete()

    except Exception:
        await status.edit_text("ما كدر احمل الصوت من هذا الرابط.")
    finally:
        cleanup_file(filename)


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

print("Bot running...")
app.run_polling()
