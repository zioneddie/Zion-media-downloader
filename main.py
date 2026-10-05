import os
import logging
import instaloader
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", 8080))

# Initialize Instaloader
L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=True,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_history=False
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send a link from TikTok, YouTube, Instagram, or X (Twitter) to download.")

def download_instagram(url: str, target_filename: str) -> str:
    """Extract video file using instaloader"""
    # Extract shortcode from link (e.g. instagram.com/reel/SHORTCODE/...)
    parts = url.split('/')
    if 'reel' in parts:
        shortcode = parts[parts.index('reel') + 1]
    elif 'p' in parts:
        shortcode = parts[parts.index('p') + 1]
    else:
        raise ValueError("Invalid Instagram link format.")

    post = instaloader.Post.from_shortcode(L.context, shortcode)
    if not post.is_video:
        raise ValueError("This Instagram post is not a video.")

    import urllib.request
    urllib.request.urlretrieve(post.video_url, target_filename)
    return target_filename

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    valid_domains = ["tiktok.com", "youtube.com", "youtu.be", "instagram.com", "x.com", "twitter.com"]
    
    if not any(domain in url for domain in valid_domains):
        return

    msg = await update.message.reply_text("Processing download...")
    filename = f"download_{update.message.message_id}.mp4"

    try:
        if "instagram.com" in url:
            download_instagram(url, filename)
        else:
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': filename,
                'max_filesize': 50 * 1024 * 1024,
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        await update.message.reply_video(video=open(filename, 'rb'))
        await msg.delete()
    except Exception as e:
        logger.error(f"Download error: {e}")
        await msg.edit_text("Failed to download video. Ensure the link is public and under 50MB.")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

def main():
    ptb_app = Application.builder().token(TOKEN).build()

    ptb_app.add_handler(CommandHandler("start", start))
    ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_download))

    ptb_app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{RENDER_EXTERNAL_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
    
