import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8329638234:AAGYyRC8UOqmfifTeo-_3OmuPSsWrur0EAI"

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    await update.message.reply_text("جاري تحميل الفيديو...")

    try:
        ydl_opts = {
            'outtmpl': 'video.%(ext)s',
            'format': 'best'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await update.message.reply_video(video=open(filename, "rb"))

    except Exception as e:
        await update.message.reply_text("ما كدر احمل الفيديو من هذا الرابط")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT, download_video))

print("Bot running...")
app.run_polling()
