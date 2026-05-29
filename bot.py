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
    return "⚡ Downloader Bot with Channel Backup is Running Perfectly! ⚡"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---- Telegram Bot Logic ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "No Username"
    full_name = user.full_name

    # 📥 মূল ইউজারের চ্যাটে ওয়েলকাম মেসেজ (ইমোজি দিয়ে সাজানো)
    await update.message.reply_text(
        "👋 আসসালামু আলাইকুম!\n"
        "আমি আপনার **অল-ইন-ওয়ান ভিডিও ডাউনলোডার বট**। 🤖✨\n\n"
        "আমাকে যেকোনো ভিডিওর লিঙ্ক পাঠান, আমি সেটি সরাসরি ডাউনলোড করে দেবো! 😎\n\n"
        "🎯 **আমি যা যা ডাউনলোড করতে পারি:**\n"
        "🔹 TikTok Videos 🎬\n"
        "🔹 YouTube Shorts & Videos 📺\n"
        "🔹 Facebook Videos 📱\n"
        "🔹 Instagram Reels 📸\n\n"
        "🚀 জাস্ট লিঙ্কটি কপি করে এখানে পেস্ট করে দিন!"
    )

    # 📢 আপনার পার্সোনাল ব্যাকআপ চ্যানেলে সুন্দর নোটিফিকেশন পাঠানো
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
    url = update.message.text
    
    # লিঙ্কটি সঠিক কিনা চেক করা
    if not url.startswith("http://") and not url.startswith("https://"):
        await update.message.reply_text("⚠️ ওহ! দয়া করে একটি সঠিক ভিডিও লিঙ্ক (URL) পাঠান। 🧩")
        return

    # প্রথম স্ট্যাটাস মেসেজ
    status_message = await update.message.reply_text("🔍 লিঙ্কটি চেক করা হচ্ছে... একটু অপেক্ষা করুন! ⏳")

    # yt-dlp এর চমৎকার কনফিগারেশন
    ydl_opts = {
        'format': 'bestvideo[filesize<=45M]+bestaudio/best/best', # বেস্ট কোয়ালিটি কিন্তু ৫০ এমবি-র নিচে
        'outtmpl': 'downloaded_video.%(ext)s', 
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Mode': 'navigate',
        },
        'extractor_args': {
            'instagram': {
                'max_comments': 0,
            }
        }
    }

    try:
        # স্ট্যাটাস আপডেট: ডাউনলোড শুরু
        await status_message.edit_text("⚡ আমাদের সার্ভারে ভিডিও ডাউনলোড শুরু হয়েছে... 📥")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # যদি কোনো কারণে অন্য ফরম্যাটে ডাউনলোড হয়ে ফাইলনেম আলাদা হয় তা চেক করা
        if not os.path.exists(filename):
            base, _ = os.path.splitext(filename)
            for ext in ['mp4', 'mkv', 'webm', '3gp']:
                if os.path.exists(f"{base}.{ext}"):
                    filename = f"{base}.{ext}"
                    break

        # ফাইলের ফাইনাল সাইজ চেক (টেলিগ্রামের ৫০ এমবি বাউন্ডারি নিরাপদ রাখতে)
        filesize = os.path.getsize(filename) / (1024 * 1024)
        if filesize > 50.0:
            await status_message.edit_text(
                f"🛑 দুঃখিত! ভিডিওটির সাইজ ({filesize:.1f} MB) টেলিগ্রামের ফ্রি বটের লিমিটের (50 MB) চেয়ে বেশি বড়।\n\n"
                "💡 এটি ছোট কোনো রিলস, শর্টস বা কম সময়ের ভিডিওর ক্ষেত্রে দারুণ কাজ করবে!"
            )
            if os.path.exists(filename):
                os.remove(filename)
            return

        # স্ট্যাটাস আপডেট: টেলিগ্রামে পাঠানো হচ্ছে
        await status_message.edit_text("🚀 ডাউনলোড সফল! এবার ভিডিওটি আপনার চ্যাটে পাঠানো হচ্ছে... 📤")

        with open(filename, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file, 
                caption="🎉 আপনার কাঙ্ক্ষিত ভিডিওটি রেডি! উপভোগ করুন। 🔥\n\n👑 Developer By MANSIB"
            )

        if os.path.exists(filename):
            os.remove(filename)
            
        await status_message.delete()

    except Exception as e:
        print(f"Error: {str(e)}")
        await status_message.edit_text(
            "❌ দুঃখিত! ভিডিওটি প্রসেস করা সম্ভব হয়নি।\n\n"
            "💡 **সম্ভাব্য কারণ:**\n"
            "১. লিঙ্কটি ভুল বা প্রাইভেট প্রোফাইলের হতে পারে। 🧩\n"
            "২. ইন্সটাগ্রামের কড়া সিকিউরিটির কারণে সার্ভার সাময়িক ব্লক করেছে। 🛑"
        )
        try:
            if 'filename' in locals() and os.path.exists(filename):
                os.remove(filename)
        except:
            pass

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

    print("Bot is starting with Developer By MANSIB brand...")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
