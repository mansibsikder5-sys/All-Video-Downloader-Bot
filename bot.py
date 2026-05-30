import os
import threading
import asyncio
import yt_dlp
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ---- Fake Server for Render Free Tier ----
app = Flask(__name__)

@app.route('/')
def home():
    return "⚡ FB, TikTok Downloader & Song Finder Bot is Running! ⚡"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---- Telegram Bot Logic ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "No Username"
    full_name = user.full_name

    await update.message.reply_text(
        "👋 আসসালামু আলাইকুম!\n"
        "আমি আপনার **ভিডিও ডাউনলোডার এবং গান খোঁজার বট**। 🤖🎶\n\n"
        "🎯 **আমি যা যা করতে পারি:**\n"
        "🔹 TikTok Videos 🎬 (লিঙ্ক দিলে)\n"
        "🔹 Facebook Videos 📱 (লিঙ্ক দিলে)\n"
        "🎵 **Song Finder:** যেকোনো গানের নাম টাইপ করে পাঠালেই আমি সেটি অডিও (MP3) আকারে এনে দেবো! 😎\n\n"
        "🚀 জাস্ট লিঙ্ক অথবা গানের নাম লিখে পাঠিয়ে দিন!"
    )

    BACKUP_CHAT_ID = os.environ.get("TELEGRAM_BACKUP_CHAT_ID")
    if BACKUP_CHAT_ID:
        try:
            log_message = (
                "🎉 **নতুন ইউজার জয়েন করেছে!** 🎉\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 **নাম:** {full_name}\n"
                f"🆔 **আইডি:** `{user_id}`\n"
                f"🔗 **ইউজারনেম:** {username}\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "🤖 _বটটি সফলভাবে কাজ করছে..._"
            )
            await context.bot.send_message(chat_id=BACKUP_CHAT_ID, text=log_message, parse_mode="Markdown")
        except Exception as e:
            print(f"Backup Channel Error: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    # 📥 মেথড ১: ইউজার যদি ভিডিও লিঙ্ক পাঠায় (Facebook / TikTok)
    if text.startswith("http://") or text.startswith("https://"):
        if "instagram.com" in text or "youtu" in text:
            await update.message.reply_text(
                "🛑 দুঃখিত! এই বটের নতুন আপডেটে **YouTube** এবং **Instagram** ভিডিও ডাউনলোড বন্ধ করা হয়েছে।\n\n"
                "💡 তবে আপনি যেকোনো গানের নাম লিখে পাঠালে সেটি অডিও (MP3) হিসেবে পাবেন! অথবা Facebook/TikTok ভিডিওর লিঙ্ক দিতে পারেন।"
            )
            return

        status_message = await update.message.reply_text("🔍 লিঙ্কটি চেক করা হচ্ছে... একটু অপেক্ষা করুন! ⏳")
        ydl_opts = {
            'format': 'bestvideo[filesize<=45M]+bestaudio/best[filesize<=45M]/best',
            'outtmpl': 'downloaded_video.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            }
        }
        
        try:
            await status_message.edit_text("⚡ আমাদের সার্ভারে ভিডিও ডাউনলোড শুরু হয়েছে... 📥")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                filename = ydl.prepare_filename(info)

            if not os.path.exists(filename):
                base, _ = os.path.splitext(filename)
                for ext in ['mp4', 'mkv', 'webm', '3gp']:
                    if os.path.exists(f"{base}.{ext}"):
                        filename = f"{base}.{ext}"
                        break

            await status_message.edit_text("🚀 ডাউনলোড সফল! এবার ভিডিওটি পাঠানো হচ্ছে... 📤")
            with open(filename, 'rb') as video_file:
                await update.message.reply_video(video=video_file, caption="🎉 আপনার ভিডিওটি রেডি! 🔥\n\n👑 Developer By MANSIB")
            if os.path.exists(filename): os.remove(filename)
            await status_message.delete()
        except Exception as e:
            print(f"Video Error: {str(e)}")
            await status_message.edit_text("❌ দুঃখিত! ভিডিওটি প্রসেস করা সম্ভব হয়নি। লিঙ্কটি সঠিক কিনা চেক করুন।")
            if 'filename' in locals() and os.path.exists(filename): os.remove(filename)

    # 🎵 মেথড ২: ইউজার যদি গানের নাম লেখে (Song Finder)
    else:
        status_message = await update.message.reply_text(f"🔍 '{text}' গানটি খোঁজা হচ্ছে... একটু অপেক্ষা করুন! 🎵")
        
        audio_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'default_search': 'ytsearch1', # ইউটিউব সার্চের ১ম রেজাল্ট নেবে
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'http_headers': {
                # ব্লকিং এড়াতে লাইটওয়েট মোবাইল ব্রাউজার হেডার
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
            }
        }

        try:
            await status_message.edit_text("📥 গানটি পাওয়া গেছে! অডিও ফাইলে কনভার্ট করা হচ্ছে... 🎛️")
            
            with yt_dlp.YoutubeDL(audio_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                video_data = info['entries'][0] if 'entries' in info else info
                title = video_data.get('title', 'audio')
                filename = f"{title}.mp3"

            # স্পেশাল ক্যারেক্টারের কারণে এক্সটেনশন ফাইল চেক
            if not os.path.exists(filename):
                for f in os.listdir('.'):
                    if f.endswith('.mp3'):
                        filename = f
                        break

            await status_message.edit_text("🚀 কনভার্ট কমপ্লিট! গানটি আপনার চ্যাটে পাঠানো হচ্ছে... 📤")
            
            with open(filename, 'rb') as audio_file:
                await update.message.reply_audio(
                    audio=audio_file, 
                    title=title,
                    caption=f"🎵 গান: {title}\n\n👑 Developer By MANSIB"
                )
            
            if os.path.exists(filename): os.remove(filename)
            await status_message.delete()

        except Exception as e:
            print(f"Audio Error: {str(e)}")
            await status_message.edit_text("❌ দুঃখিত! এই নামে কোনো গান খুঁজে পাওয়া যায়নি বা ডাউনলোডে সমস্যা হয়েছে।")
            if 'filename' in locals() and os.path.exists(filename): os.remove(filename)

def main():
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing!")
        return

    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    print("Bot is starting with Hybrid FB/TikTok & Audio Engine...")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
