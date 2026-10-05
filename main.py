import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", 8080))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send a link from TikTok, YouTube, Instagram, or X (Twitter) to download.")

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not any(domain in url for domain in ["tiktok.com", "youtube.com", "youtu.be", "instagram.com", "x.com", "twitter.com"]):
        return

    msg = await update.message.reply_text("Processing download...")
    filename = f"download_{update.message.message_id}.mp4"

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': filename,
        'max_filesize': 50 * 1024 * 1024,  # 50MB Telegram limit
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        await update.message.reply_video(video=open(filename, 'rb'))
        await msg.delete()
        if os.path.exists(filename):
            os.remove(filename)
    except Exception as e:
        logger.error(f"Download error: {e}")
        await msg.edit_text("Failed to download video. Ensure link is public and under 50MB.")
        if os.path.exists(filename):
            os.remove(filename)

def main():
    ptb_app = Application.builder().token(TOKEN).build()

    ptb_app.add_handler(CommandHandler("start", start))
    ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_download))

    # Native webhook handling (binds port and manages event loop internally)
    ptb_app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{RENDER_EXTERNAL_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
    
