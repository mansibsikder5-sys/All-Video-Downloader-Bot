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
    return "⚡ Facebook & TikTok Downloader Bot is Running! ⚡"

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
        "আমি আপনার **ফেসবুক ও টিকটক ভিডিও ডাউনলোডার বট**। 🤖✨\n\n"
        "🎯 **আমি যা যা ডাউনলোড করতে পারি:**\n"
        "🔹 TikTok Videos 🎬\n"
        "🔹 Facebook Videos 📱\n\n"
        "🚀 জাস্ট ভিডিওর লিঙ্কটি কপি করে এখানে পেস্ট করে দিন, আমি সরাসরি ভিডিও পাঠিয়ে দেবো! 😎"
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
    url = update.message.text
    
    if not url.startswith("http://") and not url.startswith("https://"):
        await update.message.reply_text("⚠️ ওহ! দয়া করে একটি সঠিক ভিডিও লিঙ্ক (URL) পাঠান। 🧩")
        return

    # ফেসবুক বা টিকটক ছাড়া অন্য লিঙ্ক দিলে বারণ করে দেওয়া
    if not any(domain in url for domain in ["facebook.com", "fb.watch", "tiktok.com", "vm.tiktok.com"]):
        await update.message.reply_text(
            "🛑 দুঃখিত! এই বটটি শুধুমাত্র **Facebook** এবং **TikTok** ভিডিও সাপোর্ট করে।\n\n"
            "💡 দয়া করে একটি সঠিক ফেসবুক বা টিকটক ভিডিওর লিঙ্ক পাঠান।"
        )
        return

    status_message = await update.message.reply_text("🔍 লিঙ্কটি চেক করা হচ্ছে... একটু অপেক্ষা করুন! ⏳")

    # ফেসবুক ও টিকটকের জন্য অপ্টিমাইজড সেটিংস
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
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # এক্সটেনশন ফিক্সিং
        if not os.path.exists(filename):
            base, _ = os.path.splitext(filename)
            for ext in ['mp4', 'mkv', 'webm', '3gp']:
                if os.path.exists(f"{base}.{ext}"):
                    filename = f"{base}.{ext}"
                    break

        filesize = os.path.getsize(filename) / (1024 * 1024)
        if filesize > 50.0:
            await status_message.edit_text(
                f"🛑 দুঃখিত! ভিডিওটির সাইজ ({filesize:.1f} MB) টেলিগ্রাম ফ্রি লিমিটের (50 MB) চেয়ে বড়।\n\n"
                "💡 কম সাইজের বা ছোট কোনো ভিডিওর লিঙ্ক ট্রাই করুন!"
            )
            if os.path.exists(filename): os.remove(filename)
            return

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
            "❌ দুঃখিত! ভিডিওটি ডাউনলোড করা সম্ভব হয়নি।\n\n"
            " **সম্ভাব্য কারণ:**\n"
            "১. লিঙ্কটি ভুল অথবা ভিডিওটি প্রাইভেট/ডিলিট করা হয়েছে। \n"
            "২. ভিডিওর ফাইল সাইজ ৫০ মেগাবাইটের বেশি। 🛑"
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

    print("Bot is starting with Pure Facebook & TikTok Engine...")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
